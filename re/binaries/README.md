# External SOLIDWORKS inputs

Use a licensed SOLIDWORKS installation outside repository checkouts.
Follow the [research artifact policy](../../Documentation/Reference/Research/ResearchArtifacts.md).
CAD files, documents, independently authored tools, and recorded format knowledge remain permitted research inputs.

## Verify an installation

`Manifest.json` records expected module names, versions, sizes, and SHA-256 digests for SOLIDWORKS 2025, build `33.5.0.0053`.
The manifest contains identity metadata and format findings.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1 -VerifyOnly
```

The default source is the manifest's `install_root`.
Use `-InstallRoot <path>` for another licensed installation.
Exit code zero means every expected module matches its recorded size, digest, and file version.
A mismatch requires verification against the actual build before reusing addresses or offsets.

## External analysis copies

If an analysis tool needs separate copies, supply a destination outside every repository checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1 -DestinationRoot C:\CadResearch\Solidworks
```

`-VerifyOnly -DestinationRoot <path>` verifies an existing external analysis directory without copying files.
The helper rejects destinations inside its repository checkout.
It does not detect every other checkout or filesystem alias.
Choose the external destination explicitly and keep vendor software out of Git.

## Signature-table research

`GenSignatureTable.py` reads `sldmfcu.dll` from the licensed installation by default.
Pass `--dll <external-path>` for another input.
The tool verifies the recorded digest before accepting its extraction.
Version-specific findings require the matching module build.

The CAD corpus comparison uses `re/data/Serialization/SignatureTable.json` as recorded format evidence.
Set `KIT_SOLIDWORKS_DLL` in an authorized compatibility environment to additionally compare every recorded table row with an external module.
A configured missing path or mismatched digest fails the check.
