from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


class RecordSinks:

    def __init__(self, VersionText: str) -> None:
        super().__init__()
        self.DataWriter = BitWriter()
        self.TextItems: list[str] = []
        self.HandleRefs: list[DwgHandleRef] = []
        self.VersionText = VersionText
