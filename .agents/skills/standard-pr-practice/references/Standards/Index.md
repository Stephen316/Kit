<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Complete repository standards

These are active parts of standard-pr-practice, not separately installed skills.
Every original rule, example, caveat, metadata field, document, image, and tracked
resource from the previous `.agents/` and `.kiro/` skill/steering collections is
preserved in full. Nothing was summarized away. The portable rules are the active
copies of Kiro steering; their original source versions remain available for
provenance. Read each rule set relevant to the task, using the routing table in
`../../SKILL.md`.

The content of each original file is preserved byte for byte after its notice
and provenance wrapper. The original files, paths, modes, and bytes also exist
in [OriginalStandards.zip](../../assets/OriginalStandards.zip), which is a
provenance artifact and is never extracted or installed as additional skills.
[Manifest.json](Manifest.json) records the original Git blob, SHA-256, size, and
current location for every file, pinned to source commit
`bc47bd1a43916f664a11e3be9698b36ec723d8d2`. Remote CI verifies the complete source
inventory against that commit and checks both the archive and readable copies.

## Precedence and path resolution

Current user instructions, `AGENTS.md`, and the operational rules in the main
`SKILL.md` take precedence over conflicting preserved text. All other coding,
quality, security, architecture, naming, formatting, design, and verification
requirements retain their original force and scope. In particular:

- Do not add explanatory code comments or comment-oriented docstrings; preserve
  required license notices and existing comments. The preserved rationale-comment
  guidance records the former rule and does not authorize adding comments now.
- Unit tests remain prohibited. Use integration, end-to-end, smoke, compatibility,
  and repository-wide policy checks at real boundaries. Do not reinterpret an
  old request for an isolated test as permission to add one.
- No tests run locally. Keep permitted static formatting/checking local and
  execute tests remotely, with heavy acceptance in the native merge queue.
- [ReviewBot.json](../../ReviewBot.json) defines the only automated reviewer
  request comment. The main skill defines all-CI follow-up and review evidence
  requirements.
- Only verified repository administrators can explicitly authorize agent merges,
  queue enrollment, auto-merge, or supported overrides under the main skill's
  gates. Ordinary coding requests do not grant merge authority.
- Open normal PRs for this workflow. Preserve worktree isolation and user-owned
  state. Older draft-PR or generator instructions do not change this workflow.
- Do not recreate the old skill trees or run the retired steering generator.
  References to activating another old skill mean reading its consolidated
  document here. Referenced sibling documents, CLI paths, and resource paths
  resolve through the source-to-document mapping in `Manifest.json` relative to
  the document's declared original source path. Those original path strings are
  preserved intentionally; they are not instructions to restore old directories.
  Documents with moved relative links provide current clickable reference tables
  before the preserved payload. Use those links instead of its original paths.
- The original `re/` exemption remains unchanged. Do not expand the scope or
  infer external writes, messages, installations, or permission from copied text.

The original ui-ux-pro-max `data` and `scripts` entries were tracked text pointers,
not bundled data or executable directories. Their exact contents are preserved
below wrapper metadata showing the correctly rebased current resource path.
Neither target exists in the pinned source commit; no missing data or scripts
have been invented or represented as available.

## Portable standards and original steering

| Former skill                | Active complete document                                       | Original steering source                                   |
| --------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| `chats`                     | [Chats](Portable/Chats.md)                                     | [Chats](Kiro/Chats.md)                                     |
| `code-formatting`           | [CodeFormatting](Portable/CodeFormatting.md)                   | [CodeFormatting](Kiro/CodeFormatting.md)                   |
| `compact-tool-descriptions` | [CompactToolDescriptions](Portable/CompactToolDescriptions.md) | [CompactToolDescriptions](Kiro/CompactToolDescriptions.md) |
| `component-architecture`    | [ComponentArchitecture](Portable/ComponentArchitecture.md)     | [ComponentArchitecture](Kiro/ComponentArchitecture.md)     |
| `design-system-discipline`  | [DesignSystemDiscipline](Portable/DesignSystemDiscipline.md)   | [DesignSystemDiscipline](Kiro/DesignSystemDiscipline.md)   |
| `fix-errors-dont-ask`       | [FixErrorsDontAsk](Portable/FixErrorsDontAsk.md)               | [FixErrorsDontAsk](Kiro/FixErrorsDontAsk.md)               |
| `frontend-stack`            | [FrontendStack](Portable/FrontendStack.md)                     | [FrontendStack](Kiro/FrontendStack.md)                     |
| `git-never-touch-main`      | [GitNeverTouchMain](Portable/GitNeverTouchMain.md)             | [GitNeverTouchMain](Kiro/GitNeverTouchMain.md)             |
| `hostcontrol-contract`      | [HostcontrolContract](Portable/HostcontrolContract.md)         | [HostcontrolContract](Kiro/HostcontrolContract.md)         |
| `identifier-markers`        | [IdentifierMarkers](Portable/IdentifierMarkers.md)             | [IdentifierMarkers](Kiro/IdentifierMarkers.md)             |
| `isolated-agent-worktrees`  | [IsolatedAgentWorktrees](Portable/IsolatedAgentWorktrees.md)   | [IsolatedAgentWorktrees](Kiro/IsolatedAgentWorktrees.md)   |
| `layout-system`             | [LayoutSystem](Portable/LayoutSystem.md)                       | [LayoutSystem](Kiro/LayoutSystem.md)                       |
| `linear-issue-tracking`     | [LinearIssueTracking](Portable/LinearIssueTracking.md)         | [LinearIssueTracking](Kiro/LinearIssueTracking.md)         |
| `lossless-translation`      | [LosslessTranslation](Portable/LosslessTranslation.md)         | [LosslessTranslation](Kiro/LosslessTranslation.md)         |
| `mcp-tool-doc-pages`        | [McpToolDocPages](Portable/McpToolDocPages.md)                 | [McpToolDocPages](Kiro/McpToolDocPages.md)                 |
| `naming-convention`         | [NamingConvention](Portable/NamingConvention.md)               | [NamingConvention](Kiro/NamingConvention.md)               |
| `no-cad-runtime`            | [NoCadRuntime](Portable/NoCadRuntime.md)                       | [NoCadRuntime](Kiro/NoCadRuntime.md)                       |
| `no-donor-blocks`           | [NoDonorBlocks](Portable/NoDonorBlocks.md)                     | [NoDonorBlocks](Kiro/NoDonorBlocks.md)                     |
| `no-stubs`                  | [NoStubs](Portable/NoStubs.md)                                 | [NoStubs](Kiro/NoStubs.md)                                 |
| `no-unrequested-styling`    | [NoUnrequestedStyling](Portable/NoUnrequestedStyling.md)       | [NoUnrequestedStyling](Kiro/NoUnrequestedStyling.md)       |
| `page-title-separator`      | [PageTitleSeparator](Portable/PageTitleSeparator.md)           | [PageTitleSeparator](Kiro/PageTitleSeparator.md)           |
| `pin-dependencies`          | [PinDependencies](Portable/PinDependencies.md)                 | [PinDependencies](Kiro/PinDependencies.md)                 |
| `pixi-lockfiles`            | [PixiLockfiles](Portable/PixiLockfiles.md)                     | [PixiLockfiles](Kiro/PixiLockfiles.md)                     |
| `python-package-manager`    | [PythonPackageManager](Portable/PythonPackageManager.md)       | [PythonPackageManager](Kiro/PythonPackageManager.md)       |
| `rationale-comments`        | [RationaleComments](Portable/RationaleComments.md)             | [RationaleComments](Kiro/RationaleComments.md)             |
| `react-doctor`              | [ReactDoctor](Portable/ReactDoctor.md)                         | [ReactDoctor](Kiro/ReactDoctor.md)                         |
| `repository-structure`      | [RepositoryStructure](Portable/RepositoryStructure.md)         | [RepositoryStructure](Kiro/RepositoryStructure.md)         |
| `shadcn-pages`              | [ShadcnPages](Portable/ShadcnPages.md)                         | [ShadcnPages](Kiro/ShadcnPages.md)                         |
| `spdx-header`               | [SpdxHeader](Portable/SpdxHeader.md)                           | [SpdxHeader](Kiro/SpdxHeader.md)                           |
| `split-large-definitions`   | [SplitLargeDefinitions](Portable/SplitLargeDefinitions.md)     | [SplitLargeDefinitions](Kiro/SplitLargeDefinitions.md)     |
| `user-owned-workspace`      | [UserOwnedWorkspace](Portable/UserOwnedWorkspace.md)           | [UserOwnedWorkspace](Kiro/UserOwnedWorkspace.md)           |
| `workos-token-verification` | [WorkosTokenVerification](Portable/WorkosTokenVerification.md) | [WorkosTokenVerification](Kiro/WorkosTokenVerification.md) |

## Interface and design standards

These complete instruction documents retain all their supporting resources in
the adjacent folders. Resolve their original filenames through the manifest as
specified above; no independent skill registration is created.

| Former skill                  | Complete instruction document                                               |
| ----------------------------- | --------------------------------------------------------------------------- |
| `baseline-ui`                 | [BaselineUi](Design/BaselineUi/Instructions.md)                             |
| `design-lab`                  | [DesignLab](Design/DesignLab/Instructions.md)                               |
| `fixing-accessibility`        | [FixingAccessibility](Design/FixingAccessibility/Instructions.md)           |
| `fixing-motion-performance`   | [FixingMotionPerformance](Design/FixingMotionPerformance/Instructions.md)   |
| `frontend-design`             | [FrontendDesign](Design/FrontendDesign/Instructions.md)                     |
| `interface-design`            | [InterfaceDesign](Design/InterfaceDesign/Instructions.md)                   |
| `make-interfaces-feel-better` | [MakeInterfacesFeelBetter](Design/MakeInterfacesFeelBetter/Instructions.md) |
| `react-doctor`                | [ReactDoctor](Design/ReactDoctor/Instructions.md)                           |
| `shadcn`                      | [Shadcn](Design/Shadcn/Instructions.md)                                     |
| `ui-ux-pro-max`               | [UiUxProMax](Design/UiUxProMax/Instructions.md)                             |

The [original agent index](Provenance/AgentIndex.md) preserves the former routing
and generation mapping. Its workflow and generator instructions are superseded
by the current main skill; its original text is retained for lossless provenance.
