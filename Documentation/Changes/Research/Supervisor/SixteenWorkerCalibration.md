# Sixteen-worker offline calibration

Pass `--max-concurrency 16` to append a sixteen-worker trial to the fixed offline calibration sweep. The default remains one, two, four and eight workers. The report's `requested_steps` records the actual schedule and a successful extended sweep writes a private `Trial16` directory. [Offline calibration guide](../../../Reference/Research/OfflineCalibration.md)

The extension reuses the immutable manifest, resource policy, one-second overlap requirement and ten-percent throughput plateau rule. The eight- and sixteen-worker trials are comparable only when both complete with the same output digest, source and environment identity, and required telemetry. Headroom or a short workload can leave the final trial incomplete.

The remote process cases cover the unchanged default schedule and the extended schedule with an exhausted CPU reserve. The extended case verifies a private sixteen-worker trial, admission refusal and the absent recommendation. Remote execution of those cases is pending.
