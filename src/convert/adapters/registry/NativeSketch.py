from convert.adapters.registry.NativeRules import RuleFindings
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import NativeGeometry

# portable geometry kinds keep unresolved source shapes out of editable exports
KPortableKinds = frozenset(
    KindValue.value for KindValue in GeometryKind if KindValue != GeometryKind.NATIVE
)


# sketch export requires understood geometry and validated bindings in every profile
def SketchFindings(Document: CadDocument) -> tuple[str, ...]:
    Findings: list[str] = []
    ParamIds = frozenset(ParamValue.id for ParamValue in Document.parameters)
    for SketchValue in Document.sketches:
        for EntityValue in SketchValue.entities:
            if (
                isinstance(EntityValue.geometry, NativeGeometry)
                or EntityValue.kind not in KPortableKinds
            ):
                Findings.append(
                    f"{Document.source.path}: sketch {SketchValue.id} entity {EntityValue.id} ({EntityValue.kind})"
                )
        Findings.extend(RuleFindings(Document, SketchValue, ParamIds))
    return tuple(Findings)
