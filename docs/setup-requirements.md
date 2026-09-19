# Setup Requirements

This template requires a few tools to be installed for full functionality.
Skills remain available when hook prerequisites are missing, but lifecycle
validation cannot run.

## Required

| Tool | Purpose | Install |
| ---- | ---- | ---- |
| **Git** | Version control, branch management | [git-scm.com](https://git-scm.com/) |
| **Codex** | Desktop app or AI agent CLI | `npm install -g @openai/codex` |
| **Python 3** | Hook launcher and JSON validation | [python.org](https://www.python.org/) |
| **Bash** | Lifecycle hook execution | Included with Git for Windows; native on macOS/Linux |

## Recommended

| Tool | Used By | Purpose | Install |
| ---- | ---- | ---- | ---- |
| **jq** | JSON-aware hooks | JSON parsing in commit/push/asset/agent hooks | See below |

### Installing jq

**Windows** (any of these):
```
winget install jqlang.jq
choco install jq
scoop install jq
```

**macOS**:
```
brew install jq
```

**Linux**:
```
sudo apt install jq     # Debian/Ubuntu
sudo dnf install jq     # Fedora
sudo pacman -S jq       # Arch
```

## Platform Notes

### Windows
- Git for Windows includes **Git Bash**. The plugin resolves it from the Git
  installation so Windows' WSL `bash.exe` launcher cannot shadow it.
- Codex loads hook commands from the installed plugin's `hooks/hooks.json`

### macOS / Linux
- Bash is available natively
- Install `jq` via your package manager for full hook support

## Verifying Your Setup

Run these commands to check prerequisites:

```bash
git --version          # Should show git version
bash --version         # Should show bash version
jq --version           # Should show jq version (optional)
python3 --version      # Should show python version
```

## What Happens Without Tools

| Missing Tool | Effect |
| ---- | ---- |
| **jq** | Hooks fall back to Python or basic JSON extraction; complex `apply_patch` payloads require either jq or Python. |
| **Python 3** | Lifecycle hooks cannot start; skills remain available. |
| **Both** | Lifecycle hooks cannot start; skills remain available. |

## Recommended IDE

Codex can be used from the Codex desktop app, its editor integrations, or the terminal CLI.
