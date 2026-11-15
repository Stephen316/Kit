# Compare saved Cut support against licensed SOLIDWORKS

Pass the copied [P04 readback outputs](../../Workers/SolidWorksQueuedReadback.md) and the trusted receipt digest to the support report.

```sh
python re/automation/P04LicensedSupport.py /private/P04Readback --receipt-sha256 RECEIPT_SHA256
```

The report verifies the original SOLIDWORKS capture roster, native collector source, plan, receipt and measurements. It decodes each saved part through the public reader and follows CutSketch to the earlier native boss. It compares the saved owner, plane normal and plane offset to the licensed observation before and after rebuild. It calculates the remaining cap area from the two saved profile perimeters and compares it to the measured native face area.

The report preserves each archive digest and both lifecycle observations. The signed plane offset is measured from the native model-to-sketch transform. The archive occurrence and the application's persistent face reference have separate identities. Editable cross-format acceptance remains pending.

The `dd0873d1b` replay matched all eleven P04 parts and both observation phases. The licensed receipt SHA-256 is `6d52f5fc595385bab4920200ffa91c20439086d9fa50fa4e0578183d9eb26cdc`. The replay report SHA-256 is `647cb09e0b240caadfeb52ce9b3cc33fa3607609a88ffcf16b1eeeef2a644cd5`. The existing final-body comparison reproduced the same eleven-pair report after the shared custody checks were extracted.
