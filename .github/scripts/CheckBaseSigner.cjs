// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { IsRepoAdmin } = require("./IsRepoAdmin.cjs");

async function CheckBaseSigner(Github, Repository, Revision) {
  const Data = await Github.graphql(
    `query($owner:String!,$name:String!,$revision:GitObjectID!) {
      repository(owner:$owner,name:$name) {
        object(oid:$revision) {
          ... on Commit {
            signature { isValid wasSignedByGitHub signer { login databaseId } }
          }
        }
      }
    }`,
    { owner: Repository.owner, name: Repository.repo, revision: Revision },
  );
  const Signature = Data.repository.object?.signature;
  if (
    Signature?.isValid &&
    !Signature.wasSignedByGitHub &&
    Signature.signer?.databaseId &&
    (await IsRepoAdmin(Github, Repository, Signature.signer))
  )
    return;
  throw new Error(
    `The base version change requires a repository administrator's verified signature on PR head ${Revision}.`,
  );
}

module.exports = { CheckBaseSigner };
