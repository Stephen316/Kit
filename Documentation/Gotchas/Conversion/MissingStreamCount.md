# Missing stream count

A successful return might appear to prove that the complete payload was written. A `write()` result of `None` bypasses the final count check. Use a reliable count or independently verify output. See [stream boundaries](../../Reference/Architecture/Engine.md#stream-destinations).
