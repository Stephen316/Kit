# Measure an offline decoder workload

Use this research tool with Python 3.14 or newer on Linux, macOS, or Windows 10 and newer. On Windows, use the repository's locked development environment for the Win32 dependency and use `python` as the interpreter command.

```sh
python3 re/automation/Calibration.py --manifest CalibrationManifest.json --output .rescratch/CalibrationRun
```

The output directory must not exist.
The tool creates private per-trial stores and does not attach to a live controller.
Use an immutable checkout and inputs for the entire run.
No native application, external model, arbitrary runner command, or grouped session is allowed.

## Manifest contract

The version-one JSON object has exactly these fields:

| Field                 | Required value                                                            |
| --------------------- | ------------------------------------------------------------------------- |
| `calibration_version` | Integer `1`                                                               |
| `kind`                | `decode.solidworks` or `decode.fusion`                                    |
| `pool`                | One controller pool label                                                 |
| `runner`              | `threads`, `initial_peak_memory_mib`, and `max_memory_mib`                |
| `bindings`            | Binding labels mapped to existing file `path`, `sha256`, and `size_bytes` |
| `resources`           | Resource labels mapped to their actual `capacity` and boolean `available` |
| `jobs`                | Eight through 256 explicit controller job specifications                  |
| `reserved_cpus`       | Positive integer reserve                                                  |
| `reserved_memory_mib` | Positive integer reserve                                                  |
| `max_seconds`         | Per-trial supervisor limit, five through 3600 seconds                     |

Each job uses the selected kind, exactly one `source` input binding, no dependencies, and only declared resources.
SOLIDWORKS options support `configuration`; Fusion options support boolean `allow_partial`.
The usual controller job deadlines, retry limits, versions, IDs, and resources are preserved.
Do not copy jobs from a production queue or remove their dependencies to make a calibration manifest.
Author a separate representative workload explicitly.

Each input is limited to 256 MiB. Declared input bindings total at most 512 MiB.
The manifest is limited to one MiB, and neutral serialization inside a worker is limited to 64 MiB.
The tool does not retain that neutral document as a conversion artifact; it retains its digest and counts for performance comparison.
The existing supervisor memory limit is sampled enforcement, not a new kernel memory or CPU quota.

This example creates a manifest from an existing research sample without inventing its digest:

```python
import hashlib
import json
import subprocess
from pathlib import Path

source = Path("re/solidworks/examples/.SLDPRT/example.SLDPRT").resolve()
content = source.read_bytes()
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
manifest = {
    "calibration_version": 1,
    "kind": "decode.solidworks",
    "pool": "offline",
    "runner": {"threads": 1, "initial_peak_memory_mib": 256, "max_memory_mib": 1024},
    "bindings": {"sample": {"path": str(source), "sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}},
    "resources": {},
    "reserved_cpus": 2,
    "reserved_memory_mib": 4096,
    "max_seconds": 300,
    "jobs": [
        {"id": f"calibration:part{index}", "kind": "decode.solidworks", "inputs": {"source": "sample"}, "rule_version": "offline-read@1", "tool_version": revision}
        for index in range(8)
    ],
}
with Path("CalibrationManifest.json").open("x", encoding="utf-8") as output:
    json.dump(manifest, output)
```

These eight deliberately listed jobs read the same sample.
Use representative inputs and enough work to obtain useful measurements.
A short or resource-constrained workload can produce no recommendation.
Keep the operator's actual resource reservations; do not lower them to force a higher step.

## Read the output

`Manifest.json` is a read-only canonical snapshot.
`Trial1`, `Trial2`, `Trial4`, and `Trial8` contain separate controller, artifact, and supervisor state when those steps are attempted.
Each `Prepared.json` records the actual controller maximum, pool, resources, and job fingerprints.
`RegistryContract.json` records single-job interpretation and the registry digest.
`Trial.json` contains worker intervals, physical CPU and RSS observations, throughput, measurement coverage, incomplete reasons, and source identities.
`Cleanup.json` records supervisor exit and private-session cleanup.
`Calibration.json` records the attempted steps, comparisons, stop reason, and optional measured recommendation.

Exit `0` means the requested sweep was attempted through all four steps.
It does not mean every trial was complete or that a recommendation exists.
Exit `2` records an interrupted or stopped sweep.
Exit `1` reports an invalid request or infrastructure failure; inspect the private output when one was created.
A failure report with `cleanup_verified=False` must not be treated as evidence that all owned processes stopped.

The one-second sustained-overlap threshold is an explicit concurrency policy.
It does not substitute for CPU utilization, held-out workload coverage, or target-application measurements.
Trial wall time includes supervisor and controller overhead but excludes store preparation and input copying.
Worker CPU observations cover that process through result preparation, excluding final result publication and interpreter exit. Decoder CPU and wall counters cover reader import, decode, model validation, and serialization.
RSS comes from supervisor process receipts and separately labeled sampled group measurements. On Windows, `worker_peak_working_set_bytes` measures the actual decoder interpreter through result preparation. The supervisor receipt may give the virtual environment launcher peak separately. The trial observer sums sampled worker working sets from its owned Job Object, excluding the supervisor launcher and interpreter. Samples can count shared pages more than once.
Intervals from actual worker measurements establish overlap; scheduler timestamps do not.

The run order is fixed at one, two, four, and eight.
Filesystem and bytecode caches, processor frequency, background work, and observer overhead can affect results.
The tool does not clear system caches or isolate the whole machine.
Package-version inventory and source hashes do not establish native application acceptance.
Review those conditions before using a local recommendation elsewhere.

See [offline decoder calibration](../../Changes/Research/Supervisor/OfflineDecoderCalibration.md) and [Windows offline calibration](../../Changes/Research/Supervisor/WindowsOfflineCalibration.md).
