// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { ReadReviewers } = require("./ReviewConfig.cjs");
const { Reviewers, ExcludedReports } = ReadReviewers();
const Providers = [...Reviewers, ...ExcludedReports];
const KReviewApps = new Set(Providers.map((Provider) => Provider.AppId));
const KReviewUsers = new Set(Providers.map((Provider) => Provider.UserId));

function IsReviewApp(AppInfo) {
  return KReviewApps.has(AppInfo?.id);
}

function IsReviewUser(UserInfo) {
  return KReviewUsers.has(UserInfo?.id);
}

module.exports = { IsReviewApp, IsReviewUser };
