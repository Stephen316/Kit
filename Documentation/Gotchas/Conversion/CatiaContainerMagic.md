# CATIA container magic

`re/Methodology.md` said that CATIA V5 parts and products are CFBF containers.
A CFBF tool can then appear to show a corrupt file.
The samples in `re/catia/examples/` start with the `V5_CFV2` magic, not the CFBF signature.
Kit reads them with its own container code in `src/convert/adapters/catia/Container.py`.
Use that container code or the [CATIA adapter reference](../../Reference/Adapters/Catia.md).
Do not use a CFBF reader on these files.
The research record now marks the wrong statement.
See the [CATIA vendor notes](../../../re/Playbook/VendorNotes.md#catia-v5-catpart-catproduct-catdrawing).
