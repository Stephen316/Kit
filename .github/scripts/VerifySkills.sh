# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

set -euo pipefail

ExpectedPath=.agents/skills/standard-pr-practice/SKILL.md
mapfile -t SkillPaths < <(git ls-files -- '*/SKILL.md')
if [ "${#SkillPaths[@]}" -ne 1 ] || [ "${SkillPaths[0]}" != "$ExpectedPath" ]; then
  echo '::error::standard-pr-practice must be the only repository skill'
  exit 1
fi
test "$(head -n 1 "$ExpectedPath")" = '---'
awk '
  NR == 1 { next }
  $0 == "---" { Closed = 1; exit }
  /^name:/ { Names++; if ($0 != "name: standard-pr-practice") exit 1 }
  /^license:/ { Licenses++; if ($0 != "license: MIT") exit 1 }
  /^description: .+/ { Descriptions++ }
  END { if (!Closed || Names != 1 || Licenses != 1 || Descriptions != 1) exit 1 }
' "$ExpectedPath"
for GuidancePath in AGENTS.md CLAUDE.md; do
  test -f "$GuidancePath"
  grep --fixed-strings --quiet "$ExpectedPath" "$GuidancePath"
done
if [ -n "$(git ls-files -- .kiro/steering .kiro/skills tools/skills)" ]; then
  echo '::error::legacy skills and their generator must not be restored'
  exit 1
fi
echo 'standard-pr-practice is the only repository skill'
