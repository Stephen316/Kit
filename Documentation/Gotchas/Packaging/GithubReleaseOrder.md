# GitHub release order

The releases page might appear to list releases by creation time or by release title.
GitHub groups releases by day, newest day first.
In one day, GitHub sorts the releases by tag name in descending order.
The release title does not change the order.

On 2026-11-13, each release used a `commit-<sha>` tag.
The first page of [the releases](https://github.com/TryUniCAD/Kit/releases) showed `Kit v0.1.0.465`, `.458`, `.460`, `.456`, `.462`, `.463`, `.457`, `.459`, `.455`, and `.461`.
These positions follow the descending hexadecimal SHAs `f2ef70b`, `d830b7d`, `c2aee1e`, `bf82de1`, `b146380`, `9ea091d`, `7ce2435`, `646bff9`, `5db2591`, and `49545df`.
The second page started with `.464` (`39d0c34`), the last 2026-11-13 release by SHA.
The 2026-11-12 releases followed in descending SHA order.

Use a tag that sorts in version order, such as `v<package-version>`.
See [version release tags](../../Changes/Packaging/VersionReleaseTags.md) and [GitHub release tags](GithubReleaseTags.md).
