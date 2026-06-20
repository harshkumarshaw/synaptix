# Synaptix — First Session Guide

> **Welcome, Sila.** This is your Day 1 walkthrough for opening Antigravity and starting development.
>
> Estimated time: 60-90 minutes for full setup.

---

## What You're About to Do

You're about to set up the Synaptix development environment, do an initial commit, and prepare for your first agent-assisted development session.

By the end of this guide, you will have:
- A working local PostgreSQL database (cost: ₹0)
- A git repository with the framework committed
- An Antigravity workspace configured with your agent rules
- A clear understanding of how to start a session and what to expect

---

## Prerequisites Checklist

Before starting, confirm you have:

- [ ] Windows 10/11 with WSL2 enabled (recommended) or pure Windows
- [ ] Docker Desktop installed and running
- [ ] Git for Windows installed
- [ ] Python 3.12+ installed (`python --version`)
- [ ] Node.js 20 LTS+ installed (`node --version`)
- [ ] Google Antigravity installed (1.x or 2.0 — both supported)
- [ ] A code editor (Antigravity is one; VSCode works too as supplement)
- [ ] A GitHub account (for hosting the repo)
- [ ] At least 16 GB RAM (recommended for running Docker + IDE + agents)
- [ ] At least 50 GB free disk space

---

## Step 1: Initial Setup (15 minutes)

### 1.1 Open PowerShell as Administrator

Press `Win + X`, click "Windows PowerShell (Admin)" or "Terminal (Admin)".

### 1.2 Navigate to where you want the project

```powershell
cd C:\Users\YourName\Projects
```

### 1.3 Clone or unzip the framework

If you received the framework as a zip:
```powershell
Expand-Archive synaptix-framework.zip -DestinationPath .
cd synaptix
```

If creating fresh:
```powershell
mkdir synaptix
cd synaptix
# Copy all the framework files here
```

### 1.4 Run the setup script

```powershell
.\scripts\setup-local-dev.ps1
```

This script will:
- Check prerequisites
- Create `.env` from `.env.example`
- Generate a random JWT secret
- Initialise git
- Create `.gitignore`
- Start PostgreSQL via Docker
- Verify everything works

**If any step fails**, the script tells you what to install or fix.

---

## Step 2: Configure GitHub (10 minutes)

### 2.1 Create a private GitHub repo

Go to https://github.com/new and create:
- Repository name: `synaptix`
- Visibility: **Private** (this contains NMC-sensitive logic)
- Don't initialise with README (we have our own)

### 2.2 Connect local to GitHub

```powershell
git add .
git commit -m "chore: initial framework setup"
git remote add origin https://github.com/YOUR_USERNAME/synaptix.git
git branch -M main
git push -u origin main
```

### 2.3 Create branch structure

```powershell
git checkout -b develop
git push -u origin develop
git checkout main
```

Set `develop` as default branch in GitHub settings → Branches.

---

## Step 3: Open Antigravity (10 minutes)

### 3.1 Open the project

Launch Antigravity. Open the `synaptix` folder.

### 3.2 Verify Antigravity reads your config

Antigravity should automatically detect:
- `.antigravity-rules` — project rules
- `AGENTS.md` — agent commandments
- `agents/` — specialist agent specs

If Antigravity 2.0 (desktop app): your projects sidebar should show "synaptix" with the rules badge.
If Antigravity 1.x (IDE): the AI assistant panel should show "Project: Synaptix" with rules loaded.

### 3.3 Test with a simple prompt

In the Antigravity prompt, type:
```
What is the project I'm working on?
```

The agent should respond by referencing Synaptix, the master spec, and the agent system. If it doesn't, your `.antigravity-rules` and `AGENTS.md` aren't being read — check the file locations.

---

## Step 4: Your First Real Session (30 minutes)

### 4.1 Decide on the first task

For your first session, I recommend the **easiest possible win** to verify the system works end-to-end:

**Task: Create the `tenants` and `users` tables, with migration, and basic FastAPI health check.**

This involves the Database Agent + Backend Agent + DevOps Agent + Documentation Agent.

### 4.2 Tell the orchestrator

In Antigravity, start with:

```
I'm starting my first development session. I want to build the foundation tables (tenants, users, roles, permissions) and a basic FastAPI health check endpoint for the snx-auth service.

Please follow the AGENTS.md session start protocol. Read the mandatory files, then propose a plan involving:
1. Database Agent for migrations
2. Backend Agent for the auth service scaffold
3. DevOps Agent for the Dockerfile
4. Documentation Agent for updating CHANGELOG and session log

Then ask me to confirm before any code is written.
```

### 4.3 Review the plan

The orchestrator should respond with:
- Session start declaration ("Read AGENTS.md ✓...")
- A breakdown of tasks per agent
- Files that will be created/modified
- Tests that will be written
- A pause asking for your approval

**Review carefully.** This is your chance to correct the plan before code is generated.

### 4.4 Approve and observe

Once you approve, the agents work. Watch:
- What files they create
- What commands they run
- Whether they follow conventions
- Whether they update docs

### 4.5 Verify at the end

Run:
```powershell
# Run the new tests
pytest tests/unit -v

# Try running the service
cd services/auth
uvicorn app.main:app --reload --port 8001

# In another terminal
curl http://localhost:8001/health
```

You should see `{"status": "ok"}` or similar.

---

## Step 5: Commit and Document (10 minutes)

### 5.1 Check what changed

```powershell
git status
git diff
```

### 5.2 Run pre-commit checks manually first

```powershell
.\scripts\pre-commit-hook.ps1
```

If anything fails, fix it before committing. Common first-time failures:
- Missing tests (Coverage Manifest violation)
- Missing documentation updates
- Conventional Commits format

### 5.3 Commit

```powershell
git add .
git commit -m "feat(auth): add foundation tables and health endpoint

Initial implementation of snx-auth service with:
- tenants, users, roles, permissions tables
- Health check endpoint
- Multi-tenant context middleware (stub)
- All tests passing (X/X)
- NMC compliance tests: N/A for this scope

Refs: Phase 1A initial scaffold
Co-authored-by: backend-agent <02@synaptix.local>
Co-authored-by: database-agent <05@synaptix.local>"
```

### 5.4 Push

```powershell
git push origin develop
```

---

## What to Expect

### Realistic First-Day Outcomes

In your first session, you should NOT expect:
- Production-quality code (it's a scaffold)
- All 49 modules built (it's just the start)
- Zero bugs (agents make mistakes)

You SHOULD expect:
- A working FastAPI service with one endpoint
- A working PostgreSQL database with foundation tables
- Tests that pass
- Documentation that's updated
- A clear understanding of how agents work together

### Common Issues and Fixes

**Issue: Agent doesn't follow AGENTS.md**

Fix: Explicitly tell the agent to re-read AGENTS.md and the session start protocol. If it persists, your `.antigravity-rules` may not be loading.

**Issue: Agent generates code that doesn't compile**

Fix: This is normal. Tell the agent: "This code has an error: [paste error]. Fix it and run tests again."

**Issue: Agent invents NMC regulations**

Fix: STOP the session. Remind the agent: "You are NOT authorised to invent regulations. Re-read NMC_COMPLIANCE_TESTS.md. Cite the exact NMC document and section."

**Issue: Agent modifies files outside its scope**

Fix: Reject the changes. Remind the agent of its scope (per its agent spec file).

**Issue: Tests fail and agent keeps trying to "fix" by modifying tests**

Fix: STOP the agent. Remind it of Commandment 2: "NMC compliance tests are sacrosanct. You may not modify tests to make them pass. The test is correct; your code is wrong."

---

## Daily Workflow After First Session

### Morning Routine

1. Open PowerShell, navigate to project
2. `docker compose up -d` (if not running)
3. `git pull origin develop`
4. Open Antigravity
5. Read `docs/HANDOFF_NOTES.md` for yesterday's notes

### During the Day

- Work in focused sessions (1-2 hours each)
- Each session: one agent specialisation
- Take breaks — agentic development is mentally taxing
- Commit at least once per session

### End of Day

1. Tell the Documentation Agent: "Wrap up this session. Update all relevant docs."
2. Verify `docs/HANDOFF_NOTES.md` makes sense for tomorrow
3. `git push origin develop`
4. `docker compose down` (or leave running)

---

## When You Get Stuck

1. **Check `docs/HANDOFF_NOTES.md`** — maybe there's a note from a previous session
2. **Check `docs/AGENT_LEARNINGS.md`** — maybe an agent learned the answer
3. **Check `docs/DECISIONS.md`** — maybe an ADR explains the design
4. **Re-read `AOIP_MASTER_SPEC_v5.md`** — the answer may be there
5. **Check `.agent-memory/incident/`** — has an agent failed at this before?
6. **Ask the agent: "Why did you do X?"** — agents can explain their reasoning

If still stuck: **make a decision and document it as an ADR.** Don't let things stay ambiguous.

---

## Quality Watchlist

Things to check periodically:

- [ ] **Are NMC compliance tests passing?** (run `pytest tests/compliance`)
- [ ] **Is documentation being updated?** (check `docs/CHANGELOG.md` for recent entries)
- [ ] **Are agents staying in scope?** (check `git log --stat` — any cross-boundary changes?)
- [ ] **Is coverage holding?** (run `pytest --cov` weekly)
- [ ] **Are agent memory files growing?** (`.agent-memory/learning/*.md` should accumulate insights)
- [ ] **Are costs on track?** (Tier 0 should be ₹0 during dev — `docs/COST_LOG.md`)

---

## Phase 1A Milestone

You'll know Phase 1A is complete when:

- [ ] All foundation tables exist (tenants, users, roles, permissions, master_data)
- [ ] snx-auth service runs and handles login (email+OTP at minimum)
- [ ] MFA works for admin role
- [ ] Tenant isolation verified in tests
- [ ] First migration to JMN data done (you'll need to provide a sample CSV)
- [ ] Pre-commit hooks all working
- [ ] CI/CD pipeline passing on GitHub Actions
- [ ] At least 100 tests passing
- [ ] All Phase 1A NMC compliance tests passing

Target: 2 months from start (per ADR-001 aggressive scaffold strategy).

---

## When to Move to Cloud (Don't Yet)

You stay on local Tier 0 (₹0/month) until at least Phase 2 completion. Move to Tier 1 (Cloud Run, ₹25-43K/month) only when:
- Phase 2 modules are MVP-quality
- You're ready to onboard first real users (faculty champions)
- Local dev no longer sufficient for testing real-world scenarios

When the time comes, the DevOps Agent has playbooks for deployment.

---

## Final Note

You're embarking on building a system that, when complete, will serve 600+ students, 100+ faculty, and become NMC inspection-ready. The 49 modules will take 18 months even with aggressive agent assistance.

**Pace yourself.** This is a marathon, not a sprint. The framework you've set up is designed to ensure that no matter how long it takes, the quality holds and the regulations are met.

**Trust the system.** When you feel the urge to skip a step (skip writing a test, skip updating docs, skip the session start protocol), remember: every shortcut is a bug or compliance failure waiting to happen. The framework is rigid because the stakes are high.

**Document everything.** Your future self, three months from now, will thank you for the detailed session logs.

Now: open `AGENTS.md`, then this guide's Step 1. Let's begin.

— *Drafted June 2026, for Sila Singh Ghosh, Chairperson, Nirmala Foundation*
