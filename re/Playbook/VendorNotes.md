# Vendor notes

Where each format stands in Kit, where its findings live, and what is distinctive about it. Read the
vendor's own findings before starting; never re-derive a solved layer. Container facts below that are
not backed by Kit findings are starting hypotheses: confirm them on your samples in phase A.

---

## SOLIDWORKS (`.SLDPRT`, `.SLDASM`, `.SLDDRW`)

**State:** the most advanced study. Container framing, archive grammar, object segmentation and map
renumbering are cracked. The load-critical streams for Kit's supported feature families are emitted
from typed fields with zero opaque bytes. Arbitrary feature histories are not yet inverted; unsupported
inputs are rejected. The current boundary is in `re/solidworks/README.md` and
`re/solidworks/CorpusCoverage.md`.

**Read first:** `re/solidworks/README.md` (in its stated order), `re/solidworks/records/Definition.md`
(the end-to-end method for one stream), `re/solidworks/measurements/Measure.md` (load-critical
streams by deletion), `re/tooling/ghidra/Setup.md`.

**Distinctive facts:**

- ZIP-like container shifted by 8 bytes, with replaced magics and nibble-swapped stream names.
- A per-file signature triplet looked up from a 1000-entry table in `sldmfcu.dll`.
- The archive is the vendor's own `su_CArchive`, not MFC's `CArchive`; hooking MFC gives zero hits.
- Serializers are vtable slot 5; 2607 classes indexed in `re/data/Serialization/SerializeMap.json`.
- The Parasolid geometry cache can be deleted; the app rebuilds geometry from history.
- Missing revolve angle = 2π default from the accessor.
- Real-world corpus is localised (Spanish) and uses NFD filenames.

**Oracle:** COM API through `re/tooling/harness/`, runtime traces through `re/tooling/windbg/`.

**Open work:** feature families and sketch profiles not yet in `CorpusCoverage.md`, assemblies beyond
the typed core, drawings. Use [ShapeCatalog.md](ShapeCatalog.md) tiers 2–6 to drive them.

---

## Fusion (`.f3d`, `.f3z`)

**State:** a research decoder and capture tooling in `re/Fusion/`, and a native reader and
independent writer in `src/convert/formats/Fusion/` for qualified features. The data model is
consolidated in `Documentation/Reference/Research/FusionDataModel.md`.

**Read first:** `re/Fusion/README.md` (feature index), `re/Fusion/Notes/Workflow.md`,
`Documentation/Reference/Research/FusionDonorBan.md`, `FusionOracleCommands.md`,
`FusionAcceptanceEvidence.md`.

**Distinctive facts:**

- ZIP container; members can use ZIP method 93 (Zstandard). Python 3.13's `zipfile` cannot
  decompress method 93; use a Python with Zstandard support. Read
  `Documentation/Gotchas/Conversion/Fusion/FusionArchiveInspection.md` and
  `Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingZstdFrames.md`.
- Internal units are centimetres.
- Scripts run inside Fusion through an internal command bridge reached over a local Chromium
  debugging transport (documented in `FusionOracleCommands.md`); not a supported public API.
- `Application.executeTextCommand` exposes internal entity ids and properties (`PAsset.EntityIds`,
  `PEntity.Properties`), which show the internal object graph directly.
- Front-end panels are Chromium; REA's Electron/JavaScript tools apply to the shipped bundles.

**Oracle:** `re/Fusion/LocalOracle/` capture and accept scripts.

**Open work:** feature families listed as open in `re/Fusion/README.md`; drawings and assemblies
beyond the qualified scope.

---

## CATIA V5 (`.CATPart`, `.CATProduct`, `.CATDrawing`)

**State:** Kit has a container reader/writer for `V5_CFV2` and recognises native stream markers;
native feature decoding is limited. See `Documentation/Reference/Adapters/Catia.md` and
`src/convert/adapters/catia/Container.py`.

**Distinctive facts:**

- The container magic is `V5_CFV2\0`, with `CATIA_V5 CB0001` folder markers. It is **not** a CFBF
  (OLE2) file; do not open it with `olefile` and conclude it is corrupt.
- Streams such as `1000_00000002_2` (part data), `Format`, `CATSummaryInformation`, and markers
  `OSMX`, `CGM`, `MFBRP` (geometry), `CGR` (tessellation).
- Geometry is CGM (Dassault's kernel), not Parasolid or ACIS.
- Products reference parts by sibling path; keep `.CATPart` and `.CATProduct` sample directories as
  siblings (`re/catia/examples/`).

**Oracle:** COM Automation; macro recording for unfamiliar features.

**Open work:** almost everything above the container: the `OSMX` object graph, feature records,
knowledgeware parameters and relations.

---

## Inventor (`.ipt`, `.iam`, `.idw`, `.dwg`)

No Kit study yet. Inventor documents are commonly reported to be OLE2/CFBF storages; confirm with the
`D0 CF 11 E0` magic and `olefile`. Geometry is ASM (Autodesk's ACIS derivative); look for
`ASM BinaryFile` markers. Oracle: COM/.NET API. Start with phase A §2 and a stream census.

## Solid Edge (`.par`, `.psm`, `.asm`, `.dft`)

No Kit study yet. Commonly reported as OLE2/CFBF storages with embedded Parasolid. Oracle: COM API.
The Parasolid partition can be cross-checked against `.x_t` exports.

## NX (`.prt`)

No Kit study yet. Parasolid-based geometry with proprietary feature history. NXOpen journals are the
best recorder of any vendor and make phase C fast. Expect the same split SOLIDWORKS showed: history
matters, the geometry cache may be regenerable.

## Creo / Pro/ENGINEER (`.prt`, `.asm`, `.drw`)

No Kit study yet. Files often begin with a readable `#UGC:` header line followed by sections; confirm
on samples. Oracle: J-Link/OTK; trail files record UI sessions. Expect an object store very unlike
MFC serialisation.

## AutoCAD (`.dwg`)

No Kit study yet. DWG has extensive public documentation from the Open Design Alliance and an
open-source reader (LibreDWG). Invert the phase order: read the published specification first, then
trace only the gaps (newer versions, proprietary object classes). Always pair DWG with `DXFOUT` of
the same drawing.

## Rhino (`.3dm`)

No Kit study yet. openNURBS is the open-source reference implementation: read the source instead of
reverse engineering. Useful as a worked example of how a CAD format serialises NURBS.

## FreeCAD (`.FCStd`)

Open: a ZIP with `Document.xml`, `GuiDocument.xml` and OCCT `.brp` B-rep files. Kit reads it
(`Documentation/Reference/Adapters/Freecad.md`) and uses FreeCAD as a corpus generator. Source code is
the specification.

## Neutral formats as cross-checks

STEP (AP203/AP214/AP242), IGES, Parasolid `.x_t`, ACIS `.sat`, JT, 3MF and IFC are documented. Export
them from the vendor app for every corpus sample and measure them with OCCT or another open kernel as
an independent check of the vendor's own mass properties.
