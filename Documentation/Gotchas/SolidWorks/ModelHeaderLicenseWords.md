# SOLIDWORKS ModelHeader license words and archive boundaries

In the generation-19000 `ModelHeader`, the tail of a signed `-1` field followed by the license type 2 produces `ff ff 02 00 00 00`. A scan for CArchive class markers can interpret that byte sequence as a schema-2 definition with an empty name.

At this position the actual serializer writes the third unset time word and then the unsigned license type. Read the fields in that order and preserve the archive counter. The earlier replaced-components list is the final object allocation. [Native stores and pinned controls](../../../re/solidworks/WriterResearch/ModelHeader.md#continuation-and-spatial-frame)
