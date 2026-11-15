# SDK writer fallback can accept an unknown suffix

The SDK writer selector returns a sole supporting writer before checking file extensions.
An unknown output suffix therefore does not always cause a registry error.
This is useful for the SDK's general destinations but conflicts with a file-conversion CLI whose destination suffix selects the output type.

The CLI resolves a unique registered writer from the destination suffix and passes its format explicitly to the SDK.
Unknown or ambiguous suffixes require an explicit `--to FORMAT`.
Refusal happens before staging and preserves an existing destination even with `--overwrite`.

[Fusion compatibility run 43653469450](https://github.com/TryUniCAD/Kit/actions/runs/43653469450) exposed this behavior: the unknown-suffix case failed while 2970 cases passed.
The SDK selector is unchanged.
An explicit format still retains that adapter's destination constraints: the JSON writer requires a `.json` pathname.
The first new explicit-format case incorrectly expected JSON output to an unconventional name; [run 43654362487](https://github.com/TryUniCAD/Kit/actions/runs/43654362487) rejected it before writing.
Process coverage now retains that JSON refusal and verifies byte-exact explicit Fusion output to the same unconventional filename.
No local tests ran.
