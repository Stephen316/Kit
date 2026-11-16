# Licensed through-all body scope control

The [scope specification](../../../../../re/automation/PairedCaptures/ScopeControl/ScopeControlSpec.json) defines two independent solids and one inward through-all cut. The cut starts on A's upper face, crosses a 5 mm gap, and intersects B without changing either solid's axis bounds. Automatic scope and explicit A+B can therefore agree on all measured geometry. Explicit A should preserve B.

The SOLIDWORKS author selects the sketch and, for each explicit case, appends the native body at the scope selection mark. Before and after save it reads the extrusion definition with selection access. The report keeps the native feature scope flag, automatic-selection flag, resolved scope body references, end condition and raw depth field. The normalized through-all extent has no finite depth. The observed affected bodies come from per-body volume changes. Each solid is identified by its native producer and checked against its specified bounds. [Multibody feature scope](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/Overview/Programming_Multibody_Parts.htm), [native per-body mass properties](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ibody2~getmassproperties.html)

The author clears inherited selections and selects the created sketch feature directly. The selection check retains exact counts and can compare the document's persistent references when SOLIDWORKS supplies distinct object wrappers. [Feature selection](https://help.solidworks.com/2022/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature~Select2.html), [Persistent object equality](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~IsSamePersistentID.html)

The automatic recipe uses the SOLIDWORKS All bodies policy. It passes `UseFeatScope=false` and requires the fresh definition to return a clear Feature Scope flag and an empty native selection list. The explicit recipes require enabled Feature Scope, both Auto-select readings clear, and the exact selected body references. Each route independently measures the affected bodies before save and after reopen. [Multibody API contract](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/Overview/Programming_Multibody_Parts.htm?id=1.4.39.1), [scope modes](../../../../Gotchas/Research/Workers/SolidWorksCutScopeModes.md)

Run the author and collector from an exact checkout on the licensed SOLIDWORKS `34.4.1.1011` Windows desktop with the application closed. Choose an unused output directory outside the checkout.

```powershell
powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/ScopeControl/RunSolidWorksScope.ps1 -OutputDirectory <private-directory> -SourceRevision <full-commit>
```

The launcher checks its own Git blob, the collector and the specification. It attaches to each directly launched process by PID and observes authoring exit before reopening the exact saved files read-only in a second process. The native archive hashes must agree after rebuild. A failed phase retains its revision, specification digest and native error category in `failure.json`. Keep the report and native archives together in private evidence storage. The discovery witnesses have separate provenance from the frozen P04 captures.

Startup cleanup verifies the original process handle before any forced exit. For a preserved or terminated process, consult the cleanup disposition in the failure record. [Scope collector startup cleanup](ScopeStartupCleanup.md)

Per-case checkpoints keep the measurements and source pins for each completed authoring or reopen case. When a case raises an exception, the failure record preserves the case, failing step, HRESULT, and message. [Scope case checkpoints](ScopeCaseCheckpoints.md)

A null explicit `FeatureCut4` result after verified selection permits one fresh-document retry through the editable feature definition. The original selection, intended policy, and retry route remain visible in the evidence. [Explicit Cut retry](ScopeExplicitFallback.md)

Use the standalone watchdog when the campaign needs a hard deadline across synchronous COM calls. It retains the original capture artifacts and the outer job-drain receipt. [Scope campaign watchdog](ScopeWatchdog.md)

## Observed checkpoint

Build `34.4.1.1011` authored and saved the automatic case in a provisional scratch run at `c996f65f1745aad9aa7a82f89537eeb2f14303ee`. The archive SHA-256 is `82141d768d1190bbc0193c0e30fdc06049a93ffdda88866b514c8d504213adfe`. The read-only replay follows two saved scope-body entries to distinct Boss producers. The initial explicit feature creation refused its input. A subsequent startup produced a SOLIDWORKS crash report before the process became available to COM. The explicit selections, persisted Auto-select and fresh three-case comparison remain unverified. [Archive replay](ProvisionalScopeArchive.md), [native comparison](CutScopeReadback.md)

The bounded run at `57f1b3ee` created the through-all Cut with the selected-bodies API route and measured volume loss in both bodies. The freshly retrieved definition listed both bodies and reported `AutoSelect=false` before and during selection access after the edit and rebuild. The acceptance check stopped that run before save. The watchdog confirmed the private job drained.
