// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

function CheckBaseOrder(Before, After) {
  const Previous = Before.split(".").map(BigInt);
  const Proposed = After.split(".").map(BigInt);
  const Index = Proposed.findIndex(
    (Component, Offset) => Component !== Previous[Offset],
  );
  if (Index >= 0 && Proposed[Index] < Previous[Index])
    throw new Error(
      `Base package version cannot decrease from ${Before} to ${After}`,
    );
}

module.exports = { CheckBaseOrder };
