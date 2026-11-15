# Capture a face-supported SOLIDWORKS two-pad grid

The historical [two-pad experiments](../../../../re/solidworks/corpus/CorpusTwo.md#54-twopad--second-pad-depth-3--5--8-mm-face-supported) establish an editable native reference design. The corpus index has no hash-bound copy of those original native files. This capture creates fresh controls through the licensed SOLIDWORKS API for the A09 codec investigation.

The lower pad is 40 × 20 mm and the upper pad is 10 × 10 mm. The upper sketch selects the lower boss's native top face. The grid contains two independently authored 10 mm + 5 mm baselines, upper depths of 3 and 8 mm, and a base depth of 11 mm. The upper boss merges into one solid.

Run this from the pinned checkout with SOLIDWORKS stopped and an unused private output directory outside the repository.

```powershell
powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/SolidWorksAuthoring/RunTwoPad.ps1 -OutputDirectory PATH -SourceRevision FULL_GIT_SHA
```

The collector measures healthy controls around both phases. It records saved hashes, the live feature tree and driving dimensions, the upper sketch's resolved supporting face, body topology, volume and centroid. It compares volume and center to the independent stacked-prism formula. In the fresh reopen process it edits the upper depth, edits the base depth so the supporting face moves, and restores both. The original save hashes must stay unchanged. [SOLIDWORKS extrusion API](https://help.solidworks.com/2024/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~FeatureExtrusion2.html)

The capture provides discovery inputs and preserves the measured application scope. Reproducing the complete two-pad part without donor data, and validating the generated part in the licensed application, are separate requirements.
