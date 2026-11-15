# Checkov ecdsa startup dependency

## Expectation

An unused external-check signing feature might appear to permit exclusion of ecdsa from the development environment.

## Actual behavior

Checkov 3.4.3 imports `verify_and_register` from its signature verification registry in `checkov/main.py`.
That registry imports the key loader and verifier, which import ecdsa at module scope.
This happens before an operator selects signature verification options.
Excluding ecdsa therefore breaks scanner startup.

The [ecdsa advisory](https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp) has no patched release.
The [Checkov package](https://pypi.org/project/checkov/3.4.3/) declares the dependency explicitly.

## Workaround boundary

Keep the security scanner enabled while tracking the unresolved dependency.
Replace the cryptographic backend upstream or in a maintained fork before removing ecdsa.
Public-key-only usage does not make the installed dependency a patched release.
See the [recorded blocker](../../Changes/Dependencies/EcdsaRemediationBlocker.md) for the inspected artifact and repair requirement.
