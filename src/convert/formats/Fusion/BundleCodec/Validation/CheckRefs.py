from uuid import UUID

from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs


def CheckRefs(Value: BundleRefs, ObjectIds: set[int]) -> None:
    Targets = set(Value.Targets)
    if not Targets or len(Targets) != len(Value.Targets) or not Targets <= ObjectIds:
        raise ValueError("Invalid Fusion bundle reference targets")
    if {Entry.TargetId for Entry in Value.Relations} != Targets:
        raise ValueError("Fusion bundle relationship targets disagree")
    Roles: set[str] = set()
    for Entry in Value.Relations:
        Metadata = {Field.FieldName: Field.TextValue for Field in Entry.Metadata}
        RoleValue = Metadata.get("neutronRole", "")
        RoleGuid, Separator, RoleTarget = RoleValue.partition("_")
        if Separator and (len(RoleGuid) != 36 or not RoleTarget.startswith("urn:")):
            raise ValueError("Invalid Fusion bundle relationship role")
        try:
            RoleKey = str(UUID(RoleGuid)) + Separator + RoleTarget
        except (ValueError, AttributeError) as ErrorInfo:
            raise ValueError("Invalid Fusion bundle relationship role") from ErrorInfo
        if RoleKey in Roles:
            raise ValueError("Duplicate Fusion bundle relationship role")
        Roles.add(RoleKey)
