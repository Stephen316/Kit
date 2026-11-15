# Requested sessions are not measured decoder concurrency

An eight-session pool limit does not prove that eight decoders ran at once.
CPU or memory reserves, counted resources, short jobs, controller setup, and scheduling can keep actual overlap lower.
Supervisor session timestamps also include setup and polling delays.
Using them as decoder intervals can fabricate a saturated trial.

The standalone calibration tool uses worker monotonic intervals and reports requested and observed concurrency separately.
It requires a declared one-second overlap plateau and complete comparable adjacent trials before recommending a previous measured step.
Resource-constrained trials stay incomplete.
The tool never removes resources, strips dependencies, clones queued jobs, or enables application or model work to fill a requested step.

Caches and background load remain measurement conditions to review.
A local throughput comparison is performance evidence only, not native reader qualification or editable conversion acceptance.
See [the operator guide](../../Reference/Research/OfflineCalibration.md).
