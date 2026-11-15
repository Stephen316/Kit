# Windows virtual-environment launchers have separate process identities

## Expectation

A child Python process can appear to have the same PID as the `Popen` object that started it.
A readiness record can therefore appear valid only when those values are equal.

## Actual behavior

The [CPython 3.14 Windows virtual-environment redirector](https://github.com/python/cpython/blob/3.14/PC/venvlauncher.c) starts the base interpreter with `CreateProcessW`.
It waits for that interpreter and returns its exit code.
The launcher and the interpreter have different process identities.
A successful interpreter readiness record does not have to equal the launcher's PID.

The Windows tree scenario failed remotely with one retry and a queued job at revision `35080cec`.
A [subsequent Windows receipt](https://github.com/TryUniCAD/Kit/actions/runs/43666746526/job/132667719525) records exit status 1 after 10.366 seconds, without a supervisor stop reason.
The fixture's readiness deadline is ten seconds.
Its assertion originally hid the full retry reason through pytest truncation.
The failure report now prints the job, events and available result artifact, including retained stderr.
The timing does not identify the throwing line by itself.
The invalid PID equality is independently established by the CPython source.
No local Windows reproduction ran.

## Workaround

Record the application PID and its actual parent PID separately from the launcher PID.
Accept direct execution only when the application equals the launcher and its parent equals the caller.
Accept redirected execution only when the application's parent equals the launcher.
Verify the caller, launcher and application against the supervisor's recorded job object.
Check that every distinct recorded process has exited after the scenario.
Do not replace identity checks with file existence or an arbitrary delay.
