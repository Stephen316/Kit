# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from inspect import Signature as FuncSig

from interchange.compatibility.PythonCompatMethods import BindAliasMut, MakeParam


# brep callers retain historical validation reflection while canonical methods stay compliant
def BindBrepMut(ModelType: type) -> None:
    BindAliasMut(
        ModelType,
        "GetErrors",
        "validate",
        {
            "design_body_ids": "frozenset[str]",
            "return": "tuple[str, ...]",
        },
        FuncSig(
            (
                MakeParam("self"),
                MakeParam(
                    "design_body_ids",
                    DefaultValue=frozenset[str](),
                    AnnotValue="frozenset[str]",
                ),
            ),
            return_annotation="tuple[str, ...]",
        ),
    )
