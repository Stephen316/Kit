# SOLIDWORKS P04 supporting-face readback

## Behavior

The [P04 collector](../../../../re/automation/PairedCaptures/SolidWorksAuthoring/P04Readback.cs) opens read-only scratch copies of the eleven recorded SOLIDWORKS P04 parts.
It measures the pinned control before and after the batch.
The original [authoring harness](../../../Reference/Research/SolidWorksCaptureAuthoring.md), captures and receipts retain their recorded bytes.

The collector asks the cut sketch for its native support face.
It compares the face's oldest owning feature with the document's boss through the SOLIDWORKS object equality API.
It resolves the face's persistent reference to the same face before and after rebuild.
After rebuild it also resolves the reference recorded before rebuild.
Each observation records native return codes, face normal and area. [Native face ownership](https://help.solidworks.com/2019/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFace2~GetFeature.html) · [Persistent reference IDs](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Overview/Persistent_Reference_IDs.htm?id=1.4.45)

The sketch observations record point and segment IDs, dimension annotation attachments and relation definition entities.
Each point or segment records whether the native object belongs to the observed sketch.
An identifier applies within its sketch, entity type and observation.
Null or unsupported attachments and API diagnostics remain visible. [Sketch point identity](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISketchPoint~GetID.html) · [Attachment type reporting](https://help.solidworks.com/2023/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IAnnotation~GetAttachedEntityTypes.html) · [Relation definition entities](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISketchRelation~GetDefinitionEntities2.html)

## Usage

Use a dedicated Windows desktop session with licensed SOLIDWORKS 2026 build `34.4.1.1011`.
Close SOLIDWORKS before the run.
Use a complete checkout of the reviewed Git revision.
Choose a new output directory under an existing private parent outside the checkout.
Point `InteropAssembly` to the matching library in the registered SOLIDWORKS installation.

```powershell
powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1 -OutputDirectory 'C:/CadResearch/P04Readback01' -InteropAssembly 'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS (3)/api/redist/SolidWorks.Interop.sldworks.dll'
```

The launcher binds the original files and collector to the committed Git revision.
It verifies the scratch hashes before opening and verifies both the original and scratch hashes after readback.
The collector starts SOLIDWORKS and requests normal exit from the empty session it owns.

Keep `plan.json`, `measurements.json` and `receipt.json` together in private storage. SOLIDWORKS persistent references can contain the absolute path of the opened file.
An `observed` receipt means all eleven parts were read and their supporting faces passed the native checks.
Review unresolved dimension or relation slots before making a binding claim.
An incomplete receipt or a missing receipt requires diagnosis before reuse.
Use a new output directory for another run.

## Limits and verification

The collector observes P04 only.
Its persistent reference checks apply to the exact opened part in this SOLIDWORKS build.
Source readback does not identify the file stream or offset used to encode that relation.
The collector provides supplemental observations for adjudication under A02d.

On November 15, 2026, the collector at `701582eb` read all eleven P04 captures in a fresh SOLIDWORKS process at build `34.4.1.1011`. The control passed before and after the batch. The run verified the original and scratch file hashes and confirmed that the owned application exited.

Each cut sketch identifies a face on the unsuppressed `BlindBoss`. The native equality check and the persistent reference round trips identify the same support before and after rebuild. The world normal is `(0, 0, 1)` for ten captures and `(1, 0, 0)` for the YZ variant. The cut sketch transform records a local depth translation of −10 mm except for the 12 mm boss edit, which records −12 mm. The YZ sketch has a different rotation from the XY cases. The checks also passed on the through-all save.

The repeat at `4d645329` also recorded five other faces on the boss for each observation. Each of the 110 control references resolved to its own distinct face. In all 22 observations, the 52-byte span after the `moFaceRef_c` name matched both the cut sketch's supporting face and the opposite cap. It matched none of the 88 side faces. This span helps locate a cap reference but cannot establish the support occurrence. [Archive correlation](../../../../re/solidworks/records/P04SketchResidence.md#face-reference-control)

Each pass records 66 dimension owners and 132 point attachments. The two offset dimensions in each cut sketch each have one native point outside that sketch. The run also records 165 relations with 242 definition participants per pass. Of those, 33 are points outside the corresponding sketch.

The verified receipt SHA-256 is `bc361d29558338240fce751f3d84bc5a691aeef1b8937ecc993e95caac436489`. Its measurements hash is `55ded2d7e511861cdd41100bfdd1dfc17307b3a31ad8c01ceec1defb66d00305`. The raw references are kept with the private run. This evidence supplies a native observation for the SOLIDWORKS side of P04. Paired qualification also needs independent Fusion readback and observation binding.

The repeat receipt SHA-256 is `e9b4966838beb30f078d5b902177d0b80fa07731ca5402f87590d69d1d4f01ce`. Its measurements hash is `b0abfb17f2365d2b6290593b7bfd6782e14d64c92b5993c521c2d11a530afeb4`.

The repeat at `b92027a7` checks each point's native sketch against three measured owners using SOLIDWORKS object equality. All eleven parts yield an `OriginProfileFeature` named `Origin`, feature ID 5, with one point of ID `[0, 1]`. Before and after rebuild this feature owns all 44 foreign offset-dimension attachments and all 66 foreign relation definition participants. The relation participants cover the two cut offset relations and the rectangle's coincidence in each part. The [offline sketch report](../Readers/SolidWorksSketchGeometry.md) separately verifies the local solver operands and their point incidence counts. The private receipt SHA-256 is `3f9e5f6ee3022d2d976291c796516ab045abd2d15a7acbf81479d2970dd8e502`. Its measurements hash is `92230cc5a9cef3d56a39fc75b3e53a93bb6135956466f3dfe834e73de562d4d2`.
