# Foundation can rewrite a physical path under private

## Expectation

Resolving an existing physical launch path preserves its canonical path spelling.

## Actual behavior

Foundation's URL resolver can remove a leading `/private` when the resulting alias names an existing file. Python and Darwin can keep the `/private` component in the physical path pin, so direct comparison with the Foundation result can refuse a valid bundle or custody record. [Apple Foundation path resolution](https://developer.apple.com/documentation/foundation/nsurl/resolvingsymlinksinpath)

## Workaround

Resolve file paths through Darwin and compare the returned path bytes with the physical pin. For a caller-supplied custody path, require the result to match the original bytes so symlink aliases still fail. [Replacement launch procedure](../../../Changes/Research/Workers/FusionReplacementLaunch.md)
