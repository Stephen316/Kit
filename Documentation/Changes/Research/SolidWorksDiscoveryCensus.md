# SOLIDWORKS discovery reader census

The **Workflow quality** job reads the 25 SOLIDWORKS captures for P01, P03 and P04. Each run uses the tested Git revision and checks its inputs against the recorded receipt and specification hashes. It reads each native blob through the existing research reader command and also inspects the SDK native model for that blob.

Download the `SolidworksDiscoveryCensus-<attempt>` artifact from the workflow run. The [reader guide](../../Reference/Research/SolidworksResearchReader.md#discovery-census) describes the report and its scope.

The report identifies which observations are missing from the native reader and where the neutral projection loses information already present in the native model. It records discovery evidence only. The historical reader check still uses its existing 58-part corpus. The qualification and holdout files are excluded.

The workflow YAML and Python 3.11 syntax were checked without executing the census. Its decoder and projection results require a completed remote workflow run.
