# Things only you can do (step by step)
## One-time setup (before Phase 1)
1. Install: Python 3.12, Node 20+, Git, Docker Desktop. Check with `python --version`, `node --version`, `git --version`, `docker --version`.
2. In your `tangled` folder run `git init`, then create an empty private repo on github.com named `tangled`, and run the two commands GitHub shows (`git remote add origin ...`, `git push -u origin main`).
3. Copy `.github/` and `docs/` from this kit into the repo root. Copy `tangled-v6.html` into `docs/design/`. Commit: `git add . && git commit -m "Add scope and Copilot instructions"`.
4. Get an LLM key. Either an OpenAI API key (platform.openai.com, add a small prepaid balance, create a key) or a free OpenAI-compatible provider. Put it ONLY in `backend/.env` as LLM_API_KEY (and LLM_BASE_URL/LLM_MODEL if not OpenAI). Never paste it into chat or commit it.
5. In `backend/.env` set JWT_SECRET to a long random value: run `python -c "import secrets;print(secrets.token_urlsafe(48))"` and paste the output.
6. In GitHub repo Settings, Branches, add a rule requiring the CI check before merging to main (optional but recommended).
## Each phase
Branch: `git checkout -b phase-N`. Paste prompt into Copilot Agent. Run `cd backend && pytest -q` and `cd frontend && npm run build` yourself. Do the Human check in the prompt. Commit, push, open a pull request, merge when green.
## Before the pilot
1. Ask your instructor in writing to approve: running the pilot, the consent text, and that questions go to an AI provider. Show them the Privacy page.
2. Prepare 6-10 real course files (the PDFs/slides/notebooks from your weeks). Remove any file with personal data or marked confidential. Your course outline PDF carries a confidentiality notice, so ask the institute before uploading anything marked confidential.
3. Write a quiz of 8-10 questions with 4 options, each wrong option representing a specific mistake. Run it with the class and export counts per option; build the aggregate CSV (item,concept,option,count,correct).
4. Dry run with 3-4 classmates for a day: fix what breaks, then label their messages to test the classifier workflow.
5. Deploy following `docs/DEPLOY.md` and test the join link from a phone on mobile data.
## During and after
Share the join link or code on the class channel. Do the mid-pilot instructor review session. After the pilot, hand-label ~200 messages (and have a classmate label 50 for agreement), run `ml.evaluate`, then delete course data if you promised to.
