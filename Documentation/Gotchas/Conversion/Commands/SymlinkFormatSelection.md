# Canonical identity must not replace format-selection filenames

A recognized filename can be a symlink to an extensionless stored object.
Resolving that filename before format selection discards the suffix used by developer decoding.
Resolving a destination symlink can similarly discard the writer suffix.

The CLI expands home-relative paths while retaining supplied filenames for selection.
Its source-protection checks separately compare resolved paths and existing inode identities.
Decode publication resolves its final target after format selection and source-protection checks.
Remote process coverage exercises all decode layers and output publication through extensionless symlink targets.
See [the CLI procedure](../../../Tasks/CommandLine.md).
