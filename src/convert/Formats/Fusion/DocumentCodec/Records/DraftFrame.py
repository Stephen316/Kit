from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.Formats.Fusion.DocumentCodec.Records.DraftNamed import DraftNamed
from convert.Formats.Fusion.DocumentCodec.Records.DraftSubjects import DraftSubjects
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame


# the draft frame contract needs a shared interpretation so model state retains its native feature and ownership relationships
def DraftFrame(Author: AuthorState, Entity: DraftEntity) -> EntityFrame:
    Subjects = DraftSubjects(Author, Entity)
    Metadata = (
        None
        if Entity.NamedPairs is None
        else tuple(DraftNamed(Author, Entry) for Entry in Entity.NamedPairs)
    )
    return EntityFrame(Entity.RootName, Subjects, Metadata)
