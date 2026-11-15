# Sixteen-worker offline calibration

Pass `--max-concurrency 16` to append a sixteen-worker trial to the fixed offline calibration sweep. The default remains one, two, four and eight workers. The report's `requested_steps` records the actual schedule and a successful extended sweep writes a private `Trial16` directory. [Offline calibration guide](../../../Reference/Research/OfflineCalibration.md)

The extension reuses the immutable manifest, resource policy, one-second overlap requirement and ten-percent throughput plateau rule. The eight- and sixteen-worker trials are comparable only when both complete with the same output digest, source and environment identity, and required telemetry. Headroom or a short workload can leave the final trial incomplete.

The remote process cases cover the unchanged default schedule and the extended schedule with an exhausted CPU reserve. The extended case verifies a private sixteen-worker trial, admission refusal and the absent recommendation. Remote execution of those cases is pending.

## Windows observation

At `ddac1a709134cdd5e997c31bf658dfd6ec8c0507`, the extended schedule used the same 32 historical Fusion discovery archives and byte-identical manifest as the earlier [Windows staging comparison](WindowsArtifactStaging.md). The run used one thread per job and retained two CPUs and 4 GiB. All 160 jobs completed once with identical decoded-output digests and full CPU and working-set telemetry. All five trials verified clean exits and empty controller claims, supervisor sessions and Windows Job Objects.

| Requested workers | Decodes per minute | Peak simultaneous decodes | Requested overlap in seconds |
| ---: | ---: | ---: | ---: |
| 1 | 17.02 | 1 | 5.657 |
| 2 | 33.39 | 2 | 2.674 |
| 4 | 49.87 | 4 | 2.827 |
| 8 | 64.82 | 8 | 2.174 |
| 16 | 85.05 | 15 | 0 |

The first four steps met the comparison criteria. The sixteen-worker trial held sixteen active supervisor sessions and reached fifteen simultaneous decoders. The first sixteen starts span 4.747 seconds at the supervisor boundary and 4.875 seconds at the decoder boundary. The earliest of those decodes ended 0.103 seconds before the last began. Available host memory stayed above 13.84 GiB. The eight-to-sixteen comparison is noncomparable under the existing overlap rule, and the sweep produced no recommendation.

The canonical manifest SHA-256 is `a86e1ecfa76b5ce8c9a5698dd0e034378644105695b6c594bc8369ba00591620`, the calibration source digest is `db0baf03c08e4510a4fa0f771cd5ad7c762267387626a998012b20aef2fe3e36`, and the private report SHA-256 is `89be0ca005599a5e9c73ea9ce124ff8a1478d8b0737b1a6c665faca7d7fd4460`.

## Larger Windows discovery observation

The follow-up at `5770f1b322688e55237172d7a6d57c983f334ce0` used 64 distinct historical Fusion study archives across 38 folders, with 53 additions relative to the earlier 32-archive cohort. The fixed-reader census recorded a successful strict or partial decode for every selected archive. The current and historical Git trees agree on every selected blob. The cohort excludes all paired captures and known nondiscovery and held study families, including exact-byte aliases. It ranks eligible inputs by uncompressed active Design stream size, archive size, then Git path, with at most three inputs per study folder. The bindings total 9,670,016 bytes. [Earlier historical selection](WindowsOfflineCalibration.md#larger-historical-fusion-discovery-sweep)

The same five-step sweep ran on Windows with Python 3.14.6 and pywin32 312. All trials observed 20 affinity-visible logical CPUs. The runner used one thread, a 256 MiB initial admission estimate, a 1 GiB sampled worker limit and a 120-second job deadline. The host reserve remained two CPUs and 4 GiB. The per-trial deadline was 720 seconds for the larger cohort. [Offline calibration criteria](../../../Reference/Research/OfflineCalibration.md)

| Requested workers | Decodes per minute | Peak active supervisor sessions | Peak simultaneous decodes | Longest requested overlap in seconds |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 17.51 | 1 | 1 | 5.794 |
| 2 | 31.98 | 2 | 2 | 4.086 |
| 4 | 56.46 | 4 | 4 | 2.562 |
| 8 | 75.35 | 8 | 8 | 2.326 |
| 16 | 91.42 | 16 | 16 | 0.0885844 |

All 320 jobs completed once with complete CPU and working-set telemetry. The output digest `32a804539e3f50992b21f4ed576fb45979dd778696aea399761e3649d409f865` matched across all five trials. Every cleanup receipt verified a normal supervisor exit and empty claims, sessions and Job Objects. The sixteen-worker trial observed at least 14,080,610,304 bytes of available host memory and a peak sampled aggregate working set of 828,264,448 bytes.

The comparable throughput gains were 82.65%, 76.55% and 33.46% through eight workers. The sixteen-worker run reached the requested peak for 0.0885844 seconds against the existing one-second requirement. The eight-to-sixteen comparison remains noncomparable. The sweep ended without a throughput plateau or recommendation.

The first sixteen supervisor starts spanned 4.156 seconds and their matching decoder starts spanned 4.295 seconds. Across the fifteen dispatch gaps, 3.329 seconds elapsed from the previous supervisor start to the next claim event, 0.460 seconds from that event to session construction, 0.209 seconds from construction to worker launcher creation, and 0.158 seconds from creation to the start report. The controller event timestamps came from a read-only SQLite audit with identical before and after database digests. The pre-construction interval includes admission checks, controller invocation, SQLite work, claim publication and return. Individual timings for those operations remain open.

The canonical manifest SHA-256 is `fb7c3b15b789fcc1166e3735a6859b5c7271c391c1190a3955ffb4cc53b93c07`. The raw input manifest SHA-256 is `0cfda38eba5ffec23c89a1e17c486d48c819abd6d7bb0f2841a79373f1943868` and the raw provenance SHA-256 is `c302055be4d78664300252dc2d7e01856e5e7102717d266d50aa84e21ed91af6`. The calibration source digest is `352b0d8186c656eb03087d4a8bc32ba133e59e8bf4284e97f98993f3ba4080d7` and the private report SHA-256 is `31a0f26e5cd224bd61b021445ee3507df28be72dc819ca930fc79eb5396e0c91`.
