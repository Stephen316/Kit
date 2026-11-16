from collections.abc import Mapping
from typing import cast as CastValue

from convert.Commands.CheckFeatures import CheckFeatures
from convert.Commands.CheckRetained import CheckRetained
from convert.Commands.Qualified.CheckGeometry import CheckGeometry
from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.brep.Curves.BrepCurves import NativeCurve
from interchange.brep.Curves.BrepPcurves import NativePcurve
from interchange.brep.Surfaces.BrepSurfaces import NativeSurface
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.Features.FeatureKinds import NativeFeature
from interchange.geometry.Models.GeometryCurves import NativeGeometry

# unsupported records need a consistent inspection recovery path across structural guards
KInspectText = (
    " records are not conversion-ready; use kit decode or kit research for inspection"
)


# writer success must not qualify opaque records incomplete assemblies or retained source data
def CheckPortable(Document: CadDocument) -> None:
    for PartValue in WalkDocuments(Document):
        Freecad = PartValue.metadata.get("freecad")
        for RecordName, IsBlocked in (
            (
                "CapturedObjects",
                isinstance(Freecad, Mapping)
                and bool(CastValue(Mapping[object, object], Freecad).get("objects")),
            ),
            (
                "ExternalDocuments",
                isinstance(Freecad, Mapping)
                and bool(
                    CastValue(Mapping[object, object], Freecad).get(
                        "external_documents"
                    )
                ),
            ),
            (
                "UnqualifiedResearch",
                PartValue.metadata.get("kit.research_read_status") == "unqualified",
            ),
            (
                "NativeFeature",
                any(
                    isinstance(Feature.definition, NativeFeature)
                    for Feature in PartValue.FeatureTimeline
                ),
            ),
            (
                "NativeGeometry",
                any(
                    isinstance(Entity.Geometry, NativeGeometry)
                    for Sketch in PartValue.Sketches
                    for Entity in Sketch.Entities
                ),
            ),
            ("RetainedPayload", bool(PartValue.brep_payloads)),
            (
                "MissingFeatureHistory",
                not PartValue.feature_timeline
                and bool(
                    PartValue.brep is not None
                    or PartValue.meshes
                    or PartValue.bodies
                    or PartValue.sketches
                ),
            ),
        ):
            if IsBlocked:
                raise ValueError(RecordName + KInspectText)
        Assembly = PartValue.assembly
        OwnerIds = (
            {Instance.owner_definition_id for Instance in Assembly.instances}
            if Assembly is not None
            else set[str]()
        )
        if Assembly is not None and (
            any(
                Definition.kind == ComponentKind.KNative
                or Definition.attributes.get("source_resolved") is False
                or Definition.attributes.get("source_resolution") == "deferred"
                or (
                    Definition.kind in (ComponentKind.KPart, ComponentKind.KReference)
                    and not (
                        Definition.document_id
                        or Definition.body_ids
                        or Definition.mesh_ids
                        or Definition.id in OwnerIds
                    )
                )
                for Definition in Assembly.definitions
            )
            or any(
                Instance.attributes.get("transform_resolved") is False
                for Instance in Assembly.instances
            )
            or any(
                Assembly.attributes.get(FieldName)
                in ("native-only", "native_only", "unresolved")
                for FieldName in ("transform_status", "constraint_status")
            )
        ):
            raise ValueError("IncompleteAssembly" + KInspectText)
        if PartValue.brep is not None:
            for Geometry in (
                *PartValue.brep.curves,
                *PartValue.brep.pcurves,
                *PartValue.brep.surfaces,
            ):
                if isinstance(Geometry, (NativeCurve, NativePcurve, NativeSurface)):
                    raise ValueError(type(Geometry).__name__ + KInspectText)
        CheckFeatures(PartValue)
    CheckRetained(Document)
    for PartValue in WalkDocuments(Document):
        CheckGeometry(PartValue)
    for PartValue in WalkDocuments(Document):
        if PartValue.assembly is not None and PartValue.assembly.instances:
            raise ValueError("UnqualifiedAssembly" + KInspectText)
        if not PartValue.feature_timeline:
            raise ValueError("MissingFeatureHistory" + KInspectText)
