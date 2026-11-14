# Zero opaque bytes is not generation

A typed field program with zero opaque bytes might appear to be generated from format rules.
Kit's removed SOLIDWORKS programs had zero opaque bytes, but each was a recorded payload.
Each operation kept the absolute offset and the value from one vendor save, and `ReplayResolved` rejected output whose length differed from that save.
A new sketch profile therefore needed another recording, and the values were donor data.

Before you report a writer as generated, confirm that a different input can change its length and object count.
Confirm also that each value comes from the input, a rule, or a proven constant.
`tools/Donors/CheckReplays.py` rejects the recorded field program form in `src`.
See the [removal change entry](../../Changes/Solidworks/SolidworksRecordedPayloadRemoval.md).
