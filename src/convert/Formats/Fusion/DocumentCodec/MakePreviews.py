from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview


# the previews operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def MakePreviews() -> tuple[ContainerPart, ...]:
    return tuple(
        ContainerPart(
            "Previews/" + NameValue + ".png",
            EmitPreview(Length, Length, bytes((242, 242, 242, 255)) * Length * Length),
        )
        for NameValue, Length in (("big", 256), ("small", 64))
    )
