#!/usr/bin/env bash
# generate-github-agents.sh
#
# Scans .github/skills/ for BMAD agent SKILL.md files and generates
# corresponding .github/agents/*.agent.md files for GitHub Copilot agent mode.
#
# Usage:
#   ./generate-github-agents.sh           # skip existing files
#   ./generate-github-agents.sh --force   # overwrite existing files
#
# Run after:  npx bmad-method install

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$PROJECT_ROOT/.agents/skills"
AGENTS_DIR="$PROJECT_ROOT/.github/agents"
MANIFEST="$PROJECT_ROOT/_bmad/_config/agent-manifest.csv"

FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

# ---------------------------------------------------------------------------
# Tool list — uniform set for all BMAD agents
# ---------------------------------------------------------------------------
get_tools() {
  echo "[vscode/extensions, vscode/getProjectSetupInfo, vscode/installExtension, vscode/memory, vscode/newWorkspace, vscode/runCommand, vscode/vscodeAPI, vscode/askQuestions, execute/getTerminalOutput, execute/awaitTerminal, execute/killTerminal, execute/createAndRunTask, execute/runInTerminal, execute/runNotebookCell, execute/testFailure, execute/runTests, read/terminalSelection, read/terminalLastCommand, read/getNotebookSummary, read/problems, read/readFile, read/readNotebookCellOutput, agent/runSubagent, browser/openBrowserPage, edit/createDirectory, edit/createFile, edit/createJupyterNotebook, edit/editFiles, edit/editNotebook, edit/rename, search/changes, search/codebase, search/fileSearch, search/listDirectory, search/searchResults, search/textSearch, search/usages, web/fetch, web/githubRepo, todo]"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
mkdir -p "$AGENTS_DIR"

created=0
skipped=0
errors=0

echo "Scanning $SKILLS_DIR ..."
echo ""

for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_dir")"
  agent_name="${skill_name#bmad-}"
  skill_file="$skill_dir/SKILL.md"
  output_file="$AGENTS_DIR/${agent_name}.agent.md"

  [[ -f "$skill_file" ]] || continue

  # Only process skills that are agent activators
  grep -q "## On Activation" "$skill_file" || continue

  # Skip if already exists and --force not set
  if [[ -f "$output_file" ]] && [[ "$FORCE" == false ]]; then
    echo "  ⏭  Skipping  $skill_name  (already exists; run with --force to overwrite)"
    skipped=$((skipped + 1))
    continue
  fi

  # Agent file IS the skill itself
  agent_rel_path=".agents/skills/${skill_name}/SKILL.md"

  # Try manifest lookup first, fall back to parsing SKILL.md
  agent_persona=""
  agent_title=""
  agent_icon=""
  agent_capabilities=""

  if [[ -f "$MANIFEST" ]]; then
    manifest_row=$(python3 -c "
import csv, sys
with open('$MANIFEST', newline='') as f:
    for row in csv.reader(f):
        if len(row) >= 5 and row[0].strip() == '$skill_name':
            print('|'.join([row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip()]))
            sys.exit(0)
" 2>/dev/null) || true
    if [[ -n "$manifest_row" ]]; then
      agent_persona="$(echo "$manifest_row" | cut -d'|' -f1)"
      agent_title="$(echo "$manifest_row" | cut -d'|' -f2)"
      agent_icon="$(echo "$manifest_row" | cut -d'|' -f3)"
      agent_capabilities="$(echo "$manifest_row" | cut -d'|' -f4)"
    fi
  fi

  # Fall back to SKILL.md parsing for skills not in manifest
  if [[ -z "$agent_persona" ]]; then
    h1=$(grep "^# " "$skill_file" | head -1 | sed 's/^# //' | sed 's/[[:space:]]*$//')
    agent_persona=$(echo "$h1" | sed $'s/[^[:print:]]//g' | sed 's/ *[^ a-zA-Z0-9][^ ]*[[:space:]]*$//' | sed 's/[[:space:]]*$//')
    agent_icon=$(echo "$h1" | grep -oE '[^ ]+$' | head -1)
    [[ "$agent_icon" =~ ^[a-zA-Z0-9] ]] && agent_icon=""
  fi
  if [[ -z "$agent_title" ]]; then
    agent_title=$(echo "$skill_name" \
      | sed 's/^bmad-agent-//' \
      | sed 's/^bmad-//' \
      | sed 's/^decom-//' \
      | sed 's/-/ /g' \
      | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1))substr($i,2)} 1')
  fi
  if [[ -z "$agent_capabilities" ]]; then
    agent_capabilities=$(sed -n 's/^description: //p' "$skill_file" | head -1)
  fi

  tools="$(get_tools "$skill_name")"

  cat > "$output_file" <<AGENT_EOF
---
name: ${agent_title}
description: ${agent_title} agent (${agent_persona} ${agent_icon}) — ${agent_capabilities}.
tools: ${tools}
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified. NEVER break character until given an exit command.

<agent-activation CRITICAL="TRUE">
1. LOAD the FULL agent file from {project-root}/${agent_rel_path}
2. READ its entire contents - this contains the complete agent persona, menu, and instructions
3. FOLLOW every step in the <activation> section precisely
4. DISPLAY the welcome/greeting as instructed
5. PRESENT the numbered menu
6. WAIT for user input before proceeding
</agent-activation>
AGENT_EOF

  echo "  ✅  Created  .github/agents/${agent_name}.agent.md  (${agent_persona} — ${agent_title})"
  created=$((created + 1))
done

echo ""
echo "─────────────────────────────────────────────"
echo "  Done: $created created, $skipped skipped, $errors errors"
echo "─────────────────────────────────────────────"
