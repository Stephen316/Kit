"""Read the witnessed modern face occurrence and its enclosing reference plane."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KNullKind,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.resolved.support.FaceFrame import ReadFacePose as read_transform
from convert.adapters.solidworks.resolved.FaceIdentity import (
    ReadFaceHead as read_face_header,
    ReadFaceReturn as read_face_tail,
    ReadSurfaceId,
)
from SketchRoot import KGeneration


# the witnessed chain begins with already established archive class and object ownership
class FaceCursor(ArchiveCursor):
    def __init__(self, blob, position, next_index, classes, objects, null_events=None):
        super().__init__(blob, position, next_index, classes, objects)
        self.null_events = null_events

    @property
    def blob(self):
        return self.BlobValue

    @property
    def position(self):
        return self.Offset

    @position.setter
    def position(self, value):
        self.Offset = value

    @property
    def next_index(self):
        return self.NextIndex

    @next_index.setter
    def next_index(self, value):
        self.NextIndex = value

    @property
    def classes(self):
        return self.Classes

    @property
    def objects(self):
        return self.Objects

    read = ArchiveCursor.ReadValue
    vector = ArchiveCursor.ReadPoint

    # face and resolved records use the witnessed compact tag branch
    def pointer(self, kind, name=None):
        _, _, index = self.TakePointer((name,), kind, CompactOnly=True)
        return index

    # report adapters retain null events even when packaged parsers consume them
    def TakePointer(self, *args, **options):
        offset, counter = self.Offset, self.NextIndex
        result = super().TakePointer(*args, **options)
        if self.null_events is not None and result[0].kind == KNullKind:
            self.null_events.append(
                (offset, counter, KNullKind, None, 0)
            )
        return result

    null = ArchiveCursor.ReadNull

# report calls retain their historical keyword arguments
def read_surface_id(cursor, kind, cap=False, pointer_kind=KClassRefKind):
    return ReadSurfaceId(cursor, kind, pointer_kind, IsCap=cap)


# the cut chooser retains its existing local owner call
def read_local_component(cursor):
    return ReadLocalPart(cursor, KGeneration)
