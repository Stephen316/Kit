from collections.abc import Iterable

from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget


def ExternalProfile(
    Profile: EntityProfile, Records: Iterable[EntityRecord], SegmentId: int
) -> EntityProfile:
    Targets = tuple(
        ExternalTarget(SegmentId, Entry.ObjectId, Entry.Groups[0].ClassGuid)
        for Entry in Records
        if Entry.IsPrimary
    )
    return EntityProfile(Profile.RootGuid, Profile.Classes, Targets)
