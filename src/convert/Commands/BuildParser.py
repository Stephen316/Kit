from argparse import ArgumentParser
from importlib.metadata import version as GetVersion
from pathlib import Path as FilePath

from convert.Commands.ConvertArgs import AddConvertMut
from convert.Commands.DecodeArgs import AddDecodeMut


def BuildParser() -> ArgumentParser:
    Parser = ArgumentParser(
        prog="kit",
        description="Convert CAD files and inspect decoded data.",
        allow_abbrev=False,
    )
    _ = Parser.add_argument(
        "--version", action="version", version=GetVersion("unicad-kit")
    )
    Commands = Parser.add_subparsers(dest="Command", required=True)
    Formats = Commands.add_parser(
        "formats", help="List registered readers and writers", allow_abbrev=False
    )
    _ = Formats.add_argument(
        "--json",
        dest="JsonOutput",
        action="store_true",
        help="Print machine-readable JSON",
    )
    Convert = Commands.add_parser(
        "convert", help="Convert an input file to an output format", allow_abbrev=False
    )
    AddConvertMut(Convert)
    Decode = Commands.add_parser(
        "decode", help="Inspect decoded data for development", allow_abbrev=False
    )
    _ = Decode.add_argument("Source", type=FilePath, metavar="SOURCE")
    AddDecodeMut(Decode)
    return Parser
