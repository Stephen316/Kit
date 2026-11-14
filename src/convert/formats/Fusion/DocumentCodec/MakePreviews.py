from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview


def MakePreviews() -> tuple[ContainerPart, ...]:
    return tuple(
        ContainerPart(
            "Previews/" + NameValue + ".png",
            EmitPreview(Length, Length, bytes((242, 242, 242, 255)) * Length * Length),
        )
        for NameValue, Length in (("big", 256), ("small", 64))
    )
