const Fs = require("node:fs");
const Path = require("node:path");
const Crypto = require("node:crypto");
const Process = require("node:child_process");
const { CiWorkflows, WorkflowPath } = require("./CiAllowlist.cjs");

async function ReadReports(Github, Context, Refs, Workflows, Reused = false) {
  const Repository = Context.repo;
  const LatestRuns = new Map();
  const Checks = [];
  const ReportRefs = new Set(Refs);
  for (const Ref of ReportRefs) {
    const Runs = await Github.paginate(
      Github.rest.actions.listWorkflowRunsForRepo,
      {
        ...Repository,
        head_sha: Ref,
        per_page: 100,
      },
    );
    for (const Run of Runs) {
      const Workflow = Run.path?.split("@")[0];
      const Spec = Workflows.get(Workflow);
      if (
        !Spec ||
        Run.id === Context.runId ||
        Run.head_sha !== Ref ||
        Spec.event !== Run.event
      )
        continue;
      const Key = `${Workflow}:${Ref}`;
      if (!LatestRuns.has(Key) || LatestRuns.get(Key).id < Run.id)
        LatestRuns.set(Key, { ...Run, workflow: Workflow });
    }
    Checks.push(
      ...(await Github.paginate(Github.rest.checks.listForRef, {
        ...Repository,
        ref: Ref,
        filter: "latest",
        per_page: 100,
      })),
    );
  }

  const RunsBySuite = new Map(
    [...LatestRuns.values()].map((Run) => [Run.check_suite_id, Run]),
  );
  const Rows = [];
  const Seen = new Set();
  for (const Check of Checks) {
    if (
      Seen.has(Check.id) ||
      Check.app?.id !== 15368 ||
      !ReportRefs.has(Check.head_sha)
    )
      continue;
    const Run = RunsBySuite.get(Check.check_suite?.id);
    if (!Run) continue;
    const Spec = Workflows.get(Run.workflow);
    const Required = Spec.required.includes(Check.name);
    const Preflight = Spec.preflight && Check.name === Spec.preflight;
    if (!Required && !Preflight && !Spec.optional?.includes(Check.name))
      continue;
    Seen.add(Check.id);
    const AllowedSkip =
      Spec.skip?.includes(Check.name) ||
      (Preflight && Run.event === "pull_request") ||
      (Reused && Required && Spec.preflight);
    Rows.push({
      name: Check.name,
      workflow: Run.workflow,
      state:
        Check.status !== "completed"
          ? "pending"
          : Check.conclusion === "success" ||
              (Check.conclusion === "skipped" && AllowedSkip)
            ? "pass"
            : "fail",
      conclusion: Check.conclusion,
      url: Check.html_url || Check.details_url || "",
    });
  }
  for (const Run of LatestRuns.values()) {
    if (Run.status !== "completed" || Run.conclusion !== "success")
      Rows.push({
        name: Run.name,
        state: Run.status !== "completed" ? "pending" : "fail",
        conclusion: Run.conclusion,
        url: Run.html_url,
      });
  }
  for (const [Workflow, Spec] of Workflows) {
    const Expected = Spec.preflight
      ? [...Spec.required, Spec.preflight]
      : Spec.required;
    for (const Name of Expected) {
      if (!Rows.some((Row) => Row.name === Name && Row.workflow === Workflow))
        Rows.push({
          name: Name,
          state: "pending",
          conclusion: "missing",
          url: "",
        });
    }
  }
  return Rows;
}

async function LoadEvidence(Github, Repository, Artifact) {
  if (
    Artifact.expired ||
    Artifact.size_in_bytes > 1048576 ||
    !Artifact.digest?.startsWith("sha256:")
  ) {
    throw new Error("CI evidence is expired, oversized, or missing its digest");
  }
  const Download = await Github.rest.actions.downloadArtifact({
    ...Repository,
    artifact_id: Artifact.id,
    archive_format: "zip",
  });
  const Bytes = Buffer.from(Download.data);
  if (
    Bytes.length > 1048576 ||
    `sha256:${Crypto.createHash("sha256").update(Bytes).digest("hex")}` !==
      Artifact.digest
  ) {
    throw new Error("CI evidence artifact digest mismatch");
  }
  const Directory = Fs.mkdtempSync(
    Path.join(process.env.RUNNER_TEMP, "PrCiEvidence-"),
  );
  const ArchivePath = Path.join(Directory, "Evidence.zip");
  Fs.writeFileSync(ArchivePath, Bytes);
  return JSON.parse(
    Process.execFileSync("unzip", ["-p", ArchivePath, "Evidence.json"], {
      maxBuffer: 65536,
      encoding: "utf8",
    }),
  );
}

async function FindReuse(Github, Context, Core) {
  if (Context.eventName !== "merge_group")
    return { reuse: false, reason: "Fresh PR or push validation" };
  const Group = Context.payload.merge_group;
  const Branch = Group.base_ref.replace(/^refs\/heads\//, "");
  const Repository = Context.repo;
  const Candidate = (
    await Github.rest.git.getCommit({
      ...Repository,
      commit_sha: Group.head_sha,
    })
  ).data;
  const Entries = [];
  let Cursor = null;
  do {
    const Data = await Github.graphql(
      `query($owner:String!,$name:String!,$branch:String!,$cursor:String) {
        repository(owner:$owner,name:$name) {
          mergeQueue(branch:$branch) {
            entries(first:100,after:$cursor) {
              pageInfo { hasNextPage endCursor }
              nodes { pullRequest { number headRefOid baseRefName state } }
            }
          }
        }
      }`,
      {
        owner: Repository.owner,
        name: Repository.repo,
        branch: Branch,
        cursor: Cursor,
      },
    );
    const Queue = Data.repository.mergeQueue;
    if (!Queue)
      return { reuse: false, reason: "Queue membership is unavailable" };
    Entries.push(...Queue.entries.nodes);
    Cursor = Queue.entries.pageInfo.hasNextPage
      ? Queue.entries.pageInfo.endCursor
      : null;
  } while (Cursor);
  const Pulls = [];
  for (const Entry of Entries) {
    const Pull = Entry.pullRequest;
    if (!Pull || Pull.state !== "OPEN" || Pull.baseRefName !== Branch) continue;
    const Compared = await Github.rest.repos.compareCommits({
      ...Repository,
      base: Pull.headRefOid,
      head: Group.head_sha,
    });
    if (["ahead", "identical"].includes(Compared.data.status)) Pulls.push(Pull);
  }
  if (!Pulls.length)
    return { reuse: false, reason: "No matching queued PR heads" };
  let Match = null;
  for (const Pull of Pulls) {
    const Current = (
      await Github.rest.pulls.get({ ...Repository, pull_number: Pull.number })
    ).data;
    if (Current.state !== "open" || Current.head.sha !== Pull.headRefOid)
      return { reuse: false, reason: "A queued PR changed" };
    const Runs = await Github.paginate(
      Github.rest.actions.listWorkflowRunsForRepo,
      {
        ...Repository,
        head_sha: Pull.headRefOid,
        event: "pull_request_target",
        per_page: 100,
      },
    );
    const Run = Runs.filter(
      (Item) => Item.path?.split("@")[0] === WorkflowPath,
    ).sort((Left, Right) => Right.id - Left.id)[0];
    if (!Run || Run.status !== "completed" || Run.conclusion !== "success")
      return { reuse: false, reason: "No successful PR aggregate run" };
    const Artifacts = await Github.paginate(
      Github.rest.actions.listWorkflowRunArtifacts,
      {
        ...Repository,
        run_id: Run.id,
        per_page: 100,
      },
    );
    const Artifact = Artifacts.find(
      (Item) =>
        Item.name === `PrCiEvidence-${Run.run_attempt}` && !Item.expired,
    );
    if (!Artifact) continue;
    const Evidence = await LoadEvidence(Github, Repository, Artifact);
    if (
      Evidence.repository_id !== Context.payload.repository.id ||
      Evidence.format !== "pr-head-tree-v1" ||
      Evidence.workflow_event !== "pull_request_target" ||
      Evidence.pull_number !== Pull.number ||
      Evidence.head_sha !== Pull.headRefOid ||
      Evidence.head_repository_id !== Current.head.repo.id ||
      Evidence.run_id !== Run.id ||
      Evidence.run_attempt !== Run.run_attempt
    )
      continue;
    const HealthRefs = [Pull.headRefOid];
    if (Evidence.report_merge_sha) {
      const Merge = (
        await Github.rest.git.getCommit({
          ...Repository,
          commit_sha: Evidence.report_merge_sha,
        })
      ).data;
      if (
        !Merge.parents.some((Parent) => Parent.sha === Evidence.head_sha) ||
        !Merge.parents.some((Parent) => Parent.sha === Evidence.base_sha)
      )
        continue;
      HealthRefs.push(Evidence.report_merge_sha);
    }
    const Health = await ReadReports(
      Github,
      Context,
      HealthRefs,
      CiWorkflows(true, true),
    );
    if (Health.some((Row) => Row.state !== "pass")) {
      return {
        reuse: false,
        reason: `PR #${Pull.number} lacks current healthy CI`,
      };
    }
    const HeadCommit = (
      await Github.rest.git.getCommit({
        ...Repository,
        commit_sha: Pull.headRefOid,
      })
    ).data;
    const BaseComparison = await Github.rest.repos.compareCommits({
      ...Repository,
      base: Group.base_sha,
      head: Pull.headRefOid,
    });
    if (
      Evidence.base_sha === Group.base_sha &&
      Evidence.base_is_ancestor === true &&
      Evidence.head_tree_sha === Candidate.tree.sha &&
      HeadCommit.tree.sha === Candidate.tree.sha &&
      ["ahead", "identical"].includes(BaseComparison.data.status)
    )
      Match = {
        pull: Pull.number,
        run: Run.html_url,
        tree: Candidate.tree.sha,
        base: Group.base_sha,
      };
  }
  if (!Match)
    return {
      reuse: false,
      reason: "Candidate tree or base differs from the tested PR inputs",
    };
  for (const Pull of Pulls) {
    const Current = (
      await Github.rest.pulls.get({ ...Repository, pull_number: Pull.number })
    ).data;
    if (Current.state !== "open" || Current.head.sha !== Pull.headRefOid)
      return {
        reuse: false,
        reason: "A queued head changed during verification",
      };
  }
  Core.info(
    `Reusing healthy PR CI from ${Match.run} for identical tree ${Match.tree} and base ${Match.base}`,
  );
  return { reuse: true, source: Match };
}

async function SetReuse({ github: Github, context: Context, core: Core }) {
  let Result;
  try {
    Result = await FindReuse(Github, Context, Core);
  } catch (ErrorInfo) {
    Result = {
      reuse: false,
      reason: `Reuse evidence unavailable: ${ErrorInfo.message}`,
    };
  }
  Core.setOutput("reuse", String(Result.reuse));
  await Core.summary
    .addHeading("PR CI reuse")
    .addRaw(`${JSON.stringify(Result)}\n`)
    .write();
}

async function PullMergeRef(Github, Context) {
  const Pull = Context.payload.pull_request;
  const Candidates = [
    Context.eventName === "pull_request" ? Context.sha : null,
    Pull.merge_commit_sha,
  ];
  const Current = (
    await Github.rest.pulls.get({ ...Context.repo, pull_number: Pull.number })
  ).data;
  if (Current.head.sha === Pull.head.sha && Current.base.sha === Pull.base.sha)
    Candidates.push(Current.merge_commit_sha);
  for (const Sha of new Set(Candidates)) {
    if (typeof Sha !== "string" || !/^[0-9a-f]{40}$/.test(Sha)) continue;
    let Commit;
    try {
      Commit = (
        await Github.rest.git.getCommit({ ...Context.repo, commit_sha: Sha })
      ).data;
    } catch (ErrorInfo) {
      if (ErrorInfo.status === 404) continue;
      throw ErrorInfo;
    }
    if (
      Commit.parents.some((Parent) => Parent.sha === Pull.head.sha) &&
      Commit.parents.some((Parent) => Parent.sha === Pull.base.sha)
    )
      return Sha;
  }
  return null;
}

async function Aggregate({ github: Github, context: Context, core: Core }) {
  const IsPull = ["pull_request", "pull_request_target"].includes(
    Context.eventName,
  );
  const ReportMerge = IsPull ? await PullMergeRef(Github, Context) : null;
  const Refs = IsPull
    ? [
        Context.payload.pull_request.head.sha,
        ...(ReportMerge ? [ReportMerge] : []),
      ]
    : [Context.sha];
  const Workflows = CiWorkflows(
    IsPull,
    false,
    Context.payload.action === "opened",
  );
  let Reuse = { reuse: false };
  if (!IsPull) {
    try {
      Reuse = await FindReuse(Github, Context, Core);
    } catch (ErrorInfo) {
      Core.info(
        `Running fresh candidate checks because reuse evidence is unavailable: ${ErrorInfo.message}`,
      );
    }
  }
  const Deadline = Date.now() + 80 * 60000;
  let Rows;
  for (;;) {
    if (IsPull) {
      const Current = (
        await Github.rest.pulls.get({
          ...Context.repo,
          pull_number: Context.payload.pull_request.number,
        })
      ).data;
      if (
        Current.state !== "open" ||
        Current.head.sha !== Context.payload.pull_request.head.sha
      )
        throw new Error("The PR head changed during CI aggregation");
    }
    Rows = await ReadReports(Github, Context, Refs, Workflows, Reuse.reuse);
    const Failed = Rows.filter((Row) => Row.state === "fail");
    if (Failed.length) {
      await Core.summary
        .addHeading("CI failed")
        .addTable([
          ["Check", "Conclusion", "Report"],
          ...Failed.map((Row) => [
            Row.name,
            Row.conclusion || "unknown",
            Row.url,
          ]),
        ])
        .write();
      throw new Error(`CI failed: ${Failed.map((Row) => Row.name).join(", ")}`);
    }
    const Pending = Rows.filter((Row) => Row.state === "pending");
    if (!Pending.length) break;
    if (Date.now() >= Deadline)
      throw new Error(
        `CI aggregation timed out waiting for: ${Pending.map((Row) => Row.name).join(", ")}`,
      );
    Core.info(`Waiting for ${Pending.map((Row) => Row.name).join(", ")}`);
    await new Promise((Resolve) => setTimeout(Resolve, 30000));
  }
  await Core.summary
    .addHeading("CI passed")
    .addTable([
      ["Check", "Conclusion", "Report"],
      ...Rows.map((Row) => [Row.name, Row.conclusion || "unknown", Row.url]),
    ])
    .write();
  if (IsPull) {
    const Pull = Context.payload.pull_request;
    const Head = (
      await Github.rest.git.getCommit({
        ...Context.repo,
        commit_sha: Pull.head.sha,
      })
    ).data;
    const Comparison = await Github.rest.repos.compareCommits({
      ...Context.repo,
      base: Pull.base.sha,
      head: Pull.head.sha,
    });
    const Directory = Path.join(process.env.RUNNER_TEMP, "PrCiEvidence");
    Fs.mkdirSync(Directory, { recursive: true });
    Fs.writeFileSync(
      Path.join(Directory, "Evidence.json"),
      JSON.stringify(
        {
          format: "pr-head-tree-v1",
          workflow_event: Context.eventName,
          repository_id: Context.payload.repository.id,
          head_repository_id: Pull.head.repo.id,
          pull_number: Pull.number,
          head_sha: Pull.head.sha,
          base_sha: Pull.base.sha,
          head_tree_sha: Head.tree.sha,
          base_is_ancestor: ["ahead", "identical"].includes(
            Comparison.data.status,
          ),
          report_merge_sha: ReportMerge,
          run_id: Context.runId,
          run_attempt: Number(process.env.GITHUB_RUN_ATTEMPT),
        },
        null,
        2,
      ),
    );
  }
}

async function VerifyEvidence({
  github: Github,
  context: Context,
  core: Core,
}) {
  const ArtifactId = Number(process.env.PR_CI_ARTIFACT_ID);
  if (!Number.isSafeInteger(ArtifactId) || ArtifactId <= 0)
    throw new Error("Missing published evidence artifact ID");
  const Artifact = (
    await Github.rest.actions.getArtifact({
      ...Context.repo,
      artifact_id: ArtifactId,
    })
  ).data;
  const Evidence = await LoadEvidence(Github, Context.repo, Artifact);
  const Pull = Context.payload.pull_request;
  if (
    Evidence.format !== "pr-head-tree-v1" ||
    Evidence.workflow_event !== Context.eventName ||
    Evidence.repository_id !== Context.payload.repository.id ||
    Evidence.head_repository_id !== Pull.head.repo.id ||
    Evidence.pull_number !== Pull.number ||
    Evidence.head_sha !== Pull.head.sha ||
    Evidence.base_sha !== Pull.base.sha ||
    Evidence.run_id !== Context.runId ||
    Evidence.run_attempt !== Number(process.env.GITHUB_RUN_ATTEMPT)
  ) {
    throw new Error("Published CI evidence does not match this exact PR run");
  }
  const Head = (
    await Github.rest.git.getCommit({
      ...Context.repo,
      commit_sha: Evidence.head_sha,
    })
  ).data;
  const Comparison = await Github.rest.repos.compareCommits({
    ...Context.repo,
    base: Evidence.base_sha,
    head: Evidence.head_sha,
  });
  if (
    Head.tree.sha !== Evidence.head_tree_sha ||
    Evidence.base_is_ancestor !==
      ["ahead", "identical"].includes(Comparison.data.status)
  ) {
    throw new Error("Published CI evidence has inconsistent commit provenance");
  }
  if (Evidence.report_merge_sha) {
    const Merge = (
      await Github.rest.git.getCommit({
        ...Context.repo,
        commit_sha: Evidence.report_merge_sha,
      })
    ).data;
    if (
      !Merge.parents.some((Parent) => Parent.sha === Pull.head.sha) ||
      !Merge.parents.some((Parent) => Parent.sha === Pull.base.sha)
    ) {
      throw new Error("Published CI evidence has inconsistent report refs");
    }
  }
  if (
    Context.eventName === "pull_request" &&
    Evidence.report_merge_sha !== Context.sha
  ) {
    throw new Error(
      "Bootstrap evidence does not identify its actual PR merge ref",
    );
  }
  await Core.summary
    .addRaw(
      `Verified artifact ${Artifact.id} through the GitHub download API, including its digest and exact PR provenance\n`,
    )
    .write();
}

module.exports = { SetReuse, Aggregate, VerifyEvidence };
