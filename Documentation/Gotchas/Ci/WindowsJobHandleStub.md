# Windows job opener stub omits the returned handle

## Expectation

The pinned `types-pywin32==312.0.0.20261104` declaration for `win32job.OpenJobObject` should expose the handle returned by the native binding.

## Actual behavior

Mypy reports that this declaration returns `None`, making valid Job Object membership checks and handle cleanup fail static analysis. The [pywin32 binding source](https://github.com/mhammond/pywin32/blob/main/win32/src/win32job.i) declares `PyHANDLE OpenJobObject`, rather than a void result. Static analysis of `OpenProcess` also exposes an integer handle, so callers cannot rely on an inferred `.Close()` method for that API.

## Workaround

The Windows fixture retrieves the documented `OpenJobObject` runtime attribute at its platform boundary, retains the returned owning handle object until cleanup, and converts it to an integer only for the typed membership call. It closes process handles through `win32api.CloseHandle` and closes the owning job handle in `finally`. No checker suppression or global platform override is added.

Mypy and Pyright checked the fixture after this repair. Real process behavior remains verified by the Windows CI gate; a passing static check alone does not prove cleanup.
