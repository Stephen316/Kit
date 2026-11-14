from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds


def CreateMatIds() -> MaterialIds:
    return MaterialIds(
        PackageId=str(MakeUuid()),
        AssetId=str(MakeUuid()),
        LibraryId=str(MakeUuid()),
        PhysicalId=str(MakeUuid()),
        StructuralId=str(MakeUuid()),
        ThermalId=str(MakeUuid()),
        AppearanceId=str(MakeUuid()),
        PhysicalDef=str(MakeUuid()),
        StructuralDef=str(MakeUuid()),
        ThermalDef=str(MakeUuid()),
        AppearanceDef=str(MakeUuid()),
        PartName="ProteinAsset." + str(MakeUuid()) + ".protein",
    )
