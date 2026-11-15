# Compare saved P04 sketch dimensions against licensed SOLIDWORKS

Use the copied [P04 readback outputs](../../Workers/SolidWorksQueuedReadback.md) and the trusted receipt digest.

```sh
python re/automation/P04LicensedSketch.py /private/P04Readback --receipt-sha256 RECEIPT_SHA256
```

The report uses the same capture and collector pins as the [licensed cap comparison](SolidWorksLicensedCutSupport.md). It reads the two P04 sketches through the public reader and matches each saved length to the native dimension of the same name and sketch owner. Before and after rebuild it compares the measured length and whether it drives the sketch or is owned by a centering equation.

The centering expressions must reference the measured base and cut sizes in the saved operand order. The report verifies both native equation attachments to their target dimensions and evaluates the two measured differences divided by two. This covers the verified P04 sketches and keeps the observations separate from an editable cross-format round trip.

The `008e83c08` replay matched both licensed phases for eleven parts. It checked 88 driving and 44 derived dimension observations, with 44 measured equation assignments. The report's SHA-256 is `f64a9141829077017eee094fb8b2a2c8409b71fe1f59ee1eafbb3b3fe54b6fc7`.

The `44dbcaaa4` replay also matched all 264 ordered attachment slots. The 220 perimeter operands matched the licensed point IDs and local coordinates. The other 44 slots resolved to the licensed Origin feature. Their projected positions matched the saved proxies, which carry sketch-local IDs. The expanded report SHA-256 is `d232bec27cc78ef616415717ae2a8b1bf570351057c6e181077ad37d51094789`.

The `12af84b0c` replay matched 330 native relation rows across both observation phases. These include 88 horizontal relations, 88 vertical relations, 22 Origin coincidences and 132 distance relations. The comparison checks the native current and definition operands against the neutral references. The two offset relations share the same generic native relation and operands. Their individual horizontal and vertical meanings come from the saved distance classes and measured display dimensions. [SOLIDWORKS sketch relation operands](../../../../Gotchas/Conversion/SolidWorksSketchRelationOperands.md)

The report SHA-256 is `65d6527b12f2e51fc72591ebb7d8b00747e347f5af58daeb5bd7b2f1b9205296`.
