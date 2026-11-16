from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the draft subjects contract needs a shared interpretation so model state retains its native feature and ownership relationships
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
