// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { execFileSync } = require("node:child_process");

function ReadBaseVersion(Content) {
  return execFileSync(
    "python3",
    [
      "-c",
      String.raw`from re import fullmatch
from sys import stdin
from tomllib import load

Version = load(stdin.buffer)["project"]["version"]
Pattern = r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}"
if not isinstance(Version, str) or not fullmatch(Pattern, Version):
    raise SystemExit("Expected a three-part base package version")
print(Version)
`,
    ],
    { input: Content, encoding: "utf8" },
  ).trim();
}

module.exports = { ReadBaseVersion };
