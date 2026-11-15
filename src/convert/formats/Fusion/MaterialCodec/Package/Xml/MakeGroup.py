from xml.etree.ElementTree import Element as XmlElement, SubElement


# the group operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def MakeGroup(GroupName: str) -> tuple[XmlElement, XmlElement]:
    RootValue = XmlElement("root", {"version": "1", "name": "root"})
    return RootValue, SubElement(RootValue, "group", {"name": GroupName})
