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

The C# source compiled against the installed SOLIDWORKS 2026 interop declarations.
Windows PowerShell 5.1 parsed the launcher.
The collector has not run in SOLIDWORKS.
