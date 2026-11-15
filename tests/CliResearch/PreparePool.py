from json import dumps as DumpJson
from pathlib import Path as FilePath
from sys import executable as KPythonPath

from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# session lifecycle coverage needs an actual configured runner and isolated durable state
def PreparePool(WorkPath: FilePath) -> FilePath:
    StorePath = WorkPath / "Store"
    Started = ResearchCli(
        WorkPath, "controller", "--store", str(StorePath), "init", "--max-running", "8"
    )
    assert Started.returncode == 0, Started.stderr
    SchemaPath = WorkPath / "ResultSchema.json"
    _ = SchemaPath.write_text(
        DumpJson(
            {
                "type": "object",
                "required": ["count", "inputs", "tokenless"],
                "additionalProperties": False,
                "properties": {
                    "count": {"type": "integer", "minimum": 0},
                    "inputs": {"type": "array", "items": {"type": "string"}},
                    "tokenless": {"type": "boolean", "const": True},
                },
            }
        )
    )
    RunnerPath = ResearchRoot() / "tests/Research/SessionRunner.py"
    assert RunnerPath.is_file()
    RegistryPath = WorkPath / "Runners.json"
    _ = RegistryPath.write_text(
        DumpJson(
            {
                "runners": {
                    "fixture.decode": {
                        "pool": "decode",
                        "argv": [KPythonPath, str(RunnerPath), "{session}"],
                        "result_schema": str(SchemaPath),
                    }
                }
            }
        )
    )
    ConfigPath = WorkPath / "Supervisor.json"
    _ = ConfigPath.write_text(
        DumpJson(
            {
                "state": str(WorkPath / "SupervisorState"),
                "controller": {"adapter": "a03", "store": str(StorePath)},
                "registry": str(RegistryPath),
                "worker": "cli:fixture",
                "pools": {"decode": {"max_sessions": 1}},
                "stop_grace_seconds": 1,
                "poll_seconds": 0.1,
            }
        )
    )
    return ConfigPath
