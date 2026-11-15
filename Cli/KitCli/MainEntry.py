from convert.Commands.MainEntry import MainEntry as RuntimeEntry
from KitCli.RunResearch import RunResearch


# research process access belongs to the explicit developer command composition
def MainEntry() -> int:
    return RuntimeEntry(ResearchRunner=RunResearch)
