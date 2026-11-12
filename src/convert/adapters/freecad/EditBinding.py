from xml.etree.ElementTree import Element

from convert.adapters.freecad.ArchiveEditPlan import KEditableBinding


# older carrier archives have no binding but explicit bindings must remain unambiguous
def ReadEditBinding(
    RootValue: Element, PropertyName: str = KEditableBinding
) -> str | None:
    Properties = RootValue.findall(
        f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{PropertyName}']"
    )
    if not Properties:
        return None
    if len(Properties) == 1 and Properties[0].get("type") == "App::PropertyString":
        TextNodes = Properties[0].findall("String")
        if len(TextNodes) == 1 and (Binding := TextNodes[0].get("value")):
            return Binding
    raise ValueError(f"FreeCAD editable binding {PropertyName} is malformed")


# earlier editable exports recorded the shape on the final feature without a binding marker
def HasLegacyEdit(RootValue: Element) -> bool:
    MetaProps = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
    if MetaProps is None:
        return False
    Final = MetaProps.find("Property[@name='FinalFeature']/String")
    Target = MetaProps.find("Property[@name='ExternalLinkTarget']/String")
    Shape = MetaProps.find("Property[@name='CachedShapeEntry']/String")
    return (
        Final is not None
        and Target is not None
        and Shape is not None
        and bool(FeatureName := Final.get("value"))
        and Target.get("value") == FeatureName
        and Shape.get("value") == f"{FeatureName}.Shape.brp"
    )
