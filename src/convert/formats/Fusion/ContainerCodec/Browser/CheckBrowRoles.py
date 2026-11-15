from convert.formats.Fusion.ContainerCodec.Browser.BrowserTargets import KBrowserTargets
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult


# invalid brow roles input must fail here so archive members retain their native ownership and reference relationships
def CheckBrowRoles(Design: DesignResult) -> None:
    if Design.Streams.SegmentId != 0:
        raise ValueError("Fusion browser requires the active design segment")
    Owners = {
        Entry.ObjectId: Entry.Groups[0].ClassGuid.upper()
        for Entry in Design.Records
        if Entry.IsPrimary and Entry.Groups
    }
    for RoleName, ClassGuid in KBrowserTargets.items():
        if Owners.get(Design.Roles.get(RoleName, -1)) != ClassGuid:
            raise ValueError("Fusion browser role has an incompatible design target")
