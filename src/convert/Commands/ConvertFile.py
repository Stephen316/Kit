from convert.api.ApiContext import GetRegistry
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.Commands.CheckPortable import CheckPortable
from convert.Commands.CliOptions import CliOptions
from convert.Commands.WriteReport import WriteReport
from convert.formats.SourceFormat import ResolveFormat


# file conversion must preserve reader identity while enforcing portable data and native writer policy
def ConvertFile(Options: CliOptions) -> dict[str, object]:
    if Options.Destination is None:
        raise ValueError("Conversion requires a destination")
    Registry = GetRegistry()
    DestFormat = Options.DestFormat
    if DestFormat is None:
        Writers = tuple(
            Adapter
            for Adapter in Registry.GetWriters()
            if Options.Destination.suffix.casefold()
            in {Extension.casefold() for Extension in Adapter.info.Extensions}
        )
        if not Writers:
            raise ValueError(
                "no writer supports the destination suffix; use --to FORMAT"
            )
        if len(Writers) != 1:
            raise ValueError("Destination suffix is ambiguous; use --to FORMAT")
        DestFormat = Writers[0].info.FormatId
    Reader = (
        Registry.GetReader(Options.SourceFormat)
        if Options.SourceFormat
        else Registry.PickReader(Options.Source)
    )
    Document = OpenDocument(
        Options.Source,
        SourceFormat=Reader.info.FormatId,
        Configuration=Options.Configuration,
        StrictMode=True,
    )
    CheckPortable(Document)
    Result = WriteDocument(
        Document,
        Options.Destination,
        DestFormat=DestFormat,
        Configuration=Options.Configuration,
        Overwrite=Options.Overwrite,
        ValidateData=True,
        AllowCarrier=False,
        InputValues={"require_native_transfers": True},
    )
    return {
        "source_format": ResolveFormat(Document, Reader),
        "destination_format": Result.AdapterName,
        **WriteReport(Result),
    }
