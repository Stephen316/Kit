from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Records.DraftNamed import DraftNamed
from convert.formats.Fusion.DocumentCodec.Records.DraftSubjects import DraftSubjects
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame


def DraftFrame(Author: AuthorState, Entity: DraftEntity) -> EntityFrame:
    Subjects = DraftSubjects(Author, Entity)
    Metadata = (
        None
        if Entity.NamedPairs is None
        else tuple(DraftNamed(Author, Entry) for Entry in Entity.NamedPairs)
    )
    return EntityFrame(Entity.RootName, Subjects, Metadata)
