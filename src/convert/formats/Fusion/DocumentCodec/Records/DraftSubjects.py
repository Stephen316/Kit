from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def DraftSubjects(
    Author: AuthorState, Entity: DraftEntity
) -> tuple[SubjectValue, ...] | None:
    if not Entity.Subjects:
        return None
    Counts: dict[str, int] = {}
    for Previous in Author.Entities:
        if Previous is Entity:
            break
        for RoleName in Previous.Subjects:
            Counts[RoleName] = Counts.get(RoleName, 0) + 1
    return tuple(
        SubjectValue(LocalRef(Author.Roles[RoleName]), Counts.get(RoleName, 0))
        for RoleName in Entity.Subjects
    )
