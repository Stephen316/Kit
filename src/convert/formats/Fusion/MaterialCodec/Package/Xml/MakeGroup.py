from xml.etree.ElementTree import Element as XmlElement, SubElement


def MakeGroup(GroupName: str) -> tuple[XmlElement, XmlElement]:
    RootValue = XmlElement("root", {"version": "1", "name": "root"})
    return RootValue, SubElement(RootValue, "group", {"name": GroupName})
