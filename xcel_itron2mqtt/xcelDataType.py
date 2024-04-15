from enum import Enum
import datetime
import time

class AccumulationBehaviourType(Enum):
        NotApplicable = 0
        Cumulative = 3
        DeltaData = 4
        Indicating = 6
        Summation = 9
        Instantaneous = 12

# https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/CommodityType
class CommodityType(Enum):
        NotApplicable = 0
        ElectricitySecondaryMetered = 1
        ElectricityPrimaryMetered = 2

# https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/DataQualifierType
class DataQualifierType(Enum):
        NotApplicable = 0
        Average = 2
        Maximum = 8
        Minimum = 9
        Normal = 12
        # <summary>
        # Standard Deviation of a Population (typically indicated by a lower case sigma)
        # </summary>
        StandardDeviationPopulation = 29
        # <summary>
        # Standard Deviation of a Sample Drawn from a Population (typically indicated by a lower case 's')
        # </summary>
        StandardDeviationSample = 30

class DateTimeInterval():
    duration = int
    start = float

    def startDateTime(start: float) -> datetime:
        return datetime.datetime.fromtimestamp(start, datetime.timezone.utc)


# https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/FlowDirectionType
class FlowDirectionType(Enum):
    NotApplicable = 0
    # <summary>
    # delivered to customer
    # </summary>
    Forward = 1
    # <summary>
    # received from customer
    # </summary>
    Reverse = 19

    # Reserved types that Itron uses based on Table C.4 of IEC 61968-9 [61968] Edition 1.0 (2009-09):

    # <summary>
    # (absolute value of forward - absolute value of reverse)
    # </summary>
    Net = 4
    # <summary>
    # (absolute value of forward + absolute value of reverse)
    # </summary>
    Total = 20

# https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/CommodityType
class KindType(Enum):
    NotApplicable = 0
    Currency = 3
    Demand = 8
    Energy = 12
    Power = 37
    
class MeterReadingType(Enum):
    Undetermined = 0 # by default registers are set to undetermined.
    InstantaneousDemand = 1
    CurrentSummationDelivered = 2
    CurrentSummationReceived = 3
    VARhDelivered = 4
    VARhReceived = 5
    VAhDelivered = 6
    VAhReceived = 7
    PhaseA = 8
    PhaseB = 9
    PhaseC = 10
    PhaseABC = 11
    MaxDemandReceived = 12
    MaxDemandDelivered = 13
    WhIntervalDelivered = 14
    WhIntervalReceived = 15
    TOUWhReceived = 16
    TOUWhDelivered = 17
    VARhIntervalDelivered = 18
    VARhIntervalReceived = 19
    VAhIntervalDelivered = 20
    VAhIntervalReceived = 21
    WhIntervalNet = 22

# https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/PhaseCode
class PhaseCode(Enum):
    NotApplicable = 0
    # <summary>
    # Phase C (and S2)
    # </summary>
    C = 32
    # <summary>
    # Phase CN (and S2N)
    # </summary>
    CN = 33
    # <summary>
    # Phase CA
    # </summary>
    CA = 40
    # <summary>
    # Phase B
    # </summary>
    B = 64
    # <summary>
    # Phase BN
    # </summary>
    BN = 65
    # <summary>
    # Phase BC
    # </summary>
    BC = 66
    # <summary>
    # Phase A (and S1)
    # </summary>
    A = 128
    # <summary>
    # Phase AN (and S1N)
    # </summary>
    AN = 129
    # <summary>
    # Phase AB
    # </summary>
    AB = 132
    # <summary>
    # Phase ABC
    # </summary>
    ABC = 224

class ServiceKind(Enum):
    Electricity = 0
    Gas = 1
    Water = 2
    Time = 3
    Pressure = 4
    Heat = 5
    Cooling = 6

class ServiceStatus(Enum):
    Off = 0
    On = 1

class SubscribableType(Enum):
    ResourceDoesNotSupportSubscriptions = 0
    ResourceSupportsNonConditionalSubscriptions = 1
    ResourceSupportsConditionalSubscriptions = 2
    ResourceSupportsBothConditionalAndNonConditionalSubscriptions = 3

#https://zepben.github.io/evolve/docs/2030-5/2030-5/SmartGrid/IEEE2030-5/Common/Types/UomType
class UomType(Enum):
    NotApplicable = 0
    # <summary>
    # A (Current in Amperes (RMS))
    # </summary>
    Amps = 5
    Voltage = 29
    # <summary>
    # W (Real power in Watts)
    # </summary>
    W = 38
    # <summary>
    # VA (Apparent power)
    # </summary>
    VA = 61
    # <summary>
    # var (Reactive power)
    # </summary>
    var = 63
    # <summary>
    #  CosTheta (Displacement Power Factor)
    # </summary>
    CosTheta = 65
    # <summary>
    # V² (Volts squared)
    # </summary>
    V2 = 67
    # <summary>
    # A² (Amp squared)
    # </summary>
    A2 = 69
    # <summary>
    # VAh (Apparent energy)
    # </summary>
    VAh = 71
    # <summary>
    #  Wh (Real energy in Watt-hours)
    # </summary>
    Wh = 72
    # <summary>
    # varh (Reactive energy)
    # </summary>
    VARh = 73
    # <summary>
    # Ah (Ampere-hours / Available Charge)
    # </summary>
    Ah = 106


class TOUType(Enum):
    NotApplicable = 0  # default if not specified
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6
    G = 7
    H = 8
    I = 9
    J = 10
    K = 11
    L = 12
    M = 13
    N = 14
    O = 15

