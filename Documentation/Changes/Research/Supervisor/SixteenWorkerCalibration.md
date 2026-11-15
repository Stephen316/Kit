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

### Controlled claim timing

At `fca003a46fcb2def5a22c38942598ebd98cac99a`, two fresh Windows A03 stores used all 64 bindings and an installed owner fence. Sixteen paired claims confirmed matching FIFO selection, attempt and fingerprint. The stores refused a seventeenth claim and recovered the published claims through the supervisor's ordinary recovery path. The diagnostic launched no decoders.

The direct adapter call took a median 187.689 ms, including a 182.073 ms controller round trip. The instrumented path measured a 194.212 ms median round trip, with 11.587 ms of paired median adapter overhead. Parent invocation to the first child Python marker and controller source load/imports together took a paired median 134.391 ms, with a median share of 70.74% of the instrumented round trip. Argument processing took a median 26.670 ms. Combined ledger initialization, transaction opening, owner check, claim, publication and commit took a median 16.700 ms. The largest observed claim-file sync cost was 135.400 ms and the largest transaction exit was 144.080 ms. These component timings describe the isolated claim path on this host.

The private timing report SHA-256 is `d571aac7ba69b073399a3fc5e419800b33b404b9b72a62e8b488a0d7c849ecb2` and its source digest is `c4cd772472d9bb3f57fa55c0581593175bc53c146aea8433022fd4536d069238`. The parent instrumentation SHA-256 is `6083558aa1f230b4e69d8513e05103337aa608f2f653de462238cc507adeab96` and the child instrumentation SHA-256 is `b999657803a392f8d6700f8c933732c614a14c049e1c2997d8a86125bc579ffa`.

### Windows sweep with the warm claim helper

The `b323938d0645bcded260e206e5fe3d164aed2252` sweep used the same 64 archived inputs, manifest, Python version, and reserve settings. The decoder, locked dependencies, calibration metrics and Windows resource observer were unchanged between source revisions. The built-in Windows supervisor used its [warm claim helper](WindowsWarmClaim.md) in all five trials.

| Requested workers | Decodes per minute | Peak simultaneous decodes | Longest requested overlap in seconds |
| ---: | ---: | ---: | ---: |
| 1 | 17.79 | 1 | 6.648 |
| 2 | 33.28 | 2 | 3.020 |
| 4 | 48.58 | 4 | 3.832 |
| 8 | 64.48 | 8 | 4.442 |
| 16 | 77.51 | 16 | 5.681 |

All 320 jobs completed once. All trials produced the same decoded-output digest as before, with complete CPU and working-set telemetry and clean supervisor, claim, session and Job Object shutdown receipts. The sixteen-worker trial observed at least 13,933,875,200 bytes of host memory available and a peak sampled aggregate working set of 1,139,089,408 bytes.

All four adjacent comparisons meet the overlap and telemetry rules. Gains are 87.11%, 45.97%, 32.73%, and 20.20%. The sweep completed without a plateau or recommendation. Absolute throughput at four, eight, and sixteen workers was lower than the preceding run. The elapsed-rate comparison remains descriptive across the two source revisions. [Isolated Windows claim latency](WindowsWarmClaim.md)

The output digest is `32a804539e3f50992b21f4ed576fb45979dd778696aea399761e3649d409f865`. The warm calibration source digest is `f29da3ed89020a9e096a81b496243f98a2742d533b63344e43bc642af1570335`, and the private report SHA-256 is `8f117d25b59642473d529167957e68fe4f390c5856592a6a7dbc976c931a895d`.
