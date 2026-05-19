# DEVLOG — chainner-multivid

Reverse-chronological session log. Most recent entry first.

---

## 2026-05-19 — Force Even Dimensions option on Resize To Side

**Done:**
- Added `BoolInput("Force Even Dimensions", default=False)` to `resize_to_side.py` (input id=5).
- Updated navi `image_type` expression to apply `round(d / 2) * 2` when `Input5` is true.
- Updated `resize_to_side_node` function signature with `force_even: bool` parameter.
- Added even-snap logic in body: `out_w = max(out_w - out_w % 2, 2)` and same for height.
- When enabled, both width and height are snapped **down** to the nearest even pixel (minimum 2), satisfying H.264/H.265 libx265 requirements.

**Next:** Phase 4 end-to-end test with all connections wired.

---

## 2026-05-19 — Audio passthrough + Directory output

**Done:**
- **Load Videos**: added Audio Stream (iterated output 5, per-video ffmpeg stream), Total Videos moved to output 6, Directory added as output 7 (non-iterated, the scanned folder path).
- **Save Videos**: added Audio Stream (iterated input id=15, optional), Audio Settings (non-iterated id=10), wired both through `_open_writer` to the FFmpeg Writer. GIF format forces audio=None. Updated `IteratorInputInfo` to `[0, 1, 14, 15]` and `on_iterate` unpacks a 4-tuple `(frame, video_name, fps, audio)`.

**How to wire the new outputs:**
- `Load Videos: Audio Stream` → `Save Videos: Audio Stream` — audio carried through per video
- `Load Videos: Directory` → `Save Videos: Directory` — outputs land in same folder as inputs
- `Load Videos: FPS` → `Save Videos: FPS` — native FPS per video

**Deferred:** Auto frame size with even horizontal pixels — likely needs a new node; user chose to hold off.

**Next:** Phase 4 — full end-to-end test with all connections wired.

---

## 2026-05-19 — End of session

**Current state:** All code committed and pushed. `Load Videos` + `Save Videos` nodes registered correctly after DirectoryInput bug fix.

**What's on the branch (`feature/multi-video-batch`):**
- `backend/.../video_frames/load_videos.py` — Load Videos generator node (fixed)
- `backend/.../video_frames/save_videos.py` — Save Videos collector node
- `run-test.bat` / `run-test.sh` — one-click test launchers
- `CLAUDE.md`, `DEVLOG.md`, `PLAN.md` — all current

**Next session:** Phase 4 — launch app, confirm both nodes appear under Video Frames, wire up Load Videos → Save Videos with Video Name connected, run with 3+ videos, verify one output file per input video.

---

## 2026-05-19 — Bug fix: Load Videos node not appearing

**Problem:** `Load Videos` node was silently failing to register — not visible in the node selector on Mac or Windows.

**Root cause:** `load_videos.py` called `DirectoryInput(primary_input=True)`. `DirectoryInput.__init__` does not accept `primary_input` (only `FileInput` subclasses do). This raised `TypeError` at import time, caught silently by `load_nodes()`, so the node never registered.

**Fix:** Changed to `DirectoryInput()` (no argument). One-line diff.

**Next:** Re-run the app and confirm both Load Videos and Save Videos nodes appear under Video Frames.

---

## 2026-05-19 — End of session (node-based pivot complete)

**Current state:** `load_videos.py` + `save_videos.py` implemented and pushed. Frontend header approach fully reverted. TypeScript type-check clean. Python nodes awaiting Phase 4 manual test.

**What's on the branch (`feature/multi-video-batch`):**
- `backend/.../video_frames/load_videos.py` — Load Videos generator node
- `backend/.../video_frames/save_videos.py` — Save Videos collector node
- `run-test.bat` / `run-test.sh` — one-click test launchers
- `CLAUDE.md`, `DEVLOG.md`, `PLAN.md` — all current

**Next session:** Launch app via `run-test.bat`, add Load Videos + Save Videos to a chain, connect Video Name output to Video Name input, run with 3+ test videos, confirm one output file per input video.

---

## 2026-05-19 — Phase 3 Revision: Node-based batch approach

**Done:**
- **Reverted** frontend header approach: deleted `BatchExecutionContext.tsx`, `BatchControls.tsx`; reverted `main.tsx` and `Header.tsx` to pre-batch state. TypeScript type check passes clean.
- **Created `backend/src/packages/chaiNNer_standard/image/video_frames/load_videos.py`**: `Load Videos` generator node. Takes a DirectoryInput, scans for video files (`.mp4 .mkv .avi .mov .webm .gif .m4v .wmv`), iterates all frames from all videos as one flat sequence. Iterated outputs: Frame, FrameIndex, VideoIndex, VideoName, FPS. Non-iterated: TotalVideos. Auto-discovered by chaiNNer's node loader.
- **Created `backend/src/packages/chaiNNer_standard/image/video_frames/save_videos.py`**: `Save Videos` collector node. Iterated inputs: Frame + VideoName. Non-iterated: Directory, FPS, format/encoder settings (same options as Save Video, reusing Writer/enums via import). Detects VideoName change → closes previous FFmpeg writer, opens a new one. Returns count of videos saved.
- Updated CLAUDE.md, PLAN.md.

**Why the change:** User requested nodes (like "Load Images" for batch images) rather than a header toolbar. Node-based approach is cleaner: the chain topology itself expresses the batch intent, no UI-layer orchestration needed.

**Verification:** `npm run type-check:js` passes clean. Python nodes untested (need app launch for Phase 4).

**Next:** Phase 4 — launch app via `run-test.bat`, place Load Videos + Save Videos nodes in a chain, run batch with 3+ videos, confirm separate output files.

---

## 2026-05-19 — Pull request opened

**Done:**
- Opened PR #1: https://github.com/wyghst/chainner-multivid/pull/1
- All feature work is visible on GitHub — navigate to the PR or switch to the `feature/multi-video-batch` branch to browse the diff.
- Note: GitHub defaults to showing `main`; the feature branch is separate by design until Phase 4 testing is complete.

---

## 2026-05-19 — End of session status

**Current state:** Phases 0–3 complete and pushed. Awaiting Phase 4 manual testing.

**What's on the branch (`feature/multi-video-batch`):**
- `run-test.bat` / `run-test.sh` — one-click test launchers (Windows / Mac)
- `src/renderer/contexts/BatchExecutionContext.tsx` — batch orchestration
- `src/renderer/components/Header/BatchControls.tsx` — batch UI in header
- `CLAUDE.md`, `DEVLOG.md`, `PLAN.md` — all current

**Uncommitted:** Only CRLF/LF snapshot normalization from running tests on Windows — not committed (no content change).

**Next session:** Run Phase 4 verification (open app via `run-test.bat`, test batch folder run with 3+ videos, test error/retry/summary flow, confirm single-video regression is clean), then Phase 5 finalize.

---

## 2026-05-19 — Test launcher scripts

**Done:**
- Created `run-test.bat` (Windows) and `run-test.sh` (Mac/Linux).
- Both scripts: check for Node.js, run `npm install` if `node_modules` is missing, then launch `npm start` (Electron with integrated Python backend — no manual Python setup required).
- Updated `CLAUDE.md` with launch instructions.

**Next:** Manual Phase 4 verification using these scripts.

---

## 2026-05-19 — Phase 3: Implementation

**Done:**
- Created `src/renderer/contexts/BatchExecutionContext.tsx`: batch orchestration context. Provides folder state, `runBatch()`, `cancelBatch()`, progress, and summary. Uses `optimizeChain` + `toBackendJson` to build chain JSON, then patches Load Video input 0 (file path) and Save Video input 2 (name stem) per video before each `backend.run()` call.
- Created `src/renderer/components/Header/BatchControls.tsx`: compact header UI with folder picker button, batch run / cancel button with live N/M count, and a completion modal listing any persistent failures.
- Modified `src/renderer/main.tsx`: added `BatchExecutionProvider` inside `ExecutionProvider`.
- Modified `src/renderer/components/Header/Header.tsx`: added `BatchControls` next to `ExecutionButtons`.

**Verification so far:**
- `npm run type-check:js` passes clean.
- `npx vitest run` — 96/96 tests pass.

**Decisions made:**
- Used `createContext` / `useContext` from `use-context-selector` to match existing codebase pattern.
- `cancelBatch()` sets a ref flag; current video finishes before the loop exits (clean shutdown).
- Snapshot file line-ending changes from running tests on Windows not committed (whitespace only).

**Next:** Phase 4 — manual verification with real test videos.

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
