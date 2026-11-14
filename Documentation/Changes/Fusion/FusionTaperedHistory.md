# Typed circular frustum BRep history

`BrepCodec.Frustum` adds a qualified reader and independent writer for the 35-record circular-frustum history profile. It recovers the semantic lower/upper radii, height and placement; body and topology identities; two-state insertion journal; provenance strings; and explicit cone/rim parameterization. It generates every record from those typed values without retaining source records, payload blocks, templates or a CAD runtime dependency.

```python
from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist

Parsed = ReadFrustumHist(HistoryBytes)
Rebuilt = EmitFrustumHist(
    Parsed.Model,
    Parsed.Identity,
    Parsed.TagSet,
    Parsed.History,
    Parsed.Stamp,
    Parsed.Frame,
)
Fresh = EmitFrustumHist(
    Parsed.Model,
    Parsed.Identity,
    Parsed.TagSet,
    Parsed.History,
    Parsed.Stamp,
)
```

The `Model` is the existing millimetre-based `FrustumBody`. Supplying `Frame` preserves source parameterization: exact centimetre geometry fields, signed sine/cosine and longitudinal scale, rim normal directions and seam points. The preserved source parameterization also includes cap frames, edge intervals, complementary coedge senses, and closed-edge vertex indices. Omitting `Frame` derives fresh geometry from the model with +Z rim carriers and vertex indices zero. The geometric locus can be identical while these two representations differ.

The reader requires ASM 23200 history headers, one closed three-face solid with two circular rims, positive height and radii, and +Z axial placement. The reader also requires circular unbounded carriers, forward cone sense and the qualified two-state insertion journal. The zero-angle cylinder limit is admitted. Typed parameter scale is positive and retained independently of the lower radius. Numeric consistency uses relative tolerance `1e-12` and absolute tolerance `1e-10` cm; stored values are retained rather than rewritten to fitted values.

Record count alone never selects this profile. Unknown fields, extra records, unsupported axes/trim forms, contradictory tags, invalid orientation, trailing bytes and archived history revisions reject explicitly. The separate Draft feature example has the same 35 initial record classes but additional delta states and old geometry, so it is rejected. There is no parser-error fallback that silently reclassifies unsupported inputs.

This addition does not change `DocumentCodec` or implement tapered feature authoring. A native file's Design parameter and its solved BRep must agree; preserving a BRep history alone does not establish complete parametric conversion. The [recovered tapered-history model](../../../re/Fusion/Reconstruction/TaperedHistory/TaperedHistoryModel.md) specifies those joins and the remaining document work. [Circular carrier orientation](../../Gotchas/Conversion/Fusion/Geometry/FusionCircularHistoryOrientation.md) explains why radii alone are insufficient for source reconstruction.

## Verification

Added remote ZIP/archive integration coverage for independent expanding, contracting and equal-radius histories and an explicit alternative parameter scale. The coverage also includes the native +7-degree control and +5-degree holdout, seven malformed typed-frame cases, three unsupported saved-journal profiles, and trailing bytes. Source cases retain the native −Z upper carrier, complementary coedge flags, vertex indices `(2,0)` and exact seam-point doubles through semantic read/reemit.

Black, Ruff, mypy, Pyright and the repository steering checker pass on the 36 scoped product/test files. Pyright also notes three existing unsupported configuration keys and reports no source errors or warnings. No local tests were run. Remote run [43237855649](https://github.com/TryUniCAD/Kit/actions/runs/43237855649) on revision `9f6753ce885eff64fdcc907361175ff65253fb6d` passed all 885 cases in 38.93 seconds, including all 17 new history cases. Standalone frustum geometry acceptance is recorded separately in [FusionFrustumGeometry](FusionFrustumGeometry.md).

Native-acceptance preparation produced four same-source document replacements through the production codec. The four replacements cover retained native upper-rim orientation, fresh independently generated orientation, retained orientation with scale 3.125 cm, and the separate five-degree holdout. [Preparation.json](../../../re/Fusion/LocalOracle/TaperedHistory/Preparation.json) binds every archive/history hash and expected measurement. Only the solved BRep part is rebuilt in those candidates; surrounding Design records remain from their respective source documents. Candidate generation itself is not native acceptance.

## Native acceptance

[Fusion 2706.1.17 accepted all four complete history replacements](../../../re/Fusion/LocalOracle/TaperedHistory/NativeAcceptance.json). Two replacements are the native +7-degree frame and a newly derived frame for the same shape. The other two replacements are an independently changed cone parameter scale of 3.125 cm and a +5-degree holdout. Each archive retains its own source Design and other non-history members; these are history acceptance fixtures, not independently authored complete documents.

The three +7-degree cases initially measure 6.533057920 cm³, area 19.616365019 cm² and centre Z 0.903393208 cm. The +5-degree holdout measures 7.993935456 cm³, area 22.208546817 cm² and centre Z 1.122599316 cm. All have three faces, two edges and two vertices. Native material density and mass remain valid.

Each case passed timeline rollback to its sketch, restoration, full rebuild and a driving height edit to 27 mm. Each case also passed a taper edit to −3 degrees, native save and reopen. The final contracting solid measures 7.338658556 cm³, area 21.242991401 cm² and centre Z 1.281608627 cm. All timeline features remain healthy and the acceptance run closes its documents.

[Preparation.json](../../../re/Fusion/LocalOracle/TaperedHistory/Preparation.json) binds source, emitted history and archive hashes to exact semantic inputs. The native report binds the same archive hashes and saved outputs to each measured stage. The changed scale case confirms that longitudinal parameter scale is independent of the physical base radius.
