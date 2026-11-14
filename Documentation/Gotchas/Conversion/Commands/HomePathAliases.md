# Home-relative aliases must match SDK path normalization

Resolving a path does not expand its leading `~` component.
The SDK expands home-relative source and destination paths before reading or publishing files.
An alias check using only `resolve()` can therefore miss a destination that overwrites the source.

The CLI expands and resolves both paths before identity checks and SDK calls.
It also compares existing inode identities to reject hardlink aliases.
The remote home-alias process cases exercise both conversion and decoding without changing the host home environment.
See [the command-line procedure](../../../Tasks/CommandLine.md).
