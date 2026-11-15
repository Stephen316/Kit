# Compare saved P04 sketch dimensions against licensed SOLIDWORKS

Use the copied [P04 readback outputs](../../Workers/SolidWorksQueuedReadback.md) and the trusted receipt digest.

```sh
python re/automation/P04LicensedSketch.py /private/P04Readback --receipt-sha256 RECEIPT_SHA256
```

The report uses the same capture and collector pins as the [licensed cap comparison](SolidWorksLicensedCutSupport.md). It reads the two P04 sketches through the public reader and matches each saved length to the native dimension of the same name and sketch owner. Before and after rebuild it compares the measured length and whether it drives the sketch or is owned by a centering equation.

The centering expressions must reference the measured base and cut sizes in the saved operand order. The report verifies both native equation attachments to their target dimensions and evaluates the two measured differences divided by two. This covers the verified P04 sketches and keeps the observations separate from an editable cross-format round trip.

The `008e83c08` replay matched both licensed phases for eleven parts. It checked 88 driving and 44 derived dimension observations, with 44 measured equation assignments. The report's SHA-256 is `f64a9141829077017eee094fb8b2a2c8409b71fe1f59ee1eafbb3b3fe54b6fc7`.
