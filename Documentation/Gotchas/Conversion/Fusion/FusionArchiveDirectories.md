# Fusion segment lookup requires explicit directories in the authored profile

A ZIP reader can infer directories from member paths. The controlled native Fusion loader did not find segment streams in that authored layout.
The first independent candidate contained eleven valid member paths and no directory entries.
Fusion reported `Initializing segment meta stream failed` before reading segment payloads.

Changing only outer compression from Deflate to stored did not change the failure.
Adding five explicit directory entries, with every member payload unchanged, advanced loading to the entity bulk stream.
That candidate then exposed a separate record-offset failure. It was not yet accepted as a complete document.

Generate explicit directory entries for the asset, each segment, and previews before their members.
Do not infer whole-document acceptance from passing this container boundary.
The [packaging evidence](../../../../re/Fusion/LocalOracle/Authored/PackagingEvidence.json) records exact candidate digests and native load errors.
