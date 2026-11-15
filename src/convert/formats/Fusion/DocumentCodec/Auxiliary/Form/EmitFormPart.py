from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormName import FormName
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline


# the form part operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitFormPart(Value: DocumentForm) -> ContainerPart:
    _ = FormName(Value.Name)
    return ContainerPart(Value.Name, EmitTspline(Value.Surface))
