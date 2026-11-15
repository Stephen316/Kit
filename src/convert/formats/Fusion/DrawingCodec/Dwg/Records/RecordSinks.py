from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


# the record sinks contract needs a dedicated boundary so section boundaries and object references remain consistent
class RecordSinks:

    # record sinks needs explicit initial state so section boundaries and object references remain consistent
    def __init__(self, VersionText: str) -> None:
        super().__init__()
        self.DataWriter = BitWriter()
        self.TextItems: list[str] = []
        self.HandleRefs: list[DwgHandleRef] = []
        self.VersionText = VersionText
