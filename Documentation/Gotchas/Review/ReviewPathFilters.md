# Review path filters

Each review integration might appear to accept a glob array of ignored paths. The repository configuration file accepts `ignorePatterns` as one newline-separated string. An array is not the documented form. The other integration has no file filter. Its `REVIEW.md` instructions are context, not an enforced filter. Its only hard skip is the `linguist-generated` attribute, and GitHub then collapses those diffs. See [review path exclusions](../../Changes/ReviewPathExclusions.md) for the current configuration.
