from argparse import ArgumentParser, REMAINDER as KArgRemainder
from pathlib import Path as FilePath

from convert.Commands.ResearchTools import KResearchScripts


# deterministic research tools need a trusted checkout and unchanged downstream arguments
def AddResearchMut(Parser: ArgumentParser) -> None:
    _ = Parser.add_argument(
        "--root",
        dest="ResearchRoot",
        type=FilePath,
        required=True,
        help="Trusted PR94 checkout whose research code and SDK will execute",
    )
    _ = Parser.add_argument(
        "ResearchTool",
        choices=tuple(KResearchScripts),
        help="Pinned readers, corpus, durable controller, or configured supervisor",
    )
    _ = Parser.add_argument(
        "ToolArgs",
        nargs=KArgRemainder,
        metavar="ARG",
        help="Arguments forwarded unchanged to the selected research tool; use TOOL --help",
    )
