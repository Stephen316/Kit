<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Timeline and feature state

[Fusion feature index](../README.md)

See [SDK history projection](../../../src/convert/formats/Fusion/HistoryProjection.py) and [history tests](../../../tests/convert/formats/FusionHistoryTests.py).

## Saved study coverage

Saved evidence includes [`timeline-state-detail-decoding.json`](../Study/timeline-state-detail-decoding.json).

| Area               | Observed support                                                                                                                                                                                                                                                                                                                      | Open work                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Timeline and state | Explicit ordered feature references, groups and collapse state, suppression and rollback flags; typed optional-reference footer variants, an imported identity-root occurrence with literal stored gate attributes, explicit occurrence-creation aliases, visible indices and derived marker position in observed root/assembly cases | Other history owner composition, unresolved support/scalar meanings, other group/state layouts and replay |
| Ordinary removal   | Public RemoveBody and RemoveInstance typed target/creator/component-scope associations, including an occurrence removal owned by its parent component; declared source routes retained separately from current collection membership                                                                                                  | Other removal/context variants, final visibility, complete lifecycle replay and regeneration              |

### Saved study findings

Study scripts, reports and capture paths in this section are relative to [the Study directory](../Study/README.md).

The feature `stored_index` is an internal native field. It is **not a global timeline position**. Record-offset order also must not be used as modeling history: a controlled reorder changed the explicit history list while leaving record order unchanged.

Use `timeline_decoding.sequences` for observed history order. `feature_order` excludes group markers; `visible_entries` reflects decoded group expansion. Marker position is derived from rollback flags and group projection. Multiple history owners remain separate. Missing or unrecognized records are reported rather than assigned a guessed order.

`direct-body-feature-decoding.json` decodes six BaseFeature body-pair associations and two BoundaryFill-owned RemoveBody actions across three existing archives. BaseFeature body attributes reciprocate literal BASEFEAT_PM_BODY_REF/BASEFEAT_DM_BODY_REF references, a repeated body list and an owned result anchor. Literal labels remain separate from unproved general source/result lifecycle semantics. RemoveBody's owned selection must agree with its parent BoundaryFill removal list and input tool identities. Nine independent API comparisons, 31 structural checks, nine control archives and eight malformed guards pass. All three main-reader summaries match. Successful records receive the observed feature kind and a separate `direct_body_feature` payload; CopyPaste and failed/other variants stay unsupported. Current visibility, arbitrary direct edits and regeneration remain unresolved.

`timeline-state-detail-decoding.json` recovers 94 previously rejected shared state footers in 23 saved archives: 62 of length76 and 32 of length86. Two optional reference slots account for their size differences. Typed bookkeeping links and repeated suppression flags are checked; other counters/scalars and support meanings remain uninterpreted. Thirty-two explicit creation/snapshot/occurrence aliases explain occurrence entries without filtering snapshots or rewriting native history IDs/order. The original assembly history has ten entries, matching actual API timeline count/order/flags; joint suppression getters and six earlier timeline contrasts are also checked. The helper passed230 focused checks including four malformed guards, exact integrated path comparisons and independent saved API occurrence path checks. Main output supplies only validated state overrides to `timeline_decoding`, attaches separate occurrence-creation references and exposes `timeline_state_details`. This does not establish current solved placement, general visibility rules, history replay or unobserved footer variants.

`remove-feature-decoding.json` adds ordinary public body, root-occurrence and nested-occurrence removal. Typed body proxies/descriptors/anchors or existing occurrence creation datums/snapshots establish the historical target independently of names and collection absence. The native no-parent RemoveBody variant is separate from the old BoundaryFill-owned child; RemoveInstance uses class `D3DC9613-9714-4DBE-99C4-0A76DB3327F1`. The nested API request normalizes to a removal owned by the parent component, which the native dependency scope confirms. Eleven token getter failures and both current occurrence-collection absence diagnostics remain explicit. Eight malformed guards and three earlier BaseFeature/BoundaryFill golden summaries pass. Main `remove_features` classifies only qualified targets, updates matching timeline entries and preserves strict historical direct-body/assembly diagnostics. Declared source paths do not restore current membership or prove final visibility.
