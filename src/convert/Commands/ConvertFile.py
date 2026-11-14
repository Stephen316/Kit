from convert.api.ApiConvert import ConvertFile as ConvertDoc
from convert.Commands.CliOptions import CliOptions
from convert.Commands.WriteReport import WriteReport


def ConvertFile(Options: CliOptions) -> dict[str, object]:
    if Options.Destination is None:
        raise ValueError("Conversion requires a destination")
    Result = ConvertDoc(
        Options.Source,
        Options.Destination,
        SourceFormat=Options.SourceFormat,
        DestFormat=Options.DestFormat,
        Configuration=Options.Configuration,
        Overwrite=Options.Overwrite,
        StrictMode=True,
        AllowCarrier=False,
    )
    return {
        "source_format": Result.source_format,
        "destination_format": Result.destination_format,
        **WriteReport(Result.output),
    }
