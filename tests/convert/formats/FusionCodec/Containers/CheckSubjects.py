from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef


def CheckSubjects(Records: tuple[EntityRecord, ...], Roles: dict[str, int]) -> None:
    RootEntry = next(Entry for Entry in Records if Entry.ObjectId == 201)
    Subjects = {
        Subject.Target: Subject.ObserverIndex
        for Subject in RootEntry.Frame.Subjects or ()
    }
    assert Subjects[SegmentRef(Roles["component"], 0)] == 1
    assert Subjects[SegmentRef(Roles["component_instances"], 0)] == 0
    assert Subjects[SegmentRef(Roles["overrides"], 0)] == 0
    assert Subjects[SegmentRef(Roles["root_instance"], 0)] == 0
