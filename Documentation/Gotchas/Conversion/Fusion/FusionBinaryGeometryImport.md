# Binary Fusion geometry needs the binary import route

`createSMTImportOptions` accepts only the `.smt` extension. Passing a generated `.smb` fails option creation. Renaming the same binary bytes to `.smt` passes option creation but fails document import. The SMT route seems to expect text, but no black-box experiment shows which parser it selects. Neither outcome demonstrates malformed binary geometry.

The installed API documents `TemporaryBRepManager.createFromFile` as supporting SMT, SMB, SAT and SAB. The unchanged generated `.smb` succeeded through that API and produced the expected cylinder. The generated `.smb` retained its geometry after insertion into a direct design, native save and reopen.

The temporary body's `physicalProperties.centerOfMass` returned zero even though its volume and bounding box were correct. The same body reported the correct center after insertion into a persistent native design, and after reopening. Check full physical properties in that context; retain the temporary observation rather than assuming every temporary-property value is authoritative.

The failed binary-as-text import also left an empty, unmodified `Untitled` document despite raising before returning a document handle. Cleanup verified that exact empty state before closing it. Import-oracle cleanup must account for partially created documents without touching unrelated documents.

Evidence: [failed text route](../../../../re/Fusion/LocalOracle/Brep/BinarySmtAcceptance.json), [successful binary route](../../../../re/Fusion/LocalOracle/Brep/BinaryTemporaryAcceptance.json), [temporary center discrepancy](../../../../re/Fusion/LocalOracle/Brep/BinaryTemporaryCenterFailure.json), and [cleanup](../../../../re/Fusion/LocalOracle/Brep/FailedImportCleanup.json).
