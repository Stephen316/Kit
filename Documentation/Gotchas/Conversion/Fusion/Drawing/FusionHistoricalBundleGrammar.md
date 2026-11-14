# Historical drawing bundles use an older description grammar

The installed 2018 drawing F3Z does not match the current bundle description grammar.
Two differences made the current `ReadBundle` reject it.

| Field                     | Current design bundles      | Historical drawing bundle           |
| ------------------------- | --------------------------- | ----------------------------------- |
| Object `createdAt`        | Present on every object     | Absent                              |
| Relationship `neutronRole`| Plain GUID                  | GUID, underscore, version URN       |

`BundleObject.CreatedAt` is now optional.
`EmitObject` writes `createdAt` only when the value is present.
`CheckRefs` accepts the compound role only when the prefix has 36 characters and the suffix starts with `urn:`.
A plain role still must parse as a UUID.

The drawing root manifest repeats the same compound role in its reference row.
`CheckBundle` compares only the first 36 characters of the bundle and manifest roles.
The redirection table carries the version URN separately.
