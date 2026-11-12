from interchange.enums.EnumBase import WireEnum


# unit identity prevents adapters from silently changing dimensional interpretation
class UnitSystem(WireEnum):
    MILLIMETER = "mm"
    METER = "m"
    INCH = "in"
    KMillimeter = "mm"
    KMeter = "m"
    KInch = "in"
