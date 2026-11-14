# Archive export does not write an F3Z bundle

## Expectation

`createFusionArchiveExportOptions` with a target name that ends in `.f3z` writes an F3Z bundle for an assembly with external references.

## Actual behavior

Fusion 2706.1.17 wrote one F3D file named `R9_archive.f3z.f3d`.
The file has the same member layout as the other root exports.
It has no `RedirectionsStream.dat` and no `ComponentReferenceData.json`.
The referenced designs are not in the file.

## Workaround

Use a native F3Z bundle, for example `re/Fusion/examples/.f3z/example1.f3z`, as dependency graph evidence.
Do not expect the API archive export to include the referenced designs.
Look for the produced file by its stem, because Fusion appends `.f3d`.

## Evidence

- [Configuration control script](../../../../../re/Fusion/LocalOracle/LinksConfigs/CreateConfigControls.py), stage `archive_probe`
- [Native controls](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json), control `R9_archive`
- [Dependency graph change](../../../../Changes/Fusion/Assembly/FusionDependencyGraph.md)
