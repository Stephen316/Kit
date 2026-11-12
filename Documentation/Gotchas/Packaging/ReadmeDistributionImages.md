# README images in distributions

A relative image can work in the repository but fail in a source distribution. The package manifest excludes `files/`. Use an absolute image URL pinned to a repository revision. See [the distribution manifest](../../../pyproject.toml).
