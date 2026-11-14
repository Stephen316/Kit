# SOLIDWORKS discovery reader census

The **Workflow quality** job reads the 25 SOLIDWORKS captures for P01, P03 and P04. Each run uses the tested Git revision and checks its inputs against the recorded receipt and specification hashes. It reads each native blob through the existing research reader command and also inspects the SDK native model for that blob.

Download the `SolidworksDiscoveryCensus-<attempt>` artifact from the workflow run. The [reader guide](../../Reference/Research/SolidworksResearchReader.md#discovery-census) describes the report and its scope.

The report identifies which observations are missing from the native reader and where the neutral projection loses information already present in the native model. It records discovery evidence only. The historical reader check still uses its existing 58-part corpus. The qualification and holdout files are excluded.

On PR head `af8257e5`, GitHub checked out merge revision `b1829aca` and decoded all 25 files at both the native and neutral boundaries. Its report recorded 561 matched, 149 different and 37 unobserved comparisons. P03 lost the decoded boss reverse flag at projection. P04 retained the formula text but omitted the dimension references from the neutral equations. The census also found incomplete sketch geometry, face support, depthless cut termination and native display-unit evidence. [Remote census job and artifact](https://github.com/TryUniCAD/Kit/actions/runs/43641328892)
