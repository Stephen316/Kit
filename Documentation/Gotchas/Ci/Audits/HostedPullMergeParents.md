# Hosted pull request merge parents

The pull request metadata and the merge commit can report different base SHAs after the target branch advances. In PR #94 run `43769573935`, the fetched merge commit had `870e87ea` as its first parent. The pull request metadata reported `e04e7b78`, an ancestor of that parent. The exact hosted tree passed the archive checks before the receipt producer refused the mismatched metadata.

Bind the receipt to the two parents of the exact `GITHUB_SHA` checkout. Check the event head, target branch and base ancestry. A receipt intended for reuse still needs independent verification against the current PR and exact checked tree. [Receipt producer](../../../Changes/Research/Controller/HostedPairedArchiveMergeParents.md)
