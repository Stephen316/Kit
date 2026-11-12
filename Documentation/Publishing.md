<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Publish maintained documentation

## Purpose and source

`Documentation/` is the maintained source of Kit documentation.
This procedure covers reviewed imports and authorized wiki publication.
A documentation PR does not itself publish the wiki.

The reference set began with a generated wiki snapshot.
The `DocumentationSources.InitialWiki.Wiki` and `DocumentationSources.InitialWiki.WikiSettings` fields in [ReviewBot.json](../.agents/skills/standard-pr-practice/ReviewBot.json) identify the optional source and its settings.
The [provenance record](Reference/Provenance.json) retains the original export metadata.
Its original content hash does not describe later edited Markdown.

## Before you start

Identify the source revision and authorized publication destination.
Complete the [documentation review](Maintenance/Review.md).
Read the [delivery requirements](Maintenance/Delivery.md).
Record standards gaps from the [conformance matrix](Standards/Conformance.md).

## Maintain repository pages

1. Update the relevant task and reference pages together.
2. Add the required [change entry](Changes/Index.md).
3. Update navigation for new or moved guides. Update terminology when it changes.
4. Record each new [gotcha](Gotchas/README.md) in a separate file.
5. Preserve license notices and source attribution.
6. Format the changed Markdown.
7. Submit the files through an isolated worktree and PR.

Expected result: the repository contains reviewed source for the intended revision.
No external publication is implied.

## Import generated source

The generator's configured sync destination is `docs/`.
Maintained pages belong in `Documentation/`.
The distinct names avoid a `Docs/` and `docs/` collision on case-insensitive filesystems.

1. Identify the generated export and its source revision.
2. Compare its claims with the current implementation.
3. Map pages to the maintained PascalCase paths.
4. Preserve useful manual content.
5. Repair links and source references.
6. Update provenance without replacing the original export identity.
7. Review the imported content through the normal PR workflow.

Do not merge a duplicate generated tree as the maintained guide.
Do not enable scheduled refresh or another review bot as part of an import.
Generation settings and automated PR review are separate concerns.

## Initialize the wiki

The wiki has a separate Git repository and history.
A repository administrator must authorize any required feature change.
Enabling the wiki does not initialize its Git remote.
GitHub requires the first page to be saved through its website.

See [GitHub's wiki procedure](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
Do not infer that initialization occurred from the feature setting alone.

## Publish an authorized revision

Use a merged, reviewed repository revision for normal publication.
If the user requests an unmerged preview, identify its source SHA prominently.

1. Clone the initialized wiki repository.

   ```sh
   git clone https://github.com/TryUniCAD/Kit.wiki.git KitWiki
   ```

2. Identify the remote default branch that serves the wiki.

   ```sh
   git -C KitWiki ls-remote --symref origin HEAD
   ```

   The observed wiki default is `refs/heads/master`.
   Recheck it before each publication.
   Stop if the remote does not identify its default branch.

3. Create a publication branch in the wiki checkout.

   ```sh
   git -C KitWiki switch -c docs/publish
   ```

4. Map `Documentation/Index.md` to `Home.md`.
5. Map other pages to unique wiki names.
6. Convert documentation links to wiki page links.
7. Convert source links to GitHub URLs pinned to the source SHA.
8. Update `_Sidebar.md` with navigation.

   Replace the repository directory links on the change and gotcha landing pages with wiki page lists.
   Build each list from the matching source directory and its subdirectories at the selected revision.
   Exclude the landing page itself. Keep these lists in the wiki output.

9. Update `_Footer.md` with the source SHA and maintenance link.
10. Inspect every changed rendered page and anchor.
11. Commit only the intended wiki files.
12. Push with `--no-verify` to the verified wiki default branch.

    If the default remains `master`, use this command:

    ```sh
    git -C KitWiki push --no-verify origin HEAD:refs/heads/master
    ```

    Use the verified default branch if it changed.
    Pushing only `docs/publish` does not update the served wiki.

For example, `Reference/Overview/ApiReference.md` maps to `Reference-Overview-ApiReference`.
Preserve unrelated wiki pages and history.
This authorization applies to the separate wiki repository.
It does not authorize a direct push to the code repository's `main` branch.

## Verify publication

1. Read back the wiki remote SHA.
2. Open Home and the sidebar links.
3. Open an API reference and a task procedure.
4. Check their source links and revision labels.
5. Record the source SHA, publication SHA, date, and known limitations.

Expected result: the published pages match the authorized source and identify their revision.
If a link or page fails, correct the publication before claiming completion.
Keep publication evidence separate from PR merge evidence.
