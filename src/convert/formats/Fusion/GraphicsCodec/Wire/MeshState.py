from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)


class MeshState:
    def __init__(
        self,
        Streams: tuple[GraphicsStream, ...],
        IsReading: bool,
        Slack: tuple[GraphicsStream, ...] = (),
    ) -> None:
        super().__init__()
        self.IsReading = IsReading
        self.Inputs = {Entry.StreamIndex: Entry.Payload for Entry in Streams}
        self.Ranges: dict[int, dict[tuple[int, int], bytes]] = {}
        self.Tails = {Entry.StreamIndex: Entry.Payload for Entry in Slack}
        if (
            len(self.Inputs) != len(Streams)
            or len(self.Tails) != len(Slack)
            or any(
                type(Entry.StreamIndex) is not int
                or not 0 <= Entry.StreamIndex < 1000
                or type(Entry.Payload) is not bytes
                for Entry in Streams + Slack
            )
            or any(not Entry.Payload for Entry in Slack)
        ):
            raise ValueError("Invalid graphics mesh streams")
