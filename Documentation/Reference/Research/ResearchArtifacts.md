# Research artifacts

## Permitted inputs

Keep CAD files, documents, independently authored research tools, and recorded format knowledge in `re/`.
Preserve their applicable licenses and attribution.
The research exemption does not authorize redistribution of vendor software.

## Vendor software

Do not stage, commit, or distribute proprietary vendor software.
This includes SOLIDWORKS DLLs, interop assemblies, executables, installers, SDK code, symbols, license files, and decompiled vendor listings.
The restriction also covers renamed files and compressed copies.
Keep licensed installations and analysis inputs outside repository checkouts.
Record versions, hashes, addresses, and format conclusions without including vendor code.

The [research ignore rules](../../../re/.gitignore) cover common executable, library, symbol, and installer extensions, including mixed-case names.
They do not identify every proprietary file.
Inspect archive members and file contents before staging research inputs.
Never use `git add -f` to include an ignored vendor artifact.

## External inputs

The [SOLIDWORKS input guide](../../../re/binaries/README.md) describes manifest verification against an external licensed installation.
The signature-table research tool reads the installation directly, or accepts an external path through `--dll`.
Compatibility checks always compare the CAD corpus with the recorded format table.
Set `KIT_SOLIDWORKS_DLL` in an authorized environment to additionally compare the complete table with the external vendor module.
Stage that licensed module in a task-owned directory beneath the operating system's temporary root before setting the variable.
The compatibility check resolves paths through the temporary filesystem boundary and rejects symlinks that escape it.
Supply the module's absolute path; the check does not expand home-directory notation.
An explicitly configured missing file, path outside that boundary, repository-contained file, or mismatched digest fails verification.
This restriction applies to the compatibility check's environment variable; research tools retain their documented external-input interface.

Production conversion remains subject to the [CAD success criteria](../Operations/CadSuccessCriteria.md).
