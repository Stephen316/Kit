from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.EmitMeshPart import (
    EmitMeshPart,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


def AlterMeshParts(
    Parts: tuple[ContainerPart, ...], Model: DocumentModel, Variant: str
) -> tuple[ContainerPart, ...]:
    Selected = Model.Meshes[-1]
    if Variant == "missing":
        return tuple(
            PartValue for PartValue in Parts if PartValue.Name != Selected.Name
        )
    Registry = ReplaceValue(
        Selected.Mesh.Registry, FusionId="59dcdd31-60bc-4c81-8b4b-276176a9dcab"
    )
    Changed = ReplaceValue(
        Selected, Mesh=ReplaceValue(Selected.Mesh, Registry=Registry)
    )
    if Variant == "uuid":
        Replacement = EmitMeshPart(Changed)
        return tuple(
            Replacement if PartValue.Name == Selected.Name else PartValue
            for PartValue in Parts
        )
    if Variant == "orphan":
        NameValue = "ParaMeshGeometry.BlobParts/ParaMeshGeometry.5b829ae6-700e-433f-b74a-e4bc7f986170.paramesh"
        return Parts + (EmitMeshPart(ReplaceValue(Changed, Name=NameValue)),)
    raise ValueError("Unknown mesh part mutation")
