# CLAUDE.md — chainner-multivid Architectural Contract

## Fork Purpose

Fork of [chaiNNer-org/chaiNNer](https://github.com/chaiNNer-org/chaiNNer) under `wyghst/chainner-multivid`.

**Feature goal:** Process a whole folder of videos in one run — queue every video in a folder and process them sequentially with the same chain.

---

## Critical Constraint: Single Iterator Per Lineage

chaiNNer enforces that **only one iterator node may exist per chain lineage**. The existing `Load Video` node is already an iterator (over frames). Nesting a "folder of videos" iterator inside it would create two iterators in one lineage — which chaiNNer explicitly prohibits.

**Chosen design:** The orchestration layer re-runs the entire chain once per video, swapping the input video path each pass. This keeps exactly one iterator per chain run. The feature lives in the **input/orchestration layer only** — not in frame-iteration logic, not in core nodes.

---

## Build & Run Commands

```bash
# Install dependencies (requires Node.js >= 18, npm >= 7)
npm install

# Run in dev mode (Electron)
npm run dev

# Build distributable
npm run make

# Run tests
npm test
```

Python backend is managed automatically by chaiNNer's integrated Python support. No manual Python setup needed for development builds.

---

## Do-Not-Touch List

- `backend/src/nodes/` — all existing node implementations, especially `load_video` and `save_video`
- `src/common/nodes/` — node type definitions and iterator registration
- Frame-iteration logic inside the execution engine
- Any existing chain file (`.chn`) format

---

## Conventions

- **Feature branch:** `feature/multi-video-batch` (never commit feature work to `main`)
- **Commit style:** `type: description` (e.g., `feat:`, `fix:`, `chore:`, `docs:`)
- **Feature code location:** TBD after Phase 2 planning (see `PLAN.md`)
- **DEVLOG.md:** Updated at the end of every working session (reverse-chronological)

---

## Syncing Upstream

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
# Then rebase feature branch if needed:
git checkout feature/multi-video-batch
git rebase main
```

---

## Remotes

| Remote   | URL                                          |
|----------|----------------------------------------------|
| origin   | git@github.com:wyghst/chainner-multivid.git  |
| upstream | git@github.com:chaiNNer-org/chaiNNer.git     |
