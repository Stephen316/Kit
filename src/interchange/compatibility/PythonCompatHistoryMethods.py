# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from inspect import Signature as FuncSig

from interchange.compatibility.PythonCompatMethods import BindAliasMut, MakeParam


# adapter callers retain historical predicate reflection while canonical methods stay compliant
def BindHistoryMut(AdapterType: type) -> None:
    BindAliasMut(
        AdapterType,
        "HasCapability",
        "supports",
        {"capability": "Capability", "return": "bool"},
        FuncSig(
            (MakeParam("self"), MakeParam("capability", AnnotValue="Capability")),
            return_annotation="bool",
        ),
    )
