# How to use these prompts with GitHub Copilot (VS Code)
1. Copy this kit's `.github/` and `docs/` folders into the repo root (next to `backend/` and `frontend/`).
2. In VS Code open Copilot Chat, choose **Agent** mode. Copilot reads `.github/copilot-instructions.md` automatically.
3. Run the phases IN ORDER. For each: open the prompt file, paste the whole text into chat, and attach `docs/SCOPE.md` with the + button.
4. When Copilot finishes, do the "Human check" at the bottom of that prompt. Only then commit and start the next phase.
5. If Copilot builds something not in the prompt: reply "Revert that. It is out of scope; add it to docs/CHANGE_REQUESTS.md." Do not accept it.
6. One phase = one git branch + one pull request. Never combine phases.
Order: 01 baseline, 02 courses/auth, 03 topics/materials, 04 student chat, 05 analysis/insights, 06 dashboard UI, 07 hardening/deploy, 08 pilot kit.
