# A driven extrusion does not qualify an undimensioned profile

A cylinder can have a live extrusion distance while its circle radius remains a
literal sketch value with no driving constraint. Checking sketch dimensions only
for bodyless documents leaves that solid profile unqualified. A matching SDK
serialization contract alone does not supply missing driving dimensions.

The CLI checks active parameter-bound driving constraints on every sketch before
SDK regeneration, whether or not the document contains bodies. Default
undimensioned cylinders and cuboids remain inspectable but cannot be converted.
Constrained SDK cuboids keep qualified conversion and native roundtrip coverage.

See [the model guard](../../../Changes/Commands/ParametricModelGuard.md).
