import os
#import ssl
import yaml
import json
import datetime
import requests
import logging
import xml.etree.ElementTree as ET
from time import sleep
from typing import Tuple
#from requests.packages.urllib3.util.ssl_ import create_urllib3_context
#from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, before_sleep_log, wait_exponential

# Local imports
from xcelEndpoint import xcelEndpoint
from xcelDataType import *
from CCM8Adapter import CCM8Adapter

IEEE_PREFIX = '{urn:ieee:std:2030.5:ns}'

logger = logging.getLogger(__name__)

class generateEndpointYaml():

    def __init__(self, name: str, ip_address: str, port: int, creds: Tuple[str, str]):
        self.name = name
        self.POLLING_RATE = 5.0
        # Base URL used to query the meter
        self.url = f'https://{ip_address}:{port}'

        # Create a new requests session based on the passed in ip address and port #
        self.requests_session = self.setup_session(creds, ip_address)

        # Set to uninitialized
        self.initalized = False

    @retry(stop=stop_after_attempt(15),
           wait=wait_exponential(multiplier=1, min=1, max=15),
           before_sleep=before_sleep_log(logger, logging.WARNING),
           reraise=True)
    def setup(self) -> None:
        # XML Entries we're looking for within the endpoint
        device_capability_info_names = ['TimeLink', 'UsagePointListLink', 'SelfDeviceLink']
        # Endpoint of the meter used for HW info
        device_capability_info_url = '/dcap'
        # Query the meter to get some more details about it
        details_dict = self.get_device_capability_details(device_capability_info_url, device_capability_info_names)
        self._deviceTime = details_dict['TimeLink']
        self._meterUsagePoint = details_dict['UsagePointListLink']
        self._selfDevice = details_dict['SelfDeviceLink']

        # Device info used for home assistant MQTT discovery
        self.device_capability_info = {
                                "timeLink": self._deviceTime,
                                "usagePointListLink": self._meterUsagePoint,
                                "selfDeviceLink": self._selfDevice
                            }

        # ready to go
        self.initalized = True

    def get_device_capability_details(self, dc_info_url: str, dc_names: list) -> dict:
        """
        Queries the Meter Device Capability endpoint at the ip address passed
        to the class.

        Returns: dict, {<element name>: <meter response>}
        """
        query_url = f'{self.url}{dc_info_url}'
        # query the hw specs endpoint
        x = self.requests_session.get(query_url, verify=False, timeout=4.0)
        # Parse the response xml looking for the passed in element names
        root = ET.fromstring(x.text)
        dc_info_dict = {}
        for name in dc_names:
            if root.find(f'.//{IEEE_PREFIX}{name}') is not None:
                dc_info_dict[name] = root.find(f'.//{IEEE_PREFIX}{name}').get('href')
        
        return dc_info_dict

    def get_meter_usage_point_details(self, upt_info_url: str, upt_names: list) -> dict:
        """
        Queries the Meter Usage Point capability endpoint at the ip address passed
        to the class.

        Returns: dict, {<element name>: <meter response>}
        """
        query_url = f'{self.url}{upt_info_url}'
        # query the usage point specs endpoint
        x = self.requests_session.get(query_url, verify=False, timeout=4.0)
        # Parse the response xml looking for the passed in element names
        root = ET.fromstring(x.text)
        upt_info_dict = {}
        for name in upt_names:
            if root.find(f'.//{IEEE_PREFIX}{name}') is not None:
                upt_info_dict[name] = root.find(f'.//{IEEE_PREFIX}{name}').attrib
        
        return upt_info_dict
        
    def get_meter_endpoint_details(self, mr_info_url: str, mr_number: int) -> list:
        """
        Queries the Meter Reading endpoint details at the ip address passed
        to the class.

        Returns: dict, {<element name>: <meter response>}
        """
        # XML Entries we're looking for within the endpoint
        meter_reading_info_names = ['description','ReadingLink','ReadingTypeLink']
        
        query_url = f'{self.url}{mr_info_url}?l={mr_number}'

        # query the MeterReading endpoint
        x = self.requests_session.get(query_url, verify=False, timeout=4.0)
        # Parse the response xml looking for the passed in element names
        root = ET.fromstring(x.text)
        #print(root.iterfind(f'.//{IEEE_PREFIX}MeterReading'))
        meter_endpoint_info_dict = {}
        meter_reading_list = []

        #for meterReading in root.iter(f'.//{IEEE_PREFIX}MeterReading'):
        for meterReading in root.findall(f'.//{IEEE_PREFIX}MeterReading'):
            meter_endpoint_info_dict = { "MeterReading" : { } }

            for child in meterReading.iter():
                #print('childMeterReading',child.tag,child.text, child.attrib)
                #print(child.tag)
                match child.tag.removeprefix(IEEE_PREFIX):
                    case 'description' :
                        meter_endpoint_info_dict['MeterReading']['Description'] = child.text
                    case 'ReadingLink':
                        meter_endpoint_info_dict['MeterReading']['ReadingLink'] = child.get('href')
                    case 'ReadingSetListLink':
                        meter_endpoint_info_dict['MeterReading']['ReadingSetListLink'] = child.get('href')
                    case 'ReadingTypeLink':
                        meter_endpoint_info_dict['MeterReading']['ReadingTypeLink'] = child.get('href')

            meter_endpoint_info_dict['MeterReading']['Description'] = meter_endpoint_info_dict['MeterReading']['Description'].replace('TOU','Time-Of-Use')

            meter_endpoint_info_dict.update(self.get_meter_endpoint_type_details(meter_endpoint_info_dict['MeterReading']['ReadingTypeLink']))
            
            if self.is_endpoint_reading_type_supported(meter_endpoint_info_dict):
                meter_endpoint_info_dict.update(self.get_meter_endpoint_reading(meter_endpoint_info_dict['MeterReading']['ReadingLink']))
            
                meter_reading_list.append(
                    meter_endpoint_info_dict
                )                
        
        # Meter responds decending instead of acending
        # Lets fix that with reverse
        meter_reading_list.reverse()

        return meter_reading_list
    
    def get_meter_endpoint_type_details(self, reading_type_info_url: str) -> dict:
        """
        Queries the endpoint Reading Type details endpoint at the ip address passed
        to the class.

        Returns: dict, {<element name>: <meter response>}
        """
        query_url = f'{self.url}{reading_type_info_url}'

        # query the MeterReading endpoint
        x = self.requests_session.get(query_url, verify=False, timeout=4.0)
        # Parse the response xml looking for the passed in element names
        root = ET.fromstring(x.text)
        
        meter_endpoint_reading_type_dict = { "ReadingType" : { } }
        for meterReadingType in root.findall(f'.//{IEEE_PREFIX}*'):
            match meterReadingType.tag.removeprefix(IEEE_PREFIX):
                case 'accumulationBehaviour':
                    meter_endpoint_reading_type_dict['ReadingType']['accumulationBehaviour'] = int(meterReadingType.text)
                case 'commodity':
                    meter_endpoint_reading_type_dict['ReadingType']['commodity'] = int(meterReadingType.text)
                case 'dataQualifier':
                    meter_endpoint_reading_type_dict['ReadingType']['dataQualifier'] = int(meterReadingType.text)
                case 'flowDirection':
                    meter_endpoint_reading_type_dict['ReadingType']['flowDirection'] = int(meterReadingType.text)
                case 'kind':
                    meter_endpoint_reading_type_dict['ReadingType']['kind'] = int(meterReadingType.text)
                case 'powerOfTenMultiplier':
                    meter_endpoint_reading_type_dict['ReadingType']['powerOfTenMultiplier'] = int(meterReadingType.text)
                case 'uom' :
                    meter_endpoint_reading_type_dict['ReadingType']['uomType'] = int(meterReadingType.text)
        
        return meter_endpoint_reading_type_dict

    def get_meter_endpoint_reading(self, reading_url: str) -> dict:
        """
        Queries the endpoint Reading details endpoint at the ip address passed
        to the class.

        Returns: dict, {<element name>: <meter response>}
        """
        query_url = f'{self.url}{reading_url}'

        # query the Reading endpoint
        x = self.requests_session.get(query_url, verify=False, timeout=4.0)
        # Parse the response xml looking for the passed in element names
        #print(x.text)
        root = ET.fromstring(x.text)
        
        meter_endpoint_reading_dict = { "Reading" : { } }
        for meterReading in root.findall(f'.//{IEEE_PREFIX}*'):
            match meterReading.tag.removeprefix(IEEE_PREFIX):
                case 'qualityFlags':
                    meter_endpoint_reading_dict['Reading']['qualityFlags'] = int(meterReading.text)
                case 'timePeriod':
                    meter_endpoint_reading_dict['Reading']['timePeriod'] = {}
                    for timePeriod in meterReading.iter():
                        match timePeriod.tag.removeprefix(IEEE_PREFIX):
                            case 'duration':
                                meter_endpoint_reading_dict['Reading']['timePeriod']['duration'] = int(timePeriod.text)
                            case 'start':
                                meter_endpoint_reading_dict['Reading']['timePeriod']['start'] = int(timePeriod.text)
                case 'touTier':
                    meter_endpoint_reading_dict['Reading']['touTier'] = int(meterReading.text)
                case 'value':
                    meter_endpoint_reading_dict['Reading']['value'] = int(meterReading.text)
        
        return meter_endpoint_reading_dict
    
    def meter_reading_to_yaml(self, meterReading: list) -> dict:
        """
        Converts Meter Reading results and converts them to yaml format

        Returns: dict, {<element name>: <meter response>}
        """
        meter_reading_yaml_list = []

        for reading in meterReading:
            meter_reading_yaml_dict = {}

            # Check that Readings are valid data types
            if self.is_endpoint_reading_supported(reading['Reading']) :
                if reading['ReadingType']['kind'] == KindType.Demand.value:
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['url'] = "{}".format(reading['MeterReading']['ReadingLink'])
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags'] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value'] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['entity_type'] = 'sensor'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['device_class'] = 'power'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['unit_of_measurement'] = \
                        UomType(reading['ReadingType']['uomType']).name
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['state_class'] = 'measurement'

                if reading['ReadingType']['kind'] == KindType.Energy.value:
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['url'] = "{}".format(reading['MeterReading']['ReadingLink'])
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags'] = {}
                    
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'] = [
                        {"duration" : {}},
                        {"start" : {}}
                        ]
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][0]['duration'] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][0]['duration']['entity_type'] = 'sensor'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][0]['duration']['device_class'] = 'duration'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][0]['duration']['value_template'] = '{{ value }}'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][0]['duration']['unit_of_measurement'] = 's'

                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][1]['start'] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][1]['start']['entity_type'] = 'sensor'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][1]['start']['device_class'] = 'timestamp'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['timePeriod'][1]['start']['value_template'] = '{{ as_datetime( value ) }}'

                    if reading['Reading'].get('touTier') is not None:
                        meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['touTier'] = {'entity_type': 'sensor'}

                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value'] = {}
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['entity_type'] = 'sensor'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['device_class'] = 'energy'
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['unit_of_measurement'] = \
                        UomType(reading['ReadingType']['uomType']).name
                    meter_reading_yaml_dict[ reading['MeterReading']['Description'] ]['tags']['value']['state_class'] = 'total_increasing'

                meter_reading_yaml_list.append(
                        meter_reading_yaml_dict
                    )  
                
        # convert string into proper yaml list
        return yaml.safe_load(yaml.dump(meter_reading_yaml_list,sort_keys=False))

    def is_endpoint_reading_type_supported(self, reading_type: dict) -> bool:
        """
        Check if Meter Reading Type is supported

        Returns: bool
        """
        supportedUomType = [
            UomType.W.value,
            UomType.var.value,
            UomType.Wh.value
        ]
        supportedAccumulationBehaviorType = [
            AccumulationBehaviourType.Instantaneous.value,
            AccumulationBehaviourType.Summation.value
        ]
        supportedKindType = [
            KindType.Energy.value,
            KindType.Demand.value
        ]

        reading_type_supported = False
        
        if  reading_type['ReadingType']['uomType'] in supportedUomType and \
            reading_type['ReadingType']['accumulationBehaviour'] in supportedAccumulationBehaviorType and \
            reading_type['ReadingType']['kind'] in supportedKindType:
                reading_type_supported = True
        
        return reading_type_supported
    
    def is_endpoint_reading_supported(self, reading: dict) -> bool:
        """
        Check if Reading is supported

        Returns: bool
        """
        reading_supported = False
        
        if  reading.get('timePeriod') and \
            reading['timePeriod'].get('duration') == 1 and \
            self.is_valid_unix_timestamp(reading['timePeriod'].get('start')) and \
            reading.get('value') is not None and \
            reading.get('value') >= 0 :

            reading_supported = True
            
        return reading_supported

    def is_valid_unix_timestamp(self, timestamp) -> bool:
        try:
            datetime.datetime.fromtimestamp(timestamp)
            return True
        except ValueError:
            return False
                 
    @staticmethod
    def setup_session(creds: tuple, ip_address: str) -> requests.Session:
        """
        Creates a new requests session with the given credentials pointed
        at the give IP address. Will be shared across each xcelQuery object.

        Returns: request.session
        """
        session = requests.Session()
        session.cert = creds
        # Mount our adapter to the domain
        session.mount('https://{ip_address}', CCM8Adapter())

        return session

    def get_yaml(self) -> dict:
        """
        Main business loop. Query the Meter and gather the necessary details to
        dynamically create a YAML that defines the meter endpoints.

        This YAML can then be used to create the Home Assistant MQTT entities
        and devices.

        Returns: None
        """
        # XML Entries we're looking for within the endpoint
        meter_usage_point_info_names = ['MeterReadingListLink']
        # Endpoint of the meter used for HW info
        meter_usage_point_info_url = self._meterUsagePoint
        # Query the meter to get some more details about it

        #print('Get Usage Point Details')
        details_dict = self.get_meter_usage_point_details(meter_usage_point_info_url, meter_usage_point_info_names)
        self._meterUsagePointUrl = details_dict['MeterReadingListLink']['href']
        self._meterUsagePointNumberOfEndpoints =  details_dict['MeterReadingListLink']['all']
        
        #print('Get MeterReading Details')
        meterReading_details_dict = self.get_meter_endpoint_details(self._meterUsagePointUrl, self._meterUsagePointNumberOfEndpoints)

        return self.meter_reading_to_yaml(meterReading_details_dict)
        

