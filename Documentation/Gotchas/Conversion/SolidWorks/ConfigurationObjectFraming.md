# Empty SOLIDWORKS configuration object streams contain a pointer

The first four bytes of the empty generation-19000 `Contents/CnfgObjs` stream can be mistaken for a dword count. The native store path writes a short list count followed by the configured-relation pointer. The pinned P01 controls have a null pointer and two framed empty configuration-name strings after it.

Consume each field in sequence. A nonempty list or non-null pointer needs its own implementation and authority before generation. [Store sites and controls](../../../../re/solidworks/authoring/PartBookkeeping.md)
