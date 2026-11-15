# A stopped macOS launch helper may never reach the requested control

## Expectation

A deliberately changed bundle pin or retained fence exercises the corresponding Swift provider guard.

## Actual behavior

The initial fixture accepted a generic failure for both controls. A Swift compile or startup failure would pass those assertions before the provider reached either guard. The positive hosted case reported only the generic failure, leaving its provider cause unresolved. [Initial hosted job](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986201023)

The next hosted run passed the six exit-watch cases. Its replacement fixture supplied a valid bundle and a changed fence, but the provider returned the bundle refusal code 5 before reaching fence refusal code 7. The fixture uses Python-resolved paths under `/private/var`. Foundation can strip the initial `/private` component when the corresponding alias exists, so comparing its result directly with the reviewed physical path can reject the same file. [Hosted refusal](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/job/132992935696), [Apple Foundation path resolution](https://developer.apple.com/documentation/foundation/nsurl/resolvingsymlinksinpath)

## Workaround

Check each refusal against its specific return code and reason. Read the bounded stderr excerpt from the disposable fixture when the provider fails unexpectedly. The owner CLI retains its existing generic refusal output for live installations. [Replacement launch procedure](../../../Changes/Research/Workers/FusionReplacementLaunch.md)

Use Darwin `realpath` to compare physical paths. Require supplied bundle, executable, plist, request and fence paths to match their physical paths. Resolve the AppKit-reported bundle and executable paths before comparing them with the reviewed paths.
