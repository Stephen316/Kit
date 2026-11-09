<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Documentation maintenance and wiki publishing

## Ownership

`Documentation/` is the source of truth for maintained documentation. `Documentation/Reference/` began as a reviewed import of Cubic wiki version 1; its [provenance record](Reference/Provenance.json) preserves original paths, generation time, source revision, and the original content hash. That hash describes the original export, not the edited Markdown.

Cubic's configured repository sync destination is `docs/`. Do not put hand-maintained guides or gotchas there. Future sync PRs must be reviewed and normalized into the existing PascalCase reference paths, with source references checked and provenance updated. The distinct `Documentation/` name avoids collisions with `docs/` on case-insensitive filesystems. Do not merge a duplicate generated tree or relax path policy to accommodate it.

[The hosted Cubic wiki](https://www.cubic.dev/wiki/TryUniCAD/Kit/1) is optional source material. Generation and auto-refresh settings are managed through [Cubic settings](https://www.cubic.dev/wiki/TryUniCAD/Kit); repository import does not enable scheduled refresh, and no scheduled refresh is claimed here. Keep generation separate from the authorized PR reviewer.

## Updating documentation

Add a new entry in [Changes](Changes/Index.md) for every repository addition, update the affected guide, and link both from the PR. Record new gotchas in [Gotchas](Gotchas/README.md) before finishing. Preserve SPDX notices, use PascalCase paths, and format Markdown with the repository's pinned Prettier invocation. Verify source references against the revision described, especially after code moves or generation.

## Publishing the GitHub wiki

The wiki has its own Git history and no repository PR gate. Publish reviewed content from a merged repository revision. If publishing a preview is explicitly requested, identify the unmerged source revision prominently instead of presenting it as merged guidance.

Enable the feature with the authenticated GitHub CLI:

```sh
gh repo edit TryUniCAD/Kit --enable-wiki
```

GitHub requires the first page to be created through its website before the wiki can be cloned. Once initialized:

```sh
git clone https://github.com/TryUniCAD/Kit.wiki.git KitWiki
git -C KitWiki switch -c docs/publish
```

Copy the reviewed Markdown into that checkout. Use `Home.md` for `Documentation/Index.md`; flatten each other repository-relative path into a unique page name, for example `Reference-Overview-ApiReference.md`. Convert local documentation links to wiki URLs without `.md`; convert source-code links to GitHub blob URLs pinned to the published commit. Preserve existing unrelated wiki pages and history.

Maintain `_Sidebar.md` with navigation and `_Footer.md` with the repository source SHA and maintenance link. Check every page target and anchor in the rendered wiki. Stage only the intended page files, commit, and push normally with `--no-verify` to the wiki's observed default branch. This publishing authorization applies to the separate wiki repository, never to direct pushes to the code repository's `main`.

Read back the wiki remote SHA and verify Home, navigation, an API page, source links, and the gotchas page. Record the publication SHA separately from PR merge evidence. See [GitHub's wiki Git workflow](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
