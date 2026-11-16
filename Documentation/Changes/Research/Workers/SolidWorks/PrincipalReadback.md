# Licensed P01 and P03 readback comparison

The A08e principal readback reopened the fourteen independently authored SOLIDWORKS discovery captures in build `34.4.1.1011`. The read-only collector enumerated the saved profile, direct sketch and boss dimensions, native relation participants and solid body before and after rebuild. Both healthy controls passed, the pinned source bytes were verified after collection, and exit was observed for the process owned by the request.

## Reproduce the comparison

From a checkout containing the collector revision and the historical capture revision, use the copied A03 outputs and the dispatch SHA-256 recorded by the controller. The comparator reads the three documents in `readback/` or their flattened `readback.*.json` copies alongside `dispatch.json`.

```text
python re/automation/PrincipalReadbackEvidence.py <copied-output-directory> --dispatch-sha256 07f8dc5052aa5879b6e7d705f7abf941b08f50936e6086b4282fa2f15553fcfe
```

The comparator verifies the dispatch phase, request-bound native owner, plan, receipt and measured output hashes. It checks the launcher, collector, specification, control and all fourteen saved files against their exact Git blobs at the worker revision. Original P01 and P03 receipt and measurement pins resolve independently at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. The report keeps artifact hashes and native CAD identities. It omits host and process identifiers and workstation paths.

The current launcher compiles `P04Readback.cs` and `P02Readback.cs` together. For that variant the comparator checks the exact launcher digest and both compiled source pins against the committed files and the same readback plan. Earlier single-source receipts retain their existing field coverage. This check still requires the completed dispatch and its measured outputs.

| Artifact | SHA-256 or revision |
| --- | --- |
| Worker Git revision | `0d527bb9ec59f7728545cd6aacfa98eb5951549b` |
| Accepted A03 result | `389b6ab976b47c5f10f36e867844b65244d701526b4db993b524c60ffc00b230` |
| Native readback plan | `232de11fb7aabe2e9c3c53e112b7bc18dfec55e6c7f046598f76c32ddc04913b` |
| Native measurements | `a8c34ec713736cc7da5725e9910286b5541375cce4b59463d93565c8cf40eb5b` |
| Native readback receipt | `4ecb6df6818c6d3d194c326e0bb10ddfc7cdf0947f975a2749444eb44e249ffe` |
| Normalized comparison report | `49f1ce0ed13f2c0092d37bff80125ee0dc5072ffff630750648a8fda792980bf` |

## Evidence scope

All fourteen article records were identical before and after rebuild. The comparison checks both phases independently against the guarded archive walk and the original reopened native measurements. Across 28 observations it checks 112 directed world-perimeter edges, 112 axis relations, 56 attached sketch size displays, and 28 Origin coincidences. The collector read 196 current relation records with 280 current and 280 definition operand slots, plus 112 direct display attachment slots. Width and height were driving in both planes and in the saved inch-unit variant. Their ordered point bindings agree with both the saved dimension members and the observed distance relations.

For the Origin coincidence, the current relation exposes a point proxy owned by `RectangleSketch`. The definition exposes the actual `Origin` point on the first slot and the owned rectangle corner on the second. The two owning sketches can use the same native point ID for distinct operands.

The sixteen P03 phase observations include the selected profile, signed single-ended blind extent, driving depth display, one solid and its face, edge and vertex counts. Volume and center of mass agree with the original reopened native measurements. Fresh world bounds agree with the bounds derived from the original reopened section and the verified signed depth. P01 observes zero solid bodies.

The earlier collector at `e73200e83bf1456767595a8a92910fee5f21f9bc` used dispatch SHA-256 `93b7c41d1d58d4d2cd1fbb9b2a2175307734e1aef7cf22fd36d515b636f7ada3`. Its report carries the independent historical boss display role and leaves the fresh boss display field empty. The second collector directly measured both. Paired capture qualification still requires fresh Fusion evidence and the frozen-rule holdout. [Qualification and editable conversion steps](../../../../Reference/Research/AutomationSteps.md)
