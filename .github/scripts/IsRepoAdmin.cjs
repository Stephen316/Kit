// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

async function IsRepoAdmin(Github, Repository, Author) {
  try {
    const { data: RoleInfo } =
      await Github.rest.repos.getCollaboratorPermissionLevel({
        ...Repository,
        username: Author.login,
      });
    return (
      RoleInfo.permission === "admin" && RoleInfo.user?.id === Author.databaseId
    );
  } catch (ErrorInfo) {
    if (ErrorInfo.status === 404) return false;
    throw ErrorInfo;
  }
}

module.exports = { IsRepoAdmin };
