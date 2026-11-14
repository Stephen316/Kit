# Older Fusion saves declare class versions that the catalog lacks

## Expectation

The packaged class catalog holds every class version that a Fusion save declares. The reader can then pick the schema by the version in the metadata row.

## Actual behavior

The three older example files declare 48 class versions that the catalog does not hold. They are `re/Fusion/examples/.f3d/example2.f3d` and the two copies of `example1.f3z`. The reader raised `Unqualified Fusion native class or schema version`.

The versions fall into three groups:

- Eight versions decode with the members of the next catalog version, minus 0, 1 or 2 members. Exactly one member set decodes every record of the version.
- Six versions decode with more than one member set. The records do not show which member the save lacks.
- 34 classes have no catalog schema at any version.

Five ACT classes also moved. At version 0 or 1 they sit in the `CommonData` class space on the `CommonBaseEntity`, `CommonBaseRootCollection` and `CommonBaseGroupEntity` bases. Their own members equal the newest version.

`Joint` version 5 derives from `AssyConstraint` `B96995C7`, a class that only the packaged native catalog holds. The ACT and Browser profiles had no schema for that base.

## Workaround

Pick each class version from the metadata row, with the base that the row names. `HistoricClasses.json` holds the eight unique layouts. Its rows are format rules derived from the catalog, not copies of saved bytes.

Give every other declared version an opaque schema. The metadata offset index bounds each record, so an opaque class keeps its own and inherited member bytes whole. Its group ends the lineage, because the base groups follow the own members. A value object of an opaque class still raises, because no index bounds it.

The ACT and Browser profiles take the exact version for declared classes and the newest version for the rest. They drop undeclared schemas whose base is absent.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#example-class-versions)
- [Inferred layouts](../../../../../re/Fusion/Reconstruction/ReadGaps/VersionLayouts.json)
- [Layout inference](../../../../../re/Fusion/Reconstruction/ReadGaps/InferVersions.py)
