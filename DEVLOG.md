# DEVLOG — chainner-multivid

Reverse-chronological session log. Most recent entry first.

---

## 2026-05-19 — Phase 1: Codebase Investigation + Phase 2: Plan

**Done:**
- Thoroughly investigated iterator/lineage system, Load Video node, Save Video node, execution engine, frontend trigger, node input UI, and backend API.
- Wrote complete `PLAN.md` proposing frontend batch orchestration approach.

**Key findings:**
- Load Video (`chainner:image:load_video`, `backend/src/packages/chaiNNer_standard/image/video_frames/load_video.py`) takes a single-file path as input 0 — not a directory. Registered as `kind="generator"`.
- Save Video (`chainner:image:save_video`) input 2 is `RelativePathInput("Video Name")` — the output filename stem.
- The `/run` endpoint (`backend/src/server.py:204`) accepts the full chain JSON on each call. Inputs are baked in; no override mechanism exists.
- `DirectoryInput` already exists in both frontend and backend — no new UI primitive needed.
- Single-iterator enforcement: frontend (`src/common/nodes/checkNodeValidity.ts:243`) and backend (`backend/src/process.py:690`). Hard constraint, cannot be worked around.

**Design decision:** Frontend batch orchestration (Option C). Re-run the chain once per video, patching the Load Video node's file path and Save Video's name in the serialized JSON before each `/run` call. No backend changes, no node changes. See `PLAN.md` for full details.

**Next:** Awaiting user approval of `PLAN.md` before Phase 3.

---

## 2026-05-19 — Phase 0: Fork & Scaffold

**Done:**
- Verified `gh` CLI authenticated as `wyghst`
- Forked `chaiNNer-org/chaiNNer` → `wyghst/chainner-multivid` via `gh repo fork`
- Cloned repo; confirmed `origin` → `wyghst/chainner-multivid`, `upstream` → `chaiNNer-org/chaiNNer`
- Created branch `feature/multi-video-batch`
- Created skeleton `CLAUDE.md`, `DEVLOG.md`, `PLAN.md`

**In progress:** Phase 1 investigation, then Phase 2 planning.

**Next:** Explore codebase — iterator/lineage system, Load Video node, Save Video node, execution engine, frontend node input UI.

---

<!-- New entries go above this line -->
