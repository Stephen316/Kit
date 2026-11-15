from xml.etree.ElementTree import ParseError  # noqa: DUO107

from convert.adapters.base import ParseUntrusted
from convert.adapters.solidworks.core.LinearDisplay import LinearDisplay

# source display metadata lives outside the feature and geometry streams
KInformationStream = "docProps/ISolidWorksInformation.xml"

# typed unit codes require the variant property namespace to establish their meaning
KIntegerTag = "{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}i4"

# source display metadata must come from the expected property document
KInformationTag = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/"
    "SolidworksInformation-properties}Properties"
)

# confirmed source display codes give lengths a reliable unit context
KLinearUnits = {"0": "mm", "3": "in"}


# canonical projection needs source display precision to qualify exact inch scalars
def ParseDisplay(Content: bytes) -> LinearDisplay | None:
    if not Content:
        return None
    try:
        RootValue = ParseUntrusted(Content)
    except (ParseError, ValueError):
        return None
    if RootValue.tag != KInformationTag:
        return None
    SectionList = RootValue.findall("propertySection[@name='UserDefinedProperties']")
    if len(SectionList) != 1:
        return None
    Section = SectionList[0]
    Values: dict[str, str] = {}
    for NameValue in ("Linear", "LinearDecimalDisplay", "LinearDecimalPlaces"):
        Items = Section.findall(f"property[@name='SW_Units{NameValue}']")
        if len(Items) == 1 and len(Items[0]) == 1 and Items[0][0].tag == KIntegerTag:
            Values[NameValue] = (Items[0][0].text or "").strip()
    UnitName = KLinearUnits.get(Values.get("Linear", ""))
    if UnitName is None:
        return None
    Places = Values.get("LinearDecimalPlaces", "")
    Decimals = (
        int(Places)
        if Values.get("LinearDecimalDisplay") == "1"
        and len(Places) == 1
        and Places in "0123456789"
        else None
    )
    return LinearDisplay(UnitName, Decimals)
