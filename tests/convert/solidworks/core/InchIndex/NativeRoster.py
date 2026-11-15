from dataclasses import asdict as AsDictionary
import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from convert.adapters.solidworks.core.LinearDisplay import LinearDisplay
from convert.adapters.solidworks.core.Native import DecodeNative


def ParseRoster() -> None:
    Model = DecodeNative(
        FilePath(System.argv[1]).read_bytes(),
        FilePath(System.argv[2]).read_bytes(),
        Display=LinearDisplay("in", 2),
    )
    Report: dict[str, object] = {
        "features": [
            {
                "id": Feature.object_id,
                "dimensions": [
                    AsDictionary(Dimension) for Dimension in Feature.dimensions
                ],
            }
            for Feature in Model.features
        ],
        "scalars": [AsDictionary(Scalar) for Scalar in Model.scalars],
        "diagnostics": list(Model.diagnostics),
    }
    _ = System.stdout.write(JsonCodec.dumps(Report))


if __name__ == "__main__":
    ParseRoster()
