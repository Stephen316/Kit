# Windows saves write graphics object identities without a prefix

## Expectation

A graphics object identity is the `%p` text of a native pointer. The macOS save `grouped.f3d` writes the root `GroupNode` identity as `0x454fc09b8`.

## Actual behavior

On macOS, `%p` writes lowercase hexadecimal digits after a `0x` prefix. On Windows, `%p` writes exactly 16 uppercase hexadecimal digits without a prefix.

Kit accepted only the macOS form. It raised `ValueError` with the message `Invalid graphics object identity for GroupNode` for `re/Fusion/examples/.f3d/example2.f3d`.

## Workaround

Accept both forms. Keep the identity text unchanged so that the `world` member stays byte-exact. Reject a zero identity in both forms.

## Evidence

- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [Scene probe script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/Probe.py)
