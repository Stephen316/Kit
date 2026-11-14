# Independent document acceptance

This addendum supersedes the empty candidate's original pending-acceptance
status in `README.md`. The frozen generation artifacts remain unchanged.

The complete independently authored parameter F3D was accepted by Fusion
2706.1.17. The native report is
[`ParameterBrowserAccepted.json`](../../LocalOracle/Authored/ParameterBrowserAccepted.json).
The accepted archive SHA-256 is
`f6e92a059e3e9db0c914f93b17191d6019fc34b5cd321e97ee83a3c75ab813c6`.
The package combines this directory's semantic Design writer with independently
authored ACT, Browser, manifest, asset, and ZIP layers.

Native opening returned a parametric design with millimeter display units,
`authoredLength = 17.25 mm`, and no sketches, bodies, or timeline features.
The parameter changed to 31.5 mm, saved, and reopened with that value. Fusion
then created a radius-20-mm circle and extruded it using the authored parameter.
The resulting native document had two timeline features, one sketch, one solid,
three faces, healthy feature status, and volume
39.5840674352331 cubic centimeters, matching `π·2²·3.15`.

This establishes that the constructor-empty material state, absent render
settings, empty named views, single mm/MKS unit system, zero invalid-cache
timestamp, and newly allocated Design identities are sufficient for this
document profile, including subsequent native modeling. The native feature
creation portion validates the authored document foundation. The separately
authored circle and extrusion variants subsequently passed the independent
native checks below.

The initial package attempts exposed independent container/Browser problems:

- Fusion needed explicit ZIP directories and the BRep blob folder even when no
  BRep part exists
- The ACT writer initially emitted fresh identities out of physical order, and
  Fusion rejected the stream. Emitting primary offsets in entity-ID order fixed
  it. The general ordering rule came from binary inspection and is not
  confirmed by a black-box experiment beyond this case
- The Browser's relationships entry requires an `AssyConstraints` object, not
  the separate `Relationships` collection. The wrong declared target class
  survived graph loading and crashed during viewport activation

The Browser fix changed its semantic target to authored `constraints` identity
1022. This Design candidate did not need a render/default-material workaround.
The absence of render settings was therefore not the cause of the crash.

The receiving application's import names the root `Untitled`; that behavior
does not indicate a lost parameter or missing component. Save/reopen and the
subsequent feature result are bound to separate native-output hashes in the
report. Production promotion still needs repository integration checks and the
same qualified format/target-application acceptance boundaries.

## Independently authored circle

[`CircleAcceptance.json`](../../LocalOracle/Authored/CircleAcceptance.json)
records acceptance of the complete independently authored circle archive,
SHA-256 `da4771d9c1dfe7c31737a2f8846b8e19fbd93189421a2a25babba1d3c80c6f37`.
Native opening produced one healthy timeline feature, one sketch, one circle
of radius 12.5 mm, and one profile. Full computation preserved those facts.
The radius changed to 18 mm and survived save/reopen. Fusion then extruded
that independently authored profile into a healthy three-face solid.
The radius-edit output SHA-256 is
`77e11b53650ad3afd6f2079b2a8886cf0c3ad81f09fc3e428094eab67ffe19cd`.

## Independently authored extrusion

[`ExtrusionAcceptance.json`](../../LocalOracle/Authored/ExtrusionAcceptance.json)
records acceptance of the complete independently authored circle/extrusion
archive, SHA-256
`7c3dbb1a213d9a3ef5fa609a721fba2de5a5870d0249d64c7c77f07968456523`.
The archive combines fresh semantic Design, ACT, and Browser graphs with
production-generated BRep history. No source archive, vendor document
template, or donor geometry is loaded by its writer.

Before computation, native opening produced two healthy timeline features and
the expected 17.25-mm-high solid, with three faces, two edges, two vertices,
and volume 8.467573949129104 cubic centimeters. Timeline rollback removed the
solid; restoration and full rebuilding reproduced it. Changing the authored
length parameter to 23 mm changed both the dependent extrusion parameter and
the resulting solid to 23 mm, with volume 11.290098598838801 cubic centimeters.
Saving and reopening preserved the parameters, healthy timeline, and solid.
The saved output SHA-256 is
`81c5f35d8bdda4f2cee8721299cc2757e496f2f386a9c26741c6d46ece000199`.

These results qualify the explicit constructor defaults, empty optional
collections, omitted recomputable recipe/dependency caches, canonical sketch
tag states, and explicit BRep-history identities used by these particular
semantic profiles on Fusion 2706.1.17. They do not establish defaults for
arbitrary operations, arbitrary historical schema versions, noncanonical tag
states, or unrelated document classes. The independently authored variants
are therefore accepted qualified profiles rather than a universal Fusion
document generator.

## Production writer

[`ProductionDocumentAcceptance.json`](../../LocalOracle/Authored/ProductionDocumentAcceptance.json)
records native acceptance of the all-production `EmitDocument(DocumentSpec(...))`
path. It uses the production Design, ACT, Browser, entity, BRep-history, manifest,
and ZIP writers. Its runtime reads only its declared format vocabulary; it does
not load the research writers, a source archive, or a document template.

The accepted 61,439-byte archive SHA-256 is
`5645020130771517c674eac3854c2d96c00100e9bb277e353f87f35295a3d995`.
Native opening showed the correct 17.25-mm-high solid before computation and
two healthy features. Rollback removed the solid, restoration reproduced it,
and editing the length to 23 mm drove the rebuilt solid. Save/reopen preserved
the edited geometry and healthy feature history. The saved output SHA-256 is
`fcce745b873b6758ebd72cd25c1dbef72004f6b028ad4e95974a10b32b0aa3b9`.
The complete 183-class declared vocabulary, including unused classes with
empty owner lists, was accepted.

The isolated native-generation entry point is
`ProductionAcceptance.py --output <path> --profile extrusion`. Invoke it through
the repository's `uv` environment using the configured supported Python, not
the system `python3` executable: the latter resolves to Python 3.9 on the oracle
machine and cannot import the current production package. This entry point
only generates the independently authored archive; the parent native harness
performs the explicitly authorized application acceptance separately.

The production parameter profile also passed native acceptance in
[`ProductionParameterAcceptance.json`](../../LocalOracle/Authored/ProductionParameterAcceptance.json),
source SHA-256
`2ffcaf982519c106fa900192451b665828974f6192f4d84b879c123b3e80f997`.
The 17.25-mm parameter changed to 31.5 mm and survived save/reopen. Subsequent
native circle/extrusion creation produced two healthy features and a solid of
39.5840674352331 cubic centimeters.

The production circle profile passed in
[`ProductionCircleAcceptance.json`](../../LocalOracle/Authored/ProductionCircleAcceptance.json),
source SHA-256
`c5e2eab570f4d86f8e3a559996f5bb062cb080b94b91f1d819d045e9ce449690`.
Its 12.5-mm radius, one profile, and healthy sketch survived full computation;
an 18-mm edit survived save/reopen, and a subsequent native extrusion was
healthy. These reports independently qualify all three public authoring
profiles on Fusion 2706.1.17.
