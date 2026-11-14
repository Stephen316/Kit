from json import loads as LoadJson

from convert.api.ApiOpen import OpenDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Commands.CliOptions import CliOptions
from convert.Commands.ContainerView import ContainerView
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def DecodeFile(Options: CliOptions) -> object:
    if Options.Layer != "neutral" and (
        Options.Partial or Options.Configuration is not None
    ):
        raise ValueError("--partial and --configuration require --layer neutral")
    if Options.StreamName is not None and Options.Layer != "container":
        raise ValueError("--stream requires --layer container")
    if Options.Layer == "container":
        return ContainerView(Options)
    if Options.Layer == "native":
        if (Options.SourceFormat or Options.Source.suffix).casefold() not in (
            "fusion.f3d",
            "f3d",
            ".f3d",
        ):
            raise ValueError("Native decoding currently supports Fusion F3D only")
        return EncodeState(ReadDocument(Options.Source.read_bytes()))
    Document = OpenDocument(
        Options.Source,
        SourceFormat=Options.SourceFormat,
        Configuration=Options.Configuration,
        StrictMode=not Options.Partial,
    )
    return {
        "kind": "kit.decode",
        "layer": "neutral",
        "partial": Options.Partial,
        "document": LoadJson(Document.to_json()),
    }
