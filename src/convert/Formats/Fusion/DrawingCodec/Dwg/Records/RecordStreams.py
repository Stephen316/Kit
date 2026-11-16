from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


# the record streams contract needs a dedicated boundary so section boundaries and object references remain consistent
class RecordStreams:

    # record streams needs explicit initial state so section boundaries and object references remain consistent
    def __init__(
        self,
        DataCursor: BitCursor,
        TextItems: tuple[str, ...],
        HandleRefs: tuple[DwgHandleRef, ...],
        VersionText: str,
    ) -> None:
        super().__init__()
        self.DataCursor = DataCursor
        self.TextItems = TextItems
        self.TextIndex = 0
        self.HandleRefs = HandleRefs
        self.HandleIndex = 0
        self.VersionText = VersionText

    # the text operation needs a distinct decoding boundary so section boundaries and object references remain consistent
    def TakeText(self) -> str:
        if self.TextIndex >= len(self.TextItems):
            raise ValueError("DWG record reads past its string stream")
        self.TextIndex += 1
        return self.TextItems[self.TextIndex - 1]

    # the handle operation needs a distinct decoding boundary so section boundaries and object references remain consistent
    def TakeHandle(self) -> DwgHandleRef:
        if self.HandleIndex >= len(self.HandleRefs):
            raise ValueError("DWG record reads past its handle stream")
        self.HandleIndex += 1
        return self.HandleRefs[self.HandleIndex - 1]

    # the handles operation needs a distinct decoding boundary so section boundaries and object references remain consistent
    def TakeHandles(self) -> tuple[DwgHandleRef, ...]:
        Remaining = self.HandleRefs[self.HandleIndex :]
        self.HandleIndex = len(self.HandleRefs)
        return Remaining
