# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from pathlib import Path as FilePath

from convert.adapters.base import Destination
from convert.adapters.base import WriteOptions
from convert.adapters.base import WriteResult
from convert.adapters.json.Metadata import KInfoValue
from convert.adapters.json.StreamIo import WriteStream
from interchange import CadDocument


# this mixin gives stream and filesystem destinations one writing policy
class JsonWriter:

    # this writer validates and emits deterministic utf eight json
    def EmitTarget(
        self,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        Settings = Options or WriteOptions()
        if Settings.validate:
            DocValue.assert_valid()
        Payload = (DocValue.to_json() + "\n").encode("utf-8")
        if isinstance(Target, (str, FilePath)):
            Output = FilePath(Target).expanduser().resolve()
            if Output.exists() and not Settings.overwrite:
                raise FileExistsError(Output)
            Output.parent.mkdir(parents=True, exist_ok=True)
            _ = Output.write_bytes(Payload)
            return WriteResult(
                Output,
                KInfoValue.format_id,
                len(Payload),
                application_usable=True,
                vendor_loadable=True,
            )
        WriteStream(Target, Payload.decode("utf-8"), Payload)
        return WriteResult(
            None,
            KInfoValue.format_id,
            len(Payload),
            application_usable=True,
            vendor_loadable=True,
        )
