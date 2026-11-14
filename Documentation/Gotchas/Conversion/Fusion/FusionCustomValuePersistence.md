# Registered members do not always determine custom value wire order

Most captured entity groups persist eligible members in lexical name order, but a custom value callback can supply its own order.
Applying the generic lexical rule to `ColorValueMetaType` produced byte-exact reconstruction while assigning the wrong color component names to the four stored floats.

The corrected reader/writer reads the four binary32 values as red, green, blue and alpha.
With that order, comparison with native property observations matches the names and values.

The [typed graph summary](../../../../re/Fusion/Reconstruction/EntityGraph/GraphSummary.json) preserves the evidence.
Byte-identical re-encoding alone proves framing, not correct field semantics. Compare named values with native observations before promoting a schema.
