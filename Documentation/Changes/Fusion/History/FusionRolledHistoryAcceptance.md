# Native acceptance of reconstructed rolled-back history

The corrected current/maximum state fields allow the complete history codec to reconstruct the corpus's rolled-back cylinder. Its journal retains current state 3, maximum allocated state 10, initial delta state 2 and next entity tag 6. The zero-angle circular carrier is represented by the qualified frustum model.

The [prepared archive](../../../../re/Fusion/LocalOracle/RolledHistory/Preparation.json) reconstructs its entire 5,300-byte `.smbh` member through `ReadFrustumHist` and `EmitFrustumHist`. All other members belong to that same source archive. The emitted archive SHA-256 is `3fe405fabad823a99cbf932e65aa63dac5d7567f792eb7041e876961a26f7bc0`.

Fusion 2706.1.17 opened both the original and reconstructed documents. The [native comparison report](../../../../re/Fusion/LocalOracle/RolledHistory/NativeAcceptance.json) records equal parameter expressions, timeline entries and health, marker positions, body names, topology counts, volumes, areas and bounds at every stage:

1. Initial marker 2, one radius-10 mm, height-10 mm cylinder with volume π cm³.
2. Rollback to marker 1, leaving the sketch and no solid.
3. Restoration to marker 2 and recomputation.
4. Move to the timeline end, regenerating all three bodies at heights 10, 20 and 30 mm.
5. Edit `d1` to 13 mm, producing first-body volume `4.084070449666906` cm³ while preserving the other two bodies.
6. Native save, reopen and rebuild, preserving the edited result.

The report SHA-256 is `f69f5f399b81ea173274ee765fd0817fe7577141c9f31556d03ddef2cf9400be`; acceptance left zero documents open. Geometry comparisons use relative tolerance `1e-8` and absolute tolerance `1e-9`. Non-geometric state matches exactly. The timeline group reports unknown health and no entity; future features initially report rolled-back health, then become healthy when restored. Those source-control states are retained rather than mislabeled as failures.

Remote run [43244128179](https://github.com/TryUniCAD/Kit/actions/runs/43244128179) passed 925 of 926 cases, including all six new state-field cases. Its sole failure was the older expectation that this now-supported archive must be rejected. That archive moves to positive full history read/re-emission coverage, including exact typed model equality and deterministic encoding. The genuine Draft/offset multi-state rejection cases remain. No local tests ran; static formatting, lint, type and steering checks passed the two affected integration modules.

This is native qualification of a complete reconstructed history within its own source document. It does not independently author the three-feature document or qualify arbitrary multi-state journals. See [the history-state API](../FusionHistoryStates.md) and [the timeline entity gotcha](../../../Gotchas/Conversion/Fusion/History/FusionTimelineGroupEntities.md).
