# ecdsa remediation blocker

Dependabot alert [2](https://github.com/TryUniCAD/Kit/security/dependabot/2) identifies
[GHSA-wj6h-64fc-37mp](https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp)
in ecdsa 0.19.2.
The advisory concerns timing attacks against secret-key operations.
Upstream provides no patched release.

## Current state

The development dependency Checkov 3.4.3 requires `ecdsa>=0.19.0,<1.0.0`.
The published Checkov 3.4.5 release retains that requirement.
Checkov imports ecdsa through its external-check signature verification modules during startup.
Removing the package from the lock without changing Checkov would break the scanner.

Source inspection found public-key loading and signature verification in those Checkov modules.
The upstream advisory states that signature verification is unaffected.
This is reachability evidence, not a patched dependency or a complete security attestation.
The advisory and the existing OSV entry remain unchanged.
No Dependabot alert was dismissed.

## Required repair

An upstream Checkov release must replace ecdsa with a supported cryptographic backend.
A maintained Checkov fork could provide that change before an upstream release.
Preserve the scanner's existing policies and signature verification when making that migration.
Do not replace this repair with dependency exclusion, scanner removal, or a relocated vulnerable lock.

## Verification

Published package metadata and the Checkov 3.4.3 wheel were inspected on 2026-11-15.
The wheel SHA-256 matches the existing lock: `666f376019f6a9fdbeb5c9d2a57be3fb83a4acd2d924d447942450a926ba0f55`.
No local tests ran.
This documentation change does not repair or close alert 2.
PR checks can validate the documentation change but cannot establish vulnerability remediation.

See the [startup dependency gotcha](../../Gotchas/Packaging/CheckovEcdsaStartup.md)
and the [security reference](../../Reference/Operations/Security.md).
