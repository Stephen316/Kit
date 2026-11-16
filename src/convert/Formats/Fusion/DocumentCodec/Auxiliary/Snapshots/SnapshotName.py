from uuid import UUID as UuidValue


# snapshot name needs an explicit validity boundary so supporting records retain their owning document relationships
def SnapshotName(NameValue: str) -> None:
    Prefix = "Breps.BlobParts/BREP."
    if not NameValue.startswith(Prefix) or not NameValue.endswith(".smb"):
        raise ValueError("Unsupported Fusion snapshot part name")
    Identity = NameValue.removeprefix(Prefix).removesuffix(".smb")
    if str(UuidValue(Identity)) != Identity.lower():
        raise ValueError("Fusion snapshot identity must be a canonical UUID")
