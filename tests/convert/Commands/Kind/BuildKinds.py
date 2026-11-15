from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.assembly.AssemblyEnums import ComponentKind, MateEntityKind, MateKind
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from tests.convert.Commands.BuildTypedAsm import BuildTypedAsm


# open kind coverage needs known equivalent values and opaque variants on otherwise qualified models
def BuildKinds(RecordName: str, Variant: str) -> CadDocument:
    KnownValue, NativeValue = {
        "Component": (ComponentKind.KPart, ComponentKind.KNative),
        "Mate": (MateKind.KCoincident, MateKind.KNative),
        "MateEntity": (MateEntityKind.KPlane, MateEntityKind.KNative),
        "SketchEntity": (GeometryKind.KPoint, GeometryKind.KNative),
        "SketchRelation": (ConstraintKind.KHorizontal, ConstraintKind.KNative),
    }[RecordName]
    KindValue = {
        "KnownEnum": KnownValue,
        "KnownText": str(KnownValue),
        "NativeEnum": NativeValue,
        "NativeText": str(NativeValue),
        "Unknown": "vendor_unknown",
    }[Variant]
    Document = (
        BuildTypedAsm()
        if RecordName in ("Component", "Mate", "MateEntity")
        else MakeFusionDoc(
            DocumentSpec(
                "Typed kind history",
                "height",
                20.0,
                ProfileKind="cuboid",
                ConstrainRectangle=True,
            )
        )
    )
    if RecordName == "Component":
        assert Document.assembly is not None
        Assembly = Document.assembly
        return ReplaceData(
            Document,
            assembly=ReplaceData(
                Assembly,
                definitions=(
                    *Assembly.definitions[:-1],
                    ReplaceData(Assembly.definitions[-1], kind=KindValue),
                ),
            ),
        )
    if RecordName == "Mate":
        assert Document.assembly is not None
        Assembly = Document.assembly
        return ReplaceData(
            Document,
            assembly=ReplaceData(
                Assembly,
                mates=(
                    ReplaceData(Assembly.mates[0], kind=KindValue),
                    *Assembly.mates[1:],
                ),
            ),
        )
    if RecordName == "MateEntity":
        assert Document.assembly is not None
        Assembly = Document.assembly
        return ReplaceData(
            Document,
            assembly=ReplaceData(
                Assembly,
                mate_entities=(
                    ReplaceData(Assembly.mate_entities[0], kind=KindValue),
                    *Assembly.mate_entities[1:],
                ),
            ),
        )
    Sketch = Document.sketches[0]
    if RecordName == "SketchEntity":
        Sketch = ReplaceData(
            Sketch,
            entities=(
                ReplaceData(Sketch.entities[0], kind=KindValue),
                *Sketch.entities[1:],
            ),
        )
    else:
        Sketch = ReplaceData(
            Sketch,
            constraints=tuple(
                (
                    ReplaceData(Relation, kind=KindValue)
                    if Relation.kind == ConstraintKind.KHorizontal
                    else Relation
                )
                for Relation in Sketch.constraints
            ),
        )
    return ReplaceData(Document, sketches=(Sketch, *Document.sketches[1:]))
