from dataclasses import replace as ChangeRecord

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureKinds import RefPlaneFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import (
    LineGeometry,
    NativeGeometry,
    PointGeometry,
)
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


# authored rectangle coordinates provide an exact editable profile without captured vendor data
def MakeEntities(Prefix: str, Scale: float) -> tuple[SketchEntity, ...]:
    Points = ((0.0, 0.0), (40.0, 0.0), (40.0, 20.0), (0.0, 20.0))
    return tuple(
        SketchEntity(
            f"{Prefix}edge{Index}",
            GeometryKind.KLine,
            LineGeometry(
                PlaneVector(Start[0] / Scale, Start[1] / Scale),
                PlaneVector(Finish[0] / Scale, Finish[1] / Scale),
            ),
        )
        for Index, (Start, Finish) in enumerate(zip(Points, Points[1:] + Points[:1]))
    )


# explicit solver relations retain design intent independently of identical profile geometry
def MakeRelations(Prefix: str) -> tuple[SketchRelation, ...]:
    return tuple(
        SketchRelation(
            f"{Prefix}relation{Index}",
            KindName,
            (ConstraintRef(f"{Prefix}edge{Index}"),),
        )
        for Index, KindName in enumerate(
            ("horizontal", "vertical", "horizontal", "vertical")
        )
    ) + (
        SketchRelation(
            f"{Prefix}widthrel",
            "distance",
            (ConstraintRef(f"{Prefix}edge0"),),
            parameter_id=f"{Prefix}width",
        ),
        SketchRelation(
            f"{Prefix}heightrel",
            "distance",
            (ConstraintRef(f"{Prefix}edge1"),),
            parameter_id=f"{Prefix}height",
        ),
    )


# owned dimensions exercise unit conversion without baking geometry scale into parameter identity
def MakeParams(Prefix: str, Scale: float, UnitName: str) -> tuple[Parameter, ...]:
    return tuple(
        Parameter(
            f"{Prefix}{NameText}",
            f"dimension {Prefix}{NameText}",
            ParameterValue(Number / Scale, ValueKind.KLength, UnitName),
            owner_id=f"{Prefix}{OwnerName}",
        )
        for NameText, Number, OwnerName in (
            ("width", 40.0, "sketch"),
            ("height", 20.0, "sketch"),
            ("depth", 8.0, "boss"),
        )
    )


# typed datum and extrusion history make dependency changes observable through real document validation
def MakeFeatures(Prefix: str, UnitName: str) -> tuple[FeatureStep, ...]:
    return (
        FeatureStep(
            f"{Prefix}datum",
            f"datum {Prefix}",
            FeatureKind.KReference,
            0,
            definition=RefPlaneFeature(
                f"{Prefix}plane",
                f"{Prefix}plane",
                ParameterValue(0.0, ValueKind.KLength, UnitName),
            ),
        ),
        FeatureStep(
            f"{Prefix}boss",
            f"boss {Prefix}",
            FeatureKind.KExtrusion,
            1,
            input_feature_ids=(f"{Prefix}datum",),
            sketch_id=f"{Prefix}sketch",
            parameter_ids=(f"{Prefix}depth",),
            operation=BooleanOp.KCreate,
            definition=DistanceExtrude(f"{Prefix}depth", SpaceVector(0.0, 0.0, 1.0)),
        ),
    )


# independently constructed models let identifier and collection changes cross the actual codec boundary
def MakeDocument(Prefix: str = "first", UnitName: str = "mm") -> CadDocument:
    Scale = 25.4 if UnitName == "in" else 1.0
    return CadDocument(
        source=CadSource("authored", f"{Prefix}.authored", "0" * 64),
        configurations=(
            Configuration(f"{Prefix}config", f"configuration {Prefix}", True),
        ),
        parameters=MakeParams(Prefix, Scale, UnitName),
        support_planes=(
            SupportPlane(f"{Prefix}plane", f"plane {Prefix}", Transform()),
        ),
        sketches=(
            Sketch(
                f"{Prefix}sketch",
                f"profile {Prefix}",
                f"{Prefix}plane",
                MakeEntities(Prefix, Scale),
                MakeRelations(Prefix),
                (f"{Prefix}width", f"{Prefix}height"),
                (tuple(f"{Prefix}edge{Index}" for Index in range(4)),),
            ),
        ),
        selections=(),
        feature_timeline=MakeFeatures(Prefix, UnitName),
        bodies=(DesignBody(f"{Prefix}body", f"solid {Prefix}", f"{Prefix}boss"),),
    )


# storage permutations retain ordered profile topology while changing unordered record collections
def PermuteModel(Document: CadDocument) -> CadDocument:
    Profile = Document.sketches[0]
    return ChangeRecord(
        Document,
        parameters=tuple(reversed(Document.parameters)),
        sketches=(
            ChangeRecord(
                Profile,
                entities=tuple(reversed(Profile.entities)),
                constraints=tuple(reversed(Profile.constraints)),
                parameter_ids=tuple(reversed(Profile.parameter_ids)),
            ),
        ),
    )


# independently varied semantic fields separate design intent from unchanged visible geometry
def ChangeSemantic(Document: CadDocument, ChangeName: str) -> CadDocument:
    if ChangeName == "dependency":
        return ChangeRecord(
            Document,
            feature_timeline=(
                Document.feature_timeline[0],
                ChangeRecord(Document.feature_timeline[1], input_feature_ids=()),
            ),
        )
    if ChangeName == "relation":
        Profile = Document.sketches[0]
        Relation = ChangeRecord(Profile.constraints[0], kind="vertical")
        return ChangeRecord(
            Document,
            sketches=(
                ChangeRecord(
                    Profile, constraints=(Relation,) + Profile.constraints[1:]
                ),
            ),
        )
    Parameter = Document.parameters[0]
    if ChangeName == "role":
        Parameter = ChangeRecord(Parameter, role=ParameterRole.KReference)
    elif ChangeName == "expression":
        Parameter = ChangeRecord(Parameter, expression=Expression("20 + 20"))
    elif ChangeName == "expression_dependency":
        Parameter = ChangeRecord(
            Parameter, expression=Expression("20 + 20", (Document.parameters[1].id,))
        )
    else:
        raise ValueError(f"unknown semantic change {ChangeName}")
    return ChangeRecord(Document, parameters=(Parameter,) + Document.parameters[1:])


# duplicated isolated points create genuine graph symmetry without relying on renamed identities
def MakeSymmetric() -> CadDocument:
    Document = MakeDocument()
    Profile = Document.sketches[0]
    Points = tuple(
        SketchEntity(
            f"duplicate{Index}",
            GeometryKind.KPoint,
            PointGeometry(PlaneVector(5.0, 7.0)),
        )
        for Index in range(2)
    )
    return ChangeRecord(
        Document, sketches=(ChangeRecord(Profile, entities=Profile.entities + Points),)
    )


# retained unsupported domains must block equality even when their observed content is identical
def MakeUnresolved(ChangeName: str) -> CadDocument:
    Document = MakeDocument()
    if ChangeName == "metadata":
        return ChangeRecord(
            Document, metadata={"authored_native_bytes": b"independently authored"}
        )
    if ChangeName == "brep":
        return ChangeRecord(Document, brep=BrepModel())
    if ChangeName == "assembly":
        return ChangeRecord(
            Document,
            assembly=AssemblyData(
                "rootassembly",
                (ComponentDef("rootassembly", "root", ComponentKind.KAssembly),),
                (),
            ),
        )
    if ChangeName == "mesh":
        return ChangeRecord(
            Document,
            meshes=(
                SurfaceMesh(
                    "triangle",
                    "triangle",
                    (
                        SpaceVector(0.0, 0.0, 0.0),
                        SpaceVector(1.0, 0.0, 0.0),
                        SpaceVector(0.0, 1.0, 0.0),
                    ),
                    ((0, 1, 2),),
                ),
            ),
        )
    if ChangeName != "native":
        raise ValueError(f"unknown unresolved domain {ChangeName}")
    Profile = Document.sketches[0]
    Entity = SketchEntity(
        "authorednative",
        GeometryKind.KNative,
        NativeGeometry("authored", "unknown", {"bytes": b"authored"}),
    )
    return ChangeRecord(
        Document,
        sketches=(ChangeRecord(Profile, entities=Profile.entities + (Entity,)),),
    )
