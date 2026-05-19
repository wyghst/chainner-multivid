# CLAUDE.md — chainner-multivid Architectural Contract

## Fork Purpose

Fork of [chaiNNer-org/chaiNNer](https://github.com/chaiNNer-org/chaiNNer) under `wyghst/chainner-multivid`.

**Feature goal:** Process a whole folder of videos in one run — queue every video in a folder and process them sequentially with the same chain.

---

## Critical Constraint: Single Iterator Per Lineage

chaiNNer enforces that **only one iterator node may exist per chain lineage**. The existing `Load Video` node is already an iterator (over frames). Nesting a "folder of videos" iterator inside it would create two iterators in one lineage — which chaiNNer explicitly prohibits.

**Chosen design (revised):** Two new backend nodes — `Load Videos` (generator) and `Save Videos` (collector) — added to the `video_frames` package. `Load Videos` takes a directory, scans for video files, and yields every frame from every video sequentially as a single flat stream. This satisfies the single-iterator rule (one generator per chain run). `Save Videos` takes the frame and video name as iterated inputs; each time the video name changes it closes the previous FFmpeg writer and opens a new one, producing one output file per source video.

---

## Build & Run Commands

```bash
# Install dependencies (requires Node.js >= 18, npm >= 7)
npm install

# TypeScript type check (fast baseline verification)
npm run type-check:js

# Launch the app for manual testing (uses integrated Python backend)
npm start                # any platform — run from repo root
# OR use the convenience scripts:
./run-test.sh            # Mac / Linux
run-test.bat             # Windows (double-click or run in cmd)

# Run in dev mode with hot-reload (requires Python + nodemon)
npm run dev

# Build distributable installer
npm run make

# Run JS tests
npm run test:js

# Run Python tests
npm run test:py
```

Python backend is managed automatically by chaiNNer's integrated Python support — no manual Python setup needed for `npm start`.
Baseline verified: `npm install` + `npm run type-check:js` both pass clean on Node.js v25.8.1.

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
- **Feature code location:**
  - `backend/src/packages/chaiNNer_standard/image/video_frames/load_videos.py` — Load Videos generator node
  - `backend/src/packages/chaiNNer_standard/image/video_frames/save_videos.py` — Save Videos collector node
- **DEVLOG.md:** Updated at the end of every working session (reverse-chronological)

## Tracking File Maintenance

After every meaningful chunk of work — completing a phase, making a design decision, hitting a blocker, or finishing a session — do all three of the following before stopping:

1. **Update `DEVLOG.md`** with what was done, decisions made, problems hit, and next steps.
2. **Update `CLAUDE.md`** if any architectural facts, build commands, conventions, or the do-not-touch list changed.
3. **Commit and push** all three tracking files (and any code changes) to `origin`:
   ```bash
   git add CLAUDE.md DEVLOG.md PLAN.md
   git commit -m "docs: update tracking files — <brief reason>"
   git push origin feature/multi-video-batch
   ```

Never end a session with uncommitted or unpushed tracking file changes.

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
