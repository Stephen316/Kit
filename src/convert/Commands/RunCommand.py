from json import dumps as DumpJson

from convert.Commands.CheckPaths import CheckPaths
from convert.Commands.CliOptions import CliOptions
from convert.Commands.ConvertFile import ConvertFile
from convert.Commands.DecodeFile import DecodeFile
from convert.Commands.FormatReport import FormatReport
from convert.Commands.PrintFormats import PrintFormats
from convert.Commands.PrintReport import PrintReport
from convert.Commands.SaveDecode import SaveDecode


def RunCommand(Options: CliOptions) -> None:
    if Options.Command == "formats":
        Formats = FormatReport()
        if Options.JsonOutput:
            print(DumpJson(Formats, indent=2, ensure_ascii=True))
            return
        PrintFormats(Formats)
        return
    CheckPaths(Options.Source, Options.Destination)
    if Options.Command == "decode":
        Decoded = DecodeFile(Options)
        Content = (
            Decoded
            if isinstance(Decoded, str)
            else DumpJson(Decoded, indent=2, ensure_ascii=True, allow_nan=False)
        )
        if Options.Destination is None:
            print(Content)
        else:
            SaveDecode(Options.Destination, Content, Options.Overwrite)
        return
    Report = ConvertFile(Options)
    if Options.JsonOutput:
        print(DumpJson(Report, indent=2, ensure_ascii=True, allow_nan=False))
        return
    PrintReport(Report)
