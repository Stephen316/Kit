# Black exclusion also matches the Feature directory

The repository's Black `force-exclude` expression `(examples|modules|re)/`
matches the trailing `re/` in `Feature/`. An explicit process-case path under
`tests/convert/Commands/Feature/` can therefore be skipped even though Black exits
successfully. Check its reported file count before treating formatting as evidence.

For these explicitly owned files, run the pinned formatter with
`--force-exclude '^/(examples|modules|re)/'` so the intended exclusions remain
anchored at the repository root. Keep the normal formatting configuration and
do not format the excluded research, modules, or example trees. Verify the
explicit paths in check mode with the same anchored exclusion.
