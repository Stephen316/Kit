# Progenitor Auxiliary Value Layout

The Fusion 2706.1.17 value type `ProgenitorAuxDataValueMetaType`, identifier `BE7E2847-FBC4-4898-A6E7-632A559A7F89`, carries a four-byte little-endian payload.
The runtime reflection capture reports schema version zero and no base value class.
Kit reads the payload as one unsigned 32-bit field named `tag`.

[ProgenitorValues.py](ProgenitorValues.py) supplies the inverse reader and writer.
The callback consumes no source payload or opaque remainder.

The initial corpus inventory reported this metatype as named metadata in 36 `SweepFaceProgenitor` records and two `EntityProgenitor` records.
The enclosing named-metadata frame already supplies its name and metatype identifier.
The auxiliary value contributes only the four tag bytes.
The parent's corpus inventory owns the subsequent complete-record decode results.

An earlier version also cited static inspection of installed Fusion libraries.
That material was removed.
It was the only source for the field name `tag`, its unsigned type, the absence of other registered members, and a constructor default of `0xffffffff`.
These points are not confirmed by a black-box experiment.
The runtime reflection capture did not initialize this member set, so it does not confirm them either.

The exact tag identity domain and its relationship to geometric tagging remain unproven.
The reader and writer retain every unsigned 32-bit value.
No target-application acceptance was established for an independently changed auxiliary tag.
