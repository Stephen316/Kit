# Fusion P03 affected depth replay

The replay tool indexes the immutable Fusion P03 field search report for both reached depth record types. It retains the matching encoding and each alternative with its prior byte contradictions or unrepresentable inputs. Each save entry binds the exact archive digest, reached body digest and range, prior bytes, signed depth measurement and source receipt. The input report must match the known proof SHA-256 `beffd2fe7ad6fa085973ea65ab273b396083f74cf04f0ca6520bdb449ca44ac5`. [Field search](FusionSignedDepthSearch.md), [Replay command](../../../../re/automation/P03DepthReplay.py)

Choose one reached role and a proposed encoding from the original bounded search. For each save the selector compares the old and proposed encoded byte sets at its measured experiment value. A save reuses its pinned observation when the sets match. A changed representable prediction queues a replay, while an unrepresentable prediction can be recorded immediately. Replay order gives known distinguishing counterexamples priority, then prefers save values with fewer repetitions and uses the variant name as a stable tie-breaker. This is a Stage 12 selector for one discovery workload. Its input changes only the numeric encoding at the established field position.

```powershell
python -B re/automation/P03DepthSearch.py > P03DepthProof.json
python -B re/automation/P03DepthReplay.py P03DepthProof.json parameter f64:little:cm:magnitude > P03DepthIndex.json
```

The plan prints its index in JSON. In the example the selector chooses only `direction-negative`. The seven other saves keep the same predictions, including the 12 mm magnitude control and the repeated baseline. The index records whether each proposed byte prediction matches the existing pinned observation at the established position. A request for the retained encoding produces an empty replay list.

To run the affected archives through the shared A03 inference runner, supply `--schedule-request` with the ordinary bound request for `p03-blind-boss.fusion`. It must name the full eight-save archive and prepared stream roster. The command then emits a regular `Controller.py schedule` input. It returns JSON `null` when there is no new work. [Inference scheduling and runner setup](../Controller/DeterministicInference.md)

```powershell
python -B re/automation/P03DepthReplay.py P03DepthProof.json parameter f64:little:cm:magnitude --schedule-request P03InferenceRequest.json > P03Schedule.json
python -B re/automation/Controller.py --store P03Store schedule P03Schedule.json
```

The selector keeps the ordinary assessment job, bound streams and inputs intact. A03 can reuse an existing assessment while dependent rescan jobs read only the selected native archives. Each selected job ID includes the prior proof, field change and native observation digest. Existing archive results stay available for unchanged saves. The shared rescan reports public reader evidence for each selected source. The field prediction and its contradictions remain in the index. Both records describe discovery evidence. Changing the capture set or field layout needs a new proof and workload.

An independent commissioning runner verified the changed prediction in one Windows A03 attempt. The `Parameter` body byte +128 contains `000000000000f0bf`, the centimetre value −1.0. The magnitude hypothesis expects positive bytes, with no matching position anywhere in that record body. The archive SHA-256 is `4cfc1e792d33d48e4b80f9829a4496cf70c2059378ce1b3cfa716b3a1c9e8aab`, the A03 attempt receipt digest is `fdc818c1f943e1ff41783c111bb908ba4772f5ca1cb881c025b8e6be0c3f17fb`, and the result digest is `dbb0dc9e3f543b13a68020eba29661124e8dc4dd0869166f1725409d4713393e`.

The shared A03 runner kept all nine prior receipts for the assessment and eight original archive results. It completed one new `inference.rescan` for the negative-direction save. Submitting the same schedule again kept that receipt. The new receipt digest is `3c3290bae1318c1bb82024c632101f2f4c7c5e3ca6f40c21bac57d70b8657dd5`, the result digest is `022a7df76b93f9994793005fe2ec614c7ec35de27ccfe71ded79d79aa88e5647`, and the replay summary SHA-256 is `5271f50f7c9a5a7b4a2c05acae889bb8c55569d60f50721f828f79004024f3fb`.
