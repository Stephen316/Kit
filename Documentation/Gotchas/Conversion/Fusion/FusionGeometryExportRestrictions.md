# Fusion geometry exports can have different account restrictions

The installed application's public export API does not guarantee that every supported format is enabled for the current account.

In Fusion 2706.1.17, the controlled cylinder exported successfully as SMT, producing a 2,142-byte file.
The subsequent SAT export raised `Cannot execute the export operation ... as the user is restricted`.
The script recorded the successful SMT artifact before reporting the SAT failure and closing its own document.

Use the successful [SMT artifact and digest](../../../../re/Fusion/LocalOracle/Brep/Export.json) as the geometry oracle.
Do not report the combined export operation as wholly successful or infer a file-format parsing failure from the account restriction.
No private export path or account-setting change was used to bypass it.
