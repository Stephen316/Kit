# Generation 19000 sketch display fields

Native editable authoring remains open. The matching installed binary and six P01 discovery archives establish an inline default visual record and the modern standard-width encoding. The experiment reconstructs 60 visual records, 60 width fields and six constructor-state triples. It emits no candidate part.

Run `python re/solidworks/authoring/SketchStyleFields.py` from the checkout. The report has SHA-256 `a6f43b9c775be4ed0414db6d0cb9f48bba11b5b2eac5480b487534174cfec1c7` before the terminal newline. It uses the [same native files and measurement pins](RectangleFields.md) and carries source and resolved SHA-256 digests for each observation.

## Visual record

The SOLIDWORKS `34.4.1.1011` PE hashes match the [recorded loader image pins](../records/P04ArchiveWalk.md#inputs). RTTI at the constructor's vtable RVA `sldmodu+0x2060f10` identifies `sg2DEnt`. The static paths below follow actual stores in these exact images. Prior native dynamic recordings exercised loading.

| Field | Constructive source | Store write |
| --- | --- | --- |
| Layer short | The `sg2DEnt` constructors at `sldmodu+0x129f190` and `+0x129f380` pass −1 to `moEntVisProp_c` at `+0x129f27a` and `+0x129f450`. The layer-qualified getters return false for that sentinel. | `sldmodu+0x100ef6f` |
| By-layer mask short | Both constructors pass the all-by-layer mask. The exported `setFlagAllByLayer` uses the same `0x1f` value. | `sldmodu+0x100ef7c` |
| Constructor-state byte | `moEntVisProp_c` initializes the field at `this+4` to 3 at `sldmodu+0x100ecd5`. The matching modern load path reads it after the shorts. | `sldmodu+0x100ef89` |
| Color dword and style short | The constructors pass unset color and style to the nested `moVisProp_c`. Its `getColor` path masks the color to 24 bits only when a layer is present. | `sldmodu+0x100f04c`, `+0x100f059` |
| Line weight short and custom-width single | The constructors pass `swLW_NONE` to `utLineWidth_c`. Its enum constructor writes the supplied weight and the −1.0 custom-width sentinel. | `sldmfcu+0x12a71e`, `+0x12a72b` |

The 17-byte record matches all 60 members, including the distinct Origin proxy and structural line. The rule covers the observed default constructor path. A layer override and custom width need separate evidence.

## Explicit display state and standard weight

The ordinary noncompact member branch writes the DB keys `Color`, `ConstraintStatus` and `LineType` through three u16s from `this+0x30/+0x34/+0x38`, then calls `utLineWidth_c::Serialize` at `sldmodu+0x1441977`. The modern load path takes the matching branch and call at `+0x1441e24`. The store skips the extension when the compact selection at `+0x14417f5` is true. The selection uses a virtual query on the sketch's owner model at `+0x12a045c`. The six controls all take the explicit branch.

The installed SDK's `swLineWeights_e` defines `NONE=-1`, `THIN=0` and `NORMAL=1`. Its assembly SHA-256 is `b15e28ed5b2e8332d409ca79635f933a60e8cc0d9bd5ec980e2a2301220e7741`. The writer fragment takes the standard weight as an explicit style input and derives its float from the native constructor. Width choices in this P01 comparison are thin for corners, Origin proxy and the structural member, and normal for perimeter members. Those requested choices reproduce all 60 saved widths. Only the thin choice is the `sg2DEnt` constructor default. The source of the authored perimeter's later normal choice still needs a trace.

The structural member retains the constructor's `Color/ConstraintStatus/LineType` triple `(5,1,1)`. It is generated for the six structural rows. The physical members and Origin proxy store `(4,2,1)` in all six archives. The sketch-wide API constraint status is 3 and the members retain their separate native code. The [local corner writer](../WriterResearch/RectangleCorners.md) now uses the native constraint-color mapping with an explicit member status. An independent underconstrained and fully defined pair would establish when to select the member status.

The local corner writer also covers graph-derived `sgLineHandle` allocation on the ordinary branch. The other members still need their compact selection and external reference rules. Full native acceptance requires the rest of the load-critical records, followed by fresh open, rebuild, edit and save/reopen under the repository's acceptance procedure.
