from collections.abc import Iterable

from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget


# the external profile contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def ExternalProfile(
    Profile: EntityProfile, Records: Iterable[EntityRecord], SegmentId: int
) -> EntityProfile:
    Targets = tuple(
        ExternalTarget(SegmentId, Entry.ObjectId, Entry.Groups[0].ClassGuid)
        for Entry in Records
        if Entry.IsPrimary
    )
    return EntityProfile(Profile.RootGuid, Profile.Classes, Targets)
