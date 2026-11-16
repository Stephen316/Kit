from uuid import uuid4 as MakeUuid

from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds


# the create mat ids contract needs a shared interpretation so appearance references remain connected to their owning entities
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
