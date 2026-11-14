from argparse import ArgumentParser
from pathlib import Path as FilePath


def AddDecodeMut(Parser: ArgumentParser) -> None:
    _ = Parser.add_argument(
        "-o",
        "--output",
        dest="Destination",
        type=FilePath,
        help="Save JSON instead of printing it",
    )
    _ = Parser.add_argument(
        "--from",
        dest="SourceFormat",
        metavar="FORMAT",
        help="Explicit reader format or alias",
    )
    _ = Parser.add_argument(
        "--configuration",
        dest="Configuration",
        help="Named configuration for neutral decoding",
    )
    _ = Parser.add_argument(
        "--layer",
        dest="Layer",
        choices=("neutral", "container", "native"),
        default="neutral",
        help="Neutral model, container inventory, or typed Fusion native state",
    )
    _ = Parser.add_argument(
        "--partial",
        dest="Partial",
        action="store_true",
        help="Use the partial neutral reader for research; does not establish conversion support",
    )
    _ = Parser.add_argument(
        "--stream",
        dest="StreamName",
        metavar="NAME",
        help="Include one exact container stream as base64 (maximum 16 MiB)",
    )
    _ = Parser.add_argument(
        "--overwrite",
        dest="Overwrite",
        action="store_true",
        help="Replace an existing JSON output",
    )
