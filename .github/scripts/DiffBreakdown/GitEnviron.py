from __future__ import annotations

import base64 as BaseCodec
import os as OsLib

KHeaderKey = "http.https://github.com/.extraheader"


def BuildGitEnv() -> dict[str, str]:
    EnvValues = {
        **OsLib.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    TokenText = EnvValues.get("GH_TOKEN", "")
    if not TokenText:
        return EnvValues
    Credential = BaseCodec.b64encode(f"x-access-token:{TokenText}".encode()).decode()
    return {
        **EnvValues,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": KHeaderKey,
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {Credential}",
    }
