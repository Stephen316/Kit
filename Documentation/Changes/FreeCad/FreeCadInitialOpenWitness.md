# Initial geometry on three FreeCAD rectangle controls

The source owner reports a fresh installed FreeCAD 1.1.4 witness at source `161885d8ec4442ddc2558a740fd2cd153a6c0819`, tree `972ce0b28532b4877505e7a4ec695472acb6c9e3`.
Three independently authored 37 × 21 mm rectangle packages opened without repair or stderr, each exposing one valid editable solid before any explicit recompute.
Each measured 12,432 mm³ with XY centroid (18.5, 10.5) mm.
[Operator report](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931310116)

| Control   | Initial Z bounds in mm | Initial Z centroid in mm |
| --------- | ---------------------- | ------------------------ |
| Forward   | [−5, 11]               | 3                        |
| Reversed  | [−11, 5]               | −3                       |
| Symmetric | [−8, 8]                | 0                        |

Each first-open feature was `Touched` while already exposing valid geometry.
Explicit recompute settled each to `Up-to-date`.
The operator corrected an audit that had reused a post-rebuild status assertion at initial open; geometry and state are now recorded separately.
This does not relax post-rebuild checks or qualify arbitrary touched features.
See the [initial-state gotcha](../../Gotchas/Conversion/FreeCad/InitialOpenTouchedState.md).

Independent 11→14 mm and 5→8 mm sheet edits moved their respective caps, preserved the other length and measured 14,763 mm³.
Symmetric total thickness 16→20 mm moved both caps and measured 15,540 mm³.
Restoration, save to distinct paths and a second fresh process reopened all three at original dimensions and geometry with the same driving expressions.
Four independent box controls and six separate native extrusion controls passed.
The two processes exited without open documents; the isolated slot was released.

| Evidence          | SHA-256                                                            |
| ----------------- | ------------------------------------------------------------------ |
| Preparation       | `9e53c1fc636fede8deb893886a20f38e6142903f230f073e50f6ec56230336ec` |
| Verified report   | `5fceb2b77d38919f8dfb588a44f25f28f9ed4aa4f4c476f07d4556d7a2d19f3e` |
| Edit receipt      | `ea0547d6a2e72290cf937f519ecebd1a43ce726a9696221661e42238d4b68111` |
| Reopen receipt    | `b3206b0182c5b63babaac594f9bec08399ee5303f7c78194f77534ef3c75132d` |
| Collector         | `4137251461f36fa3d98d69360269ac3e96b2f3c2723e6a7f0255f47979a6f839` |
| Measurement audit | `0235da52d71e3165b057e35a030203ea14b5cb17eb558258e8a66b6e4f5803eb` |

Raw candidates and receipts remain in private operator custody.
This records the initial-open measurement for these three rectangular controls at that exact source.
The [uncached earlier witness](FreeCadEndNativeWitness.md) remains an accurate C5 failure for `b32222b5`.
Other profiles, frames, units, Boolean results, retained routes and broader A16/A13/A15 qualification remain unfinished.

Strict emission refused with zero bytes.
Research emission used explicit `AllowCarrier=True` and kept both result and metadata usability/loadability flags false throughout.
No product attestation or public admission is promoted by this documentation.
The separate [hosted helper collection repair](FreeCadProcessHelperCollection.md) retains its own verification boundary.
Recording this operator evidence performed no local native, SDK, generator, test or collection execution.
