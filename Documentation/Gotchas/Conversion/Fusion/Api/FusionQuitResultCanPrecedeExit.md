# A Fusion quit error can precede the actual exit

## Expectation

A graceful AppleScript quit should either keep Fusion running after a `User cancelled` error, or stop it immediately.
A caller could use that return value to decide whether a fresh process can start.

## Actual behavior

The preflight probe recorded Fusion 2706.1.17 process 98846 with zero open documents.
The quit call returned `User cancelled` with error -128.
The subsequent bridge request failed with `ECONNREFUSED` on `127.0.0.1:9766`.
A direct application-state query then returned `running = false`.
No forced termination ran, and no open document was affected.

Therefore the AppleScript result did not establish the final process state.

## Workaround

Record the open-document count before requesting an oracle restart.
Do not force termination after a quit error.
Check the application's actual running state before starting another process.
Start Fusion only when it is stopped and the preflight count is zero.
The [session recovery record](../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/SessionRecovery.json) preserves this sequence.
The [native report](../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) records the resulting process id and its difference from the preflight id.
