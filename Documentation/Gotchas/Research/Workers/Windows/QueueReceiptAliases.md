# Reserved-name APIs do not provide one stable Windows alias policy

## Expectation

A reserved-device-name check also excludes alternate streams and ambiguous trailing-dot or trailing-space receipt names on every supported Python runtime.

## Actual behavior

The [CPython 3.12.10 `PureWindowsPath.is_reserved` implementation](https://github.com/python/cpython/blob/v3.12.10/Lib/pathlib.py) reduces the final component to a device-name stem before checking its reserved-name set.
A non-device stream name such as `x:stream` therefore does not satisfy that check.
The [CPython 3.13.0 `ntpath.isreserved` implementation](https://github.com/python/cpython/blob/v3.13.0/Lib/ntpath.py) additionally checks colons, trailing dots or spaces, control characters and other reserved characters in the path tail after `splitroot`.
That source also shows why a pathname API cannot replace a component check: `x:stream` is parsed as drive-relative, so its drive colon is outside the checked tail.
The [Python documentation](https://docs.python.org/3.13/library/os.path.html#os.path.isreserved) identifies the API as added in 3.13 and describes its rules as an approximation that can change.
These are source observations, not a local Windows reproduction.

## Workaround

The [Windows receipt guard](../../../../Changes/Research/Workers/Windows/WindowsFusionQueueReceipts.md) explicitly rejects ambiguous characters and suffixes in every non-anchor component before calling the available reserved-name API.
It then uses `ntpath.isreserved` when present and the existing `PureWindowsPath` device-name fallback otherwise.
Protected owner directory/file guards remain necessary; name checks do not establish file custody.
Dedicated Windows process coverage exercises stream, device, trailing-dot, hardlink and conflicting-record refusals.
Local verification was static; hosted Windows execution remains required.
