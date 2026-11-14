from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormName import FormName
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline


def ReadFormPart(Value: ContainerPart) -> DocumentForm:
    _ = FormName(Value.Name)
    if type(Value.Payload) is not bytes or not 0 < len(Value.Payload) <= 16777216:
        raise ValueError("Invalid or oversized document T-spline part")
    Surface = ReadTspline(Value.Payload)
    if EmitTspline(Surface) != Value.Payload:
        raise ValueError("Noncanonical document T-spline part")
    return DocumentForm(Value.Name, Surface)
