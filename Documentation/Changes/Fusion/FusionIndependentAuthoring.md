# Independently authored Fusion documents

## Behavior and usage

The research author creates complete native F3D archives directly from semantic specifications. It does not read a source archive, a vendor-generated blank document, captured object payloads, or a runtime graph template.
It allocates fresh persistent identities, constructs Design, ACT, and Browser graphs, and writes their metadata and bulk streams.
The research author also creates root/asset manifests, properties, preview images, and ZIP directories.
The class/version/member catalogue is declarative format vocabulary from the runtime reflection captures and the class catalogue; it supplies no saved instance values.

The [Design author](../../../re/Fusion/Reconstruction/DocumentAuthoring/README.md) documents root collections, parameter ownership, origin geometry, dependency state, component identities, and allocation policy. The [container author](../../../re/Fusion/Reconstruction/ContainerAuthoring/ContainerModel.md) documents the manifest and cross-segment relationships.

Generate the admitted parameter profile from repository root with:

```sh
python3 re/Fusion/Reconstruction/ContainerAuthoring/AuthorContainer.py --specification re/Fusion/Reconstruction/DocumentAuthoring/Specification.json --output /tmp/AuthoredParameter
```

The feature-container entry point accepts the circle specification:

```sh
python3 re/Fusion/Reconstruction/ContainerAuthoring/AuthorFeatureContainer.py --specification re/Fusion/Reconstruction/DocumentAuthoring/Variants/CircleSpecification.json --output /tmp/AuthoredCircle
```

The author is research code. These commands generate artifacts; they do not launch Fusion. Native acceptance scripts are separate and require the explicitly authorized application.

## Native acceptance

The [parameter acceptance report](../../../re/Fusion/LocalOracle/Authored/ParameterAcceptance.json) records independent archive digest `126dc166545a8c9156d6492d4b0913c675c7bf56aaa2fe33493dde03c05ae970`. Fusion 2706.1.17 restores the authored parameter `authoredLength = 17.25 mm`, its comment, and parametric design mode. Editing to 31.5 mm, rebuilding, saving, and reopening preserves the value. Subsequently creating a native circle and dependent extrusion produces a healthy solid with the expected volume. The report distinguishes those later native-created features from the contents of the independently authored input.

The [circle acceptance report](../../../re/Fusion/LocalOracle/Authored/CircleAcceptance.json) records independent archive digest `da4771d9c1dfe7c31737a2f8846b8e19fbd93189421a2a25babba1d3c80c6f37`. Its 112 Design entities and 135 physical records restore one named circular sketch, one timeline feature, one closed profile, and radius 12.5 mm. Fusion reports healthy state before and after recomputation. A radius edit to 18 mm survives native save/reopen. A subsequent native extrusion uses the authored profile and parameter, producing a healthy three-face solid with volume 17.55836134091411 cm³. Both acceptance runs close their documents.

The [extrusion acceptance report](../../../re/Fusion/LocalOracle/Authored/ExtrusionAcceptance.json) records independent archive digest `7c3dbb1a213d9a3ef5fa609a721fba2de5a5870d0249d64c7c77f07968456523`. Its complete Design, ACT, Browser, manifests, and 5,299-byte BRep history were generated from semantic inputs. The geometry payload comes from production `EmitHistory`; no source geometry or history is read. Before recomputation, Fusion exposes both healthy timeline features and a radius-12.5 mm, height-17.25 mm cylinder. The cylinder has volume 8.467573949129104 cm³, three faces, two edges, and two vertices. Rollback removes the body and retains the sketch; restoring the timeline restores the solid. Full recomputation succeeds. Editing `authoredLength` to 23 mm produces volume 11.290098598838801 cm³ and survives native save/reopen. The saved digest is `81c5f35d8bdda4f2cee8721299cc2757e496f2f386a9c26741c6d46ece000199`.

These results establish complete independently generated parameter, circle-sketch, and circular-extrusion F3D documents with editable history. They do not establish arbitrary feature families.

## Recovered load contracts

Native loading revealed independent obligations beyond byte-level parsing:

1. The admitted archive profile requires explicit ZIP directory entries for segment lookup. Changing compression alone did not repair the failure.
2. Primary entity payloads must follow increasing entity IDs. The native bulk loader traverses its ordered identity map and computes chunk lengths from adjacent offsets.
3. The empty `Breps.BlobParts/` directory is required even when the Design has no bodies.
4. Relationship Browser entries must target `AssyConstraints`, not the separate `Relationships` object. Correctly framed references to the wrong class caused a native activation crash.
5. Root manifest document-type strings, document and asset revision identities, segment allocator state, and metadata software-version fields have distinct meanings.

The [archive directory gotcha](../../Gotchas/Conversion/Fusion/FusionArchiveDirectories.md), [Browser target gotcha](../../Gotchas/Conversion/Fusion/FusionBrowserEntityRoles.md), and [metadata/header evidence](FusionMetadataHeaderSemantics.md) record the failure chain and corrections. A read-only inventory of 712 corpus archives found increasing primary identity order across all 2,136 Design/ACT/Browser segments. The inventory covered 259,464 primary records and 34,228 continuations without extraction errors.

## Limits

The current semantic author admits the documented reduced document, circle, and circular-extrusion profiles. No arbitrary drawing, assembly, T-spline, mesh, sculpt, or historical-version writing claim follows from these controls. The subsequent [production document codec](FusionNativeDocumentCodec.md) promotes complete document orchestration, typed entities, and the container, with its own successful native acceptance. Product adapter discovery remains governed by the broader acceptance requirements. Automated tests remain PR-only.
