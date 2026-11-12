// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { execFileSync } = require("node:child_process");
const { CheckBaseOrder } = require("./CheckBaseOrder.cjs");
const { CheckBaseSigner } = require("./CheckBaseSigner.cjs");
const { ReadBaseVersion } = require("./ReadBaseVersion.cjs");
const { ReadRepoVersion } = require("./ReadRepoVersion.cjs");

async function CheckPushBase(Github, Context) {
  const Repository = Context.repo;
  const Start =
    Context.eventName === "push" ? Context.payload.before : `${Context.sha}^`;
  const Changes = execFileSync(
    "git",
    [
      "rev-list",
      "--first-parent",
      `${Start}..${Context.sha}`,
      "--",
      "pyproject.toml",
    ],
    { encoding: "utf8" },
  ).trim();
  for (const Revision of Changes.split("\n").filter(Boolean)) {
    const Before = ReadBaseVersion(
      execFileSync("git", ["show", `${Revision}^:pyproject.toml`]),
    );
    const After = ReadBaseVersion(
      execFileSync("git", ["show", `${Revision}:pyproject.toml`]),
    );
    if (Before === After) continue;
    CheckBaseOrder(Before, After);
    const Pulls = await Github.paginate(
      Github.rest.repos.listPullRequestsAssociatedWithCommit,
      {
        ...Repository,
        commit_sha: Revision,
      },
    );
    const PullRequest = Pulls.find(
      (Candidate) =>
        Candidate.merged_at &&
        Candidate.merge_commit_sha === Revision &&
        Candidate.base.ref === "main",
    );
    if (!PullRequest)
      throw new Error(
        `No merged PR found for base package version change at ${Revision}`,
      );
    const HeadVersion = await ReadRepoVersion(
      Github,
      Repository,
      PullRequest.head.sha,
    );
    if (HeadVersion !== After)
      throw new Error(
        `The merged version ${After} differs from PR #${PullRequest.number}'s version ${HeadVersion}`,
      );
    await CheckBaseSigner(Github, Repository, PullRequest.head.sha);
  }
}

module.exports = { CheckPushBase };
