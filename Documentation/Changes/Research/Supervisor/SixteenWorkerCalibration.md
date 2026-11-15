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
