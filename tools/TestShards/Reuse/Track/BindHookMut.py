from __future__ import annotations

import inspect as Inspect


def BindHookMut(HookFunc: object, ParamNames: tuple[str, ...]) -> object:
    KindValue = Inspect.Parameter.POSITIONAL_OR_KEYWORD
    Params = [Inspect.Parameter(ParamName, KindValue) for ParamName in ParamNames]
    setattr(HookFunc, "__signature__", Inspect.Signature(Params))
    return HookFunc
