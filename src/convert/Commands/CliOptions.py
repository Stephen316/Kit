from argparse import Namespace
from pathlib import Path as FilePath


class CliOptions(Namespace):
    def __init__(self) -> None:
        super().__init__()
        self.Command = ""
        self.Source = FilePath()
        self.Destination: FilePath | None = None
        self.SourceFormat: str | None = None
        self.DestFormat: str | None = None
        self.Configuration: str | None = None
        self.JsonOutput = False
        self.Overwrite = False
        self.Partial = False
        self.Layer = "neutral"
        self.StreamName: str | None = None
