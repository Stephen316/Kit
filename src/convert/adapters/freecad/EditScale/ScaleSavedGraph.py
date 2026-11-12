from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditScale.ScaleSavedGraphFields import CheckSavedProps
from convert.adapters.freecad.EditScale.ScaleSavedGraphXml import CheckGraphTree
from convert.adapters.freecad.Native import ParseObjects


# saved scale geometry can change only through the controls in the original native graph
def CheckScaleGraph(Expected: Element, Actual: Element) -> None:
    CheckGraphTree(Expected)
    CheckGraphTree(Actual)
    Original = {Value.name: Value for Value in ParseObjects(Expected)}
    Current = {Value.name: Value for Value in ParseObjects(Actual)}
    if Original.keys() != Current.keys():
        raise ValueError("FreeCAD editable Scale native object inventory changed")
    Seeds = {Value.name for Value in Original.values() if Value.touched}
    Pending = {Value.name for Value in Current.values() if Value.touched}
    if Pending and Pending != Seeds:
        raise ValueError("FreeCAD editable Scale native rebuild is pending")
    for NameValue, Saved in Current.items():
        Template = Original[NameValue]
        if (
            Saved.type_id != Template.type_id
            or Saved.object_id != Template.object_id
            or set(Saved.dependencies) != set(Template.dependencies)
        ):
            raise ValueError(
                f"FreeCAD editable Scale native object {NameValue} routing changed"
            )
        CheckSavedProps(Template, Saved, bool(Pending))
