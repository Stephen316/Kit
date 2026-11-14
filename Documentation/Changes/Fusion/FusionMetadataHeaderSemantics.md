# Fusion metadata header semantics

## Behavior

Kit now names previously positional metadata header fields.
The [header model](../../../re/Fusion/Reconstruction/HeaderGrammar/HeaderModel.md) explains the fields.
Most names first came from binary inspection, which was removed at the tip.
Only the software version below also has saved-document evidence.

`MetaHeader.HeaderWords` holds one little-endian 64-bit saved software version.
Its construction is `(major << 50) | (minor << 38) | build`.
The controlled words `(17, 709361728)` decode to Fusion version `2706.1.17`, the version that saved the controls.
The widths of 14 bits for major and 12 bits for minor came from binary inspection.
One saved version does not confirm them.

Kit reads the wide UUID once called `Namespace` as the segment's `currentVersion`.
It reads the storage identifier fields as segment type, add-in, and neutron type.
It reads the following word as a count of ancestry UUIDs, each in counted UTF-16 text.
These readings came from binary inspection and are not confirmed by a black-box experiment.
The qualified controls have no ancestry entries.

Binary inspection also read the two manifest root UUIDs as document identity and current version.
It read the value 5 before segment declarations as the next segment ID, not a format constant.
It read the per-module version maps as persisted migrator numbers.
These readings are not confirmed by a black-box experiment.

## Evidence and limits

This addition interprets existing fields. It does not expand production header support.
Current production framing admits the observed empty-ancestry profile only.
No local automated tests ran for this documentation and research addition.
