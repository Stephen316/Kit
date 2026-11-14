from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Reading.PickBodyView import PickBodyView
from convert.formats.Fusion.DocumentCodec.Reading.ReadTypedBody import ReadTypedBody


def ReadBodyPart(Value: ContainerPart) -> DocumentBody:
    if not Value.Name.startswith("Breps.BlobParts/BREP.") or not Value.Name.endswith(
        ".smbh"
    ):
        raise ValueError("Unsupported Fusion document part")
    if type(Value.Payload) is not bytes or not 0 < len(Value.Payload) <= KJournalBytes:
        raise ValueError("Invalid or oversized Fusion document history")
    Journal = ReadJournal(Value.Payload)
    Typed = ReadTypedBody(Value.Payload, PickBodyView(Journal))
    return DocumentBody(Value.Name, Journal if Typed is None else Typed)
