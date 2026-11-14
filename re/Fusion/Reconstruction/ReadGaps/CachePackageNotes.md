# Fusion cache and package gaps

## Goal

Close the last two read and round-trip gaps of the read-gap sweep:

1. The package writer cannot write a material package with a `Resources` folder tree. `EmitMatPart` refuses it, so `example1.f3z` member 7 fails its round trip.
2. The OGS graphics cache of `example1.f3z` members 0, 3, 5, 6 and 8 does not read.

Both copies of `example1.f3z` are tracked: `re/Fusion/examples/.f3z/example1.f3z` and `re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z`. Member numbers follow `ReadBundle` order, as in the sweep. `PackageCensus.py` and `GraphicsCensus.py` label bundle documents by ZIP order instead (`zip N`).

## Tools

| Script | Use |
| --- | --- |
| `PackageCensus.py` | Lists every material package in the corpus, its asset folder links, its core field order and its ZIP member order. Writes `PackageCensus.json`. |
| `FolderSpy.py` | Prints the masked XML of chosen members of a package. |
| `TryPackage.py` | Reads a package with resources, writes it, and compares members and models. |
| `GraphicsCensus.py` | Lists every OGS world in the corpus, its serializer header and the class names it holds. Writes `GraphicsCensus.json`. |
| `CacheSpy.py`, `TraceCache.py`, `PathSpy.py` | Load one bundle scene, trace the reader, and census `PersistentPassiveNodePath` objects. |

## Material resource folders

### Corpus

`PackageCensus.py` reads all 1,679 material packages of the 1,709 tracked files.

| Asset folder links | Packages |
| --- | --- |
| `AssetData`, `Schemas` | 1,677 |
| `AssetData`, `Resources`, `Schemas` | 2 |

The two packages with resources are member 7 of the two `example1.f3z` copies. Their member layouts are equal. So all evidence for the folder layout comes from one saved package, but the package holds six resource subtrees with the same shape.

### Layout

- The asset folder `cnx.xml` links `AssetData`, `Resources` and `Schemas`, in that order.
- `Resources/core.xml` is an asset node named `Resources`.
- `Resources/cnx.xml` links one folder per asset that has resources. Here the six names are sorted.
- Each folder holds a `core.xml` asset node whose `name` is the folder name. Its fields are `identifier`, `created`, `name`, `updated` and `updates`. No folder core has `embed option`, `last saved` or `read only`.
- Each folder holds a `cnx.xml`. It either links child folders by name with bare `<link name=...>` elements, or lists resources with `schema.autodesk.data.1.resource` links.
- A resource link has the same four fields as the `AssetData` links: `created`, `interop%20content` 0, `name` and `type` `application/octet-stream`. The link name equals the file name, which has no extension.
- A resource file lies next to the `cnx.xml` that lists it.
- In this package each subtree is `<asset>/thumbnail/0/<file>`, with one PNG file.

### Member order and field order

Fusion orders the members of a package as data files, then `cnx.xml` files, then `[Content_Types].xml` and `autodesk-design-package.xml`, then `core.xml` files. 1,408 packages use that order. Kit writes its own order, and 267 Kit-written packages in the corpus use it. Fusion opens them, so member order is not part of the format.

Fusion writes folder cores as `identifier, created, name, updated, updates` in 1,408 packages and as `created, identifier, ...` in 4 others (`re/Fusion/LocalOracle/Features`). The reader ignores field order. The writer keeps its single `EmitCore` order for every folder, as it does for `AssetData` and `Schemas`.

### Writer rule

`FolderEntries` writes a `PackageFolder` at a path:

- `core.xml` from the folder core.
- `cnx.xml` with resource links when the folder has resources, and the resource files next to it from `Contents`.
- Otherwise `cnx.xml` with one link per child folder, in model order, and each child folder under its name.

`PackageEntries` links `AssetData`, `Resources` and `Schemas` when `MaterialPackage.Resources` is set, and writes the tree under `Resources/`. Every byte comes from the package model. `EmitMatPart` no longer refuses such packages.

### Check

`TryPackage.py re/Fusion/examples/.f3z/example1.f3z 7`:

- The package model round-trips, and the written package has the same 72 member names.
- 8 members are byte-equal and 59 XML members hold equal fields. The 5 others are the re-encoded streams and XML that Kit writes with self-closed links, as for every package.
- `ReadDocument(EmitParsed(model)) == model` for the document.

The package round trip is model-exact, as for the other 1,677 packages.

## Graphics caches

### Corpus

`GraphicsCensus.py` reads the `world` member of all 1,725 documents without the codec. 1,480 documents have one. It parses the serializer header and counts the length-prefixed class names.

| Serializer header | Worlds |
| --- | --- |
| `BillBoardAttribute` 2, `TextureEffectAttribute` 1, all nine classes | 780 |
| `BillBoardAttribute` 2, `TextureEffectAttribute` 2, all nine classes | 683 |
| `BillBoardAttribute` 1, `TextureEffectAttribute` 1, all nine classes | 15 |
| `BillBoardAttribute` 1, `F360InstanceNode` 0, no `GraphicsBlobFeatures` | 2 |

| Class | Worlds |
| --- | --- |
| `OverrideTransformAttribute`, `OverrideVisibilityAttribute`, `OverrideInActivatedVisibilityAttribute` | 2 |
| `PersistentPassiveNodePath` | 2 |
| `FProteinEffectAttribute` | 2 |

Each row with 2 worlds is one `example1.f3z` member in its two copies. So each rule below rests on one saved document. The rules are checked by reading the whole world to its last byte, with every mesh stream byte referenced, and by the document checks that follow.

### Serializer header without `GraphicsBlobFeatures` (member 0)

The header of member 0 names eight classes. It lacks `GraphicsBlobFeatures` and declares `F360InstanceNode` version 0. No Kit layout reads the `GraphicsBlobFeatures` version, so its absence changes nothing that Kit reads.

The world holds one instance node payload (selector 4). After `IsXref`, a version 1 payload holds a `u32` instance id. The version 0 payload ends after `IsXref`: the next bytes are the `WorldSerializerEndMark` class name. With this rule the world reads to its end.

Rule: `GraphicsBlobFeatures` may be absent from the header. `F360InstanceNode` may be version 0 or 1. A version 0 instance payload has no instance id.

### Protein effect attribute (member 5)

Member 5 holds one `FProteinEffectAttribute`, in a child set with `IsSpecific` 1 and flags `0x20`. After the priority and tie flag, it holds one length-prefixed UTF-16 text, an appearance asset id of 36 characters. The child set's apply types follow (`[16]`), then the node fields. With the one-field rule the world reads to its end.

Rule: `FProteinEffectAttribute` holds `AssetReference` text, like the first field of `FPrioritizedProteinAttribute`.

### Override attributes (member 3)

Member 3 is an assembly. Its instance nodes carry attribute sets of kind 3 whose child sets hold override attributes: 159 `OverrideTransformAttribute`, 4 `OverrideVisibilityAttribute` and 8 `OverrideInActivatedVisibilityAttribute`. `OverrideSpy.py` parses these sets by hand, and `PathSpy.py` counts the shapes.

Each override attribute links a `PersistentPassiveNodePath` object, like the `AlphaImageSelectionQualifier` link: a flag, the class name, an object id text and, on first use, the body. 171 path objects hold:

- `u32` count, then per entry a `u32` segment id and a big-endian `u64` object id. This is the entry layout of a graphics entity link.

The paths have 2, 3, 4 or 6 entries (23, 12, 24 and 112 paths). They name occurrence chains. 36 last entries name no record of this document, so they point into referenced documents. Kit keeps them as `PathEntity` values, which `CheckDocScene` does not check.

`OverrideTransformAttribute` fields:

1. `Transform`: 16 `f32`.
2. `Absolute`: flag.
3. `NodePath`: linked `PersistentPassiveNodePath`.
4. `Target`: a flag, then either a big-endian `u64` object id and a `u32` segment id (flag 1), or a node id text (flag 0). This is the target layout of a kind 3 attribute set.
5. `Overrides`: a `u32` count of override sets.

`OverrideVisibilityAttribute` holds a `Visibility` flag, then fields 3 to 5. `OverrideInActivatedVisibilityAttribute` holds a `Visibility` flag and `NodePath` only. Its 8 copies sit in child sets with `IsSpecific` 1, and the 8 bytes after the path are exactly the apply types `[0x10000]`. So it has no target and no override sets.

An override set is a child set (`IsSpecific`, flags, removed flags, append types, attributes), then a target, then an `i32` count of child sets. Member 3 holds 20 override sets with 148 child sets. In all 20 the leading child set is empty and the target is external. The child sets hold further override attributes, so the tree nests.

Of the 183 targets, 160 are external and 23 are node ids. A node id names a node of the world, so it joins the node link check of `FinishScene`.

### Version contexts older than their link (member 3)

With the overrides read, member 3 stops at `Fusion version context disagrees with its link`. `LinkSpy.py` shows 8 links. The document link of one of them names version 12. The design, ACT and Browser segments each hold a context for that link naming version 11 of the same lineage. All other 21 contexts name their link's version.

Rule: a version context can name an older version of its link's lineage. The URN must still match up to `?version=`, and its version must be lower. Every other corpus document passed the equality check before, so no other document has an older context.

### Mesh streams with stale tails (members 6 and 8)

`TailSpy.py` records the spans that the world reads from each stream.

| Member | Stream | Spans | Referenced bytes | Member bytes |
| --- | --- | --- | --- | --- |
| 6 | `stream_mesh_000` | 87 | 55,004 | 55,004 |
| 6 | `Fusion_mesh_000` | 293 | 64,048 | 128,096 |
| 8 | `stream_mesh_000` | 267 | 35,460 | 91,620 |
| 8 | `Fusion_mesh_000` | 121 | 57,680 | 706,104 |

In every stream the spans start at 0 and leave no gap. Only a tail after the last span is unreferenced. The tails hold `f32` vertex values, like the referenced data. They are what an earlier, longer save left behind when a later save rewrote the stream from offset 0. The Browser bulk stream of member 7 keeps stale records in the same way.

Rule: a mesh stream of either family can end with bytes that no world item references. Kit keeps them per stream in `GraphicScene.MeshSlack` and `GraphicScene.FusionSlack` and writes them back after the referenced spans. A gap between spans, or a stream with no span, still fails.

`TryCache.py` checks members 0, 3, 5, 6 and 8 of both copies. Each document round-trips, and the written `world` and stream members equal the saved bytes.

### Status of the members

| Member | Before | After |
| --- | --- | --- |
| 0 | Serializer header | Reads and round-trips |
| 3 | `OverrideTransformAttribute` | Reads and round-trips |
| 5 | `FProteinEffectAttribute` | Reads and round-trips |
| 6, 8 | Trailing mesh bytes | Read and round-trip |

## Sweeps

`Sweep.py <label> deep` ran on exported trees, with `SWEEP_SRC` set, so later edits did not leak into a run.

| Label | Tree | Files read | Documents read | Round trips | `NativeMaterial` pass, empty, fail |
| --- | --- | --- | --- | --- | --- |
| `base` | Read gap fixes (`ac04e964f`) | 1,698 of 1,709 | 1,704 of 1,725 | 1,698 of 1,704 | 1,656, 35, 13 |
| `packages` | Package writer | 1,698 of 1,709 | 1,704 of 1,725 | 1,700 of 1,704 | 1,656, 35, 13 |
| `cache` | Graphics rules | 1,698 of 1,709 | 1,714 of 1,725 | 1,710 of 1,714 | 1,666, 35, 13 |

`Compare.py base packages` shows only the 2 round trips of member 7. `Compare.py packages cache` shows 10 fixed documents, members 0, 3, 5, 6 and 8 in both copies, and no other change in read result, model, round trip or projection. All 18 bundle documents read and round-trip.

The 11 unread documents are outside this work: 5 Kit containers that Fusion rejected, 2 Form cache rewrites and 4 Form files whose patch words are doubles. The 4 failed round trips are the stale Form files. The 13 `NativeMaterial` failures are 11 undefined body materials and member 7 in both copies, which gives its bodies three physical assets.

## Status

Done. The package writer writes resource folders, and all five graphics members read and round-trip. The rules are in `Documentation/Changes/Fusion/Records/FusionCacheGaps.md` and its gotchas.
