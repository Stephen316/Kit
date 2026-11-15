from collections.abc import Callable
from json import dumps as DumpJson
import sys as System
from sys import argv as ArgValues
from typing import NoReturn

from convert.adapters.base.UsabilityError import UsabilityError
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.Commands.BuildParser import BuildParser
from convert.Commands.CliOptions import CliOptions
from convert.Commands.ReadVersion import ReadVersion
from convert.Commands.RunCommand import RunCommand


# command failures need stable exit codes and machine readable diagnostics for shell callers
def MainEntry(ResearchRunner: Callable[[CliOptions], NoReturn] | None = None) -> int:
    try:
        if any(len(Value) > 4096 or not Value.isprintable() for Value in ArgValues[1:]):
            raise ValueError(
                "Arguments must contain at most 4096 characters and no control characters"
            )
        Options = CliOptions()
        _ = BuildParser(ReadVersion()).parse_args(namespace=Options)
        Options.Source = Options.Source.expanduser()
        if Options.Destination is not None:
            Options.Destination = Options.Destination.expanduser()
        if Options.Command == "research":
            if ResearchRunner is None:
                raise ValueError("Run research with kit or python -m KitCli")
            ResearchRunner(Options)
        RunCommand(Options)
        return 0
    except BrokenPipeError:
        return 1
    except KeyboardInterrupt:
        print("kit: interrupted", file=System.stderr)
        return 130
    except (
        OSError,
        ValueError,
        TypeError,
        NotImplementedError,
        RegistryError,
        UsabilityError,
    ) as Error:
        Details: dict[str, object] = {
            "error": type(Error).__name__,
            "message": str(Error),
        }
        if isinstance(Error, UsabilityError):
            Details["details"] = Error.ToMapping()
        print(DumpJson(Details, ensure_ascii=True), file=System.stderr)
        return 1
