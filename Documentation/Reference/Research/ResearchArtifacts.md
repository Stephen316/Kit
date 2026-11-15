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

The [repository ignore rules](../../../.gitignore) exclude DLL and DMG filenames everywhere, including mixed-case extensions.
The [research ignore rules](../../../re/.gitignore) also cover other common executable, library, symbol, and installer extensions.
They do not identify every proprietary file.
Inspect archive members and file contents before staging research inputs.
Never use `git add -f` to include an ignored vendor artifact.

## Repository guard

The `Verify path policies` CI job rejects every tracked DLL or DMG path, including files added with ignored-file overrides.
It scans the complete Git index on pull requests, merge-group candidates, and pushes to `main`.
It also checks paths introduced by incoming commits, including binaries removed before the final revision.
The existing CI allowlist includes this job for pull requests and the merge queue.
The guard runs on each candidate without reusing a PR report.

From a repository checkout with Bash and Git available, inspect the current index:

```sh
bash .github/scripts/CheckBinaries.sh
```

An optional directory argument selects another checkout or a directory inside it.
Pass a base and head revision after the directory to also inspect incoming commits:

```sh
bash .github/scripts/CheckBinaries.sh . origin/main HEAD
```

Exit code zero means no prohibited paths are tracked.
Exit code one reports prohibited paths with shell-escaped filenames.
Exit code two means the arguments or Git input are invalid.
Remove each reported path from the index and keep authorized software outside repository checkouts.

The guard checks filenames, including mixed-case extensions.
It does not inspect archive members, detect renamed vendor software, rewrite existing history, or stop local commits before CI runs.
The vendor software restriction still covers those cases.
See [the guard change](../../Changes/Git/VendorBinaryGuard.md) and [the ignore-rule limitation](../../Gotchas/Git/IgnoreRulesDoNotBlockTrackedFiles.md).

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
