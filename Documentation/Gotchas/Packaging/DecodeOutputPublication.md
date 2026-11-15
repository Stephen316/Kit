# Temporary-file permissions survive atomic publication

A staged file might appear to inherit normal output permissions when published.
`NamedTemporaryFile` actually creates mode `0600`, regardless of the process umask.
Linking or replacing that inode retains its private mode.

The CLI creates its report inside a private temporary directory using ordinary file creation.
Publication then retains umask-filtered permissions for new files.
When replacing an output, it copies that output's permission bits before atomic replacement.
The staging directory protects unpublished report bytes.
Remote process coverage verifies the umask and replacement behavior on POSIX.
See [the CLI implementation](../../../src/convert/Commands/SaveDecode.py).
