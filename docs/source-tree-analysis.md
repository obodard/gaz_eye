# Source Tree Analysis — gaz_eye

```
gaz_eye/
├── gaz_saver.py          # Main application — all business logic (270 LOC)
├── stations.yaml         # User configuration — cities, stations, fuel settings
├── requirements.txt      # Python dependencies: requests, pyyaml, colorama
├── README.md             # User-facing documentation and quick start guide
├── .gitignore            # Standard Python gitignore
├── generate-github-agents.sh  # BMAD agent generation script
│
├── docs/                 # Project documentation (generated)
│   ├── index.md
│   ├── project-overview.md
│   ├── architecture.md
│   ├── source-tree-analysis.md
│   └── development-guide.md
│
├── _bmad/                # BMAD framework configuration (not application code)
│   ├── config.toml
│   ├── config.user.toml
│   ├── _config/          # Framework manifests
│   ├── bmm/              # Module configuration
│   ├── core/             # Core framework files
│   ├── custom/           # Customization overrides
│   └── scripts/          # Framework utility scripts
│
├── _bmad-output/         # BMAD output artifacts
│   ├── project-context.md
│   ├── planning-artifacts/
│   └── implementation-artifacts/
│
├── .agents/              # BMAD agent skill definitions (not application code)
│
├── .github/
│   └── agents/           # GitHub Copilot agent definitions
│
└── .venv/                # Python virtual environment (gitignored)
```

## Critical Directories

| Directory         | Purpose                                      |
|-------------------|----------------------------------------------|
| `/` (root)        | All application source files live here        |
| `docs/`           | Generated project documentation               |
| `_bmad/`          | BMAD framework config (not application code)  |
| `_bmad-output/`   | BMAD workflow outputs                         |

## Entry Points

- **Application:** `gaz_saver.py` → `main()` via `if __name__ == "__main__"`
- **Configuration:** `stations.yaml` (user-editable)
