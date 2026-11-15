from sys import argv as ArgValues


# ordinary commands must avoid metadata imports unless version discovery was explicitly requested
def ReadVersion() -> str:
    for Argument in ArgValues[1:]:
        if Argument in (
            "--",
            "-h",
            "--help",
            "formats",
            "convert",
            "decode",
            "research",
        ):
            return ""
        if Argument == "--version":
            from importlib.metadata import version as GetVersion

            return GetVersion("unicad-kit")
    return ""
