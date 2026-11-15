from __future__ import annotations

import inspect as Inspect


# the bind hook contract needs a shared interpretation so dependency changes cannot revive stale passing results
def BindHookMut(HookFunc: object, ParamNames: tuple[str, ...]) -> object:
    KindValue = Inspect.Parameter.POSITIONAL_OR_KEYWORD
    Params = [Inspect.Parameter(ParamName, KindValue) for ParamName in ParamNames]
    setattr(HookFunc, "__signature__", Inspect.Signature(Params))
    return HookFunc
