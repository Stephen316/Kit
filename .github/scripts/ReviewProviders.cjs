// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const {
  Comment,
} = require("../../.agents/skills/standard-pr-practice/ReviewBot.json");
const Mention = Comment.match(/^@([a-z\d-]+) review$/i);
if (!Mention) throw new Error("Invalid configured review request");

const KReviewApps = new Set([1082092, 867647, 347564]);
const KReviewUsers = new Set([191113872, 165735046, 136622811]);
const KReviewLogins = new Set([
  "cubic-dev-ai",
  "greptile-apps",
  "coderabbitai",
  Mention[1].toLowerCase(),
]);

function IsReviewApp(AppInfo) {
  return (
    KReviewApps.has(AppInfo?.id) ||
    KReviewLogins.has(AppInfo?.slug?.toLowerCase())
  );
}

function IsReviewUser(UserInfo) {
  return (
    KReviewUsers.has(UserInfo?.id) ||
    KReviewLogins.has(UserInfo?.login?.toLowerCase().replace(/\[bot\]$/, ""))
  );
}

module.exports = { IsReviewApp, IsReviewUser };
