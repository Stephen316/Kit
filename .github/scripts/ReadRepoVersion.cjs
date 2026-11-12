// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { ReadBaseVersion } = require("./ReadBaseVersion.cjs");

async function ReadRepoVersion(Github, Repository, Revision) {
  const { data: Content } = await Github.rest.repos.getContent({
    ...Repository,
    path: "pyproject.toml",
    ref: Revision,
    mediaType: { format: "raw" },
  });
  return ReadBaseVersion(Content);
}

module.exports = { ReadRepoVersion };
