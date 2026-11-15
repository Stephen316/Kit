# Native assembly markers survive interchange persistence

Expecting the native-feature guard to reject every unresolved native assembly is incorrect.
A CATProduct bytes read has no filesystem base for component lookup and can contain no component histories at all.
Occurrence names remain available while transforms default to identity and proprietary constraints remain in retained native payloads.

The reader records the unresolved state explicitly in assembly and occurrence attributes.
Those markers must participate in public write qualification even after source relabeling or JSON persistence.
The public guard now checks those exact markers recursively before output work.
Keep native reading and explicit model serialization available for inspection; they do not qualify the retained assembly for conversion.

See [the qualification change](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md) and [the native assembly reader](../../../../src/convert/adapters/catia/Assembly.py).
