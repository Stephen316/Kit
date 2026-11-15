# Compare saved Cut support against licensed SOLIDWORKS

Pass the copied [P04 readback outputs](../../Workers/SolidWorksQueuedReadback.md) and the trusted receipt digest to the support report.

```sh
python re/automation/P04LicensedSupport.py /private/P04Readback --receipt-sha256 RECEIPT_SHA256
```

The report verifies the original SOLIDWORKS capture roster, native collector source, plan, receipt and measurements. It decodes each saved part through the public reader and follows CutSketch to the earlier native boss. It compares the saved owner, plane normal and plane offset to the licensed observation before and after rebuild. It calculates the remaining cap area from the two saved profile perimeters and compares it to the measured native face area.

The report preserves each archive digest and both lifecycle observations. The signed plane offset is measured from the native model-to-sketch transform. The archive occurrence and the application's persistent face reference have separate identities. Editable cross-format acceptance remains pending.
