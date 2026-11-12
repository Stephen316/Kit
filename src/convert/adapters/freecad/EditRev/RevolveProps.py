from xml.etree.ElementTree import Element, SubElement

from interchange.geometry.models.VectorSpace import SpaceVector


# each native control has one typed payload that freecad can restore directly
def RevolveProp(
    NameValue: str, PropType: str, ChildType: str, Attributes: dict[str, str]
) -> Element:
    Property = Element("Property", {"name": NameValue, "type": PropType})
    _ = SubElement(Property, ChildType, Attributes)
    return Property


# both the direction and point belong to the same world coordinate system
def RevolveVector(NameValue: str, Vector: SpaceVector) -> Element:
    return RevolveProp(
        NameValue,
        "App::PropertyVector",
        "PropertyVector",
        {
            "valueX": f"{Vector.x:.16f}",
            "valueY": f"{Vector.y:.16f}",
            "valueZ": f"{Vector.z:.16f}",
        },
    )


# the source sketch and signed angular control must remain independently editable
def MakeRevProps(
    SketchName: str,
    Origin: SpaceVector,
    Direction: SpaceVector,
    AngleDeg: float,
    Symmetric: bool = False,
    AxisSketch: str = "",
    AxisSub: str = "Edge1",
) -> list[Element]:
    AxisLink = RevolveProp(
        "AxisLink",
        "App::PropertyLinkSub",
        "LinkSub",
        {"value": AxisSketch, "count": "1" if AxisSketch else "0"},
    )
    if AxisSketch:
        _ = SubElement(AxisLink[0], "Sub", {"value": AxisSub})
    return [
        RevolveProp(
            "Angle",
            "App::PropertyFloatConstraint",
            "Float",
            {"value": f"{AngleDeg:.16f}"},
        ),
        RevolveVector("Axis", Direction),
        AxisLink,
        RevolveVector("Base", Origin),
        RevolveProp(
            "FaceMakerClass",
            "App::PropertyString",
            "String",
            {"value": "Part::FaceMakerBullseye"},
        ),
        RevolveProp("Solid", "App::PropertyBool", "Bool", {"value": "true"}),
        RevolveProp("Source", "App::PropertyLink", "Link", {"value": SketchName}),
        RevolveProp(
            "Symmetric",
            "App::PropertyBool",
            "Bool",
            {"value": "true" if Symmetric else "false"},
        ),
    ]
