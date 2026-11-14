from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialPlan import (
    MaterialPlan,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFacts import FindSchema
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KFinishFields,
    KFinishOrder,
    KMechanicFields,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def PlanMaterial(
    SpecValue: MaterialSpec, Indexed: dict[str, SchemaNode]
) -> MaterialPlan:
    Structural = FindSchema(Indexed, "Structural", SpecValue.ClassName)
    if Structural is None:
        raise ValueError("Material class has no Fusion structural schema")
    Elastic = KMechanicFields["YoungModulus"][0]
    if (
        Elastic in SchemaFields(Structural, Indexed)
        and SpecValue.Mechanics.YoungModulus is None
    ):
        Structural = FindSchema(Indexed, "Structural", "Basic")
        if Structural is None:
            raise ValueError("Fusion vocabulary lacks the basic structural schema")
    Thermal = None
    if SpecValue.Thermal is not None:
        Thermal = FindSchema(Indexed, "Thermal", SpecValue.ClassName) or FindSchema(
            Indexed, "Thermal", "Solid"
        )
        if Thermal is None:
            raise ValueError("Material class has no Fusion thermal schema")
    FinishName, FinishLocal = FinishSchema(SpecValue.Finish, Indexed)
    return MaterialPlan(Structural, Thermal, FinishName, FinishLocal)


def FinishSchema(Finish: FinishSpec, Indexed: dict[str, SchemaNode]) -> tuple[str, str]:
    Given = tuple(
        FieldKey for FieldKey in KFinishFields if getattr(Finish, FieldKey) is not None
    )
    for LocalValue in ("Metal",) if Finish.Metallic else KFinishOrder:
        NameValue = FindSchema(Indexed, "materialappearance", LocalValue)
        if NameValue is None:
            continue
        Fields = SchemaFields(NameValue, Indexed)
        if all(
            any(Candidate in Fields for Candidate in KFinishFields[FieldKey])
            for FieldKey in Given
        ):
            return NameValue, LocalValue
    raise ValueError("No Fusion appearance schema holds every given finish property")
