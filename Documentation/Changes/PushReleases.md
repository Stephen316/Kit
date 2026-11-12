# Publish commit releases on pushes

`Release.yml` starts when a push updates `main`. It publishes a GitHub release and its six assets for the SHA at the tip of that push. Distinct SHAs use separate concurrency groups, so a later push does not displace another commit's pending release. Manual dispatch remains available from `main` for a commit without a GitHub release.

The workflow publishes `unicad-kit` to PyPI when its version is absent from the index. A push that keeps an existing version still creates its GitHub release. PyPI jobs for the same version share a concurrency group so only one can upload at a time. See the [release guide](CommitReleases.md) for Trusted Publishing setup and retry instructions.

Pull requests run the same artifact build through `ReleaseBuild.yml`. The [previous release build](https://github.com/TryUniCAD/Kit/actions/runs/43168444627) verified the ZIP, tarball, checksums, wheel, and source distribution. The first push to `main` with this change exercises automatic publishing.
