# PLAN.md — Multi-Video Batch Feature

> Status: **PROPOSED — awaiting user approval**
> Branch: `feature/multi-video-batch`
> Written: 2026-05-19, after Phase 1 investigation

---

## 1. Architectural Summary (from investigation)

Key findings that constrain design choices:

- **Load Video** (`chainner:image:load_video`) takes `VideoFileInput` — a single-file picker — as input 0. Registered as `kind="generator"` (iterator over frames). File: `backend/src/packages/chaiNNer_standard/image/video_frames/load_video.py`.
- **Save Video** (`chainner:image:save_video`) input 2 is `RelativePathInput("Video Name")` — the output filename stem, normally typed by the user. File: `backend/src/packages/chaiNNer_standard/image/video_frames/save_video.py`.
- **`/run` endpoint** (`backend/src/server.py:204`) receives the full chain JSON each call. Node inputs are baked in as either static values `{"type": "value", "value": ...}` or edges `{"type": "edge", ...}`. There is no override mechanism — the chain is re-submitted fresh each time.
- **The single-iterator constraint** is enforced at both frontend (connection-time + pre-run check, `src/common/nodes/checkNodeValidity.ts:243`) and backend (nested generators raise `ValueError`, `backend/src/process.py:690`). It cannot be worked around without breaking the architecture.
- **`DirectoryInput`** already exists in both frontend (`src/renderer/components/inputs/DirectoryInput.tsx`) and backend (`backend/src/nodes/properties/inputs/file_inputs.py:121`). The IPC call `ipcRenderer.invoke('dir-select', ...)` is already wired.
- **Frontend serializes + POSTs** the chain via `ExecutionContext.tsx:runNodes()` → `backend.run()` → `POST /run`. The chain JSON is built in `toBackendJson()` immediately before posting.

---

## 2. Folder Input Mechanism — Recommendation

### Options considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A. New "Load Video Folder" generator node** | A node that iterates over video files in a folder | ❌ Would be a second generator in the same lineage — violates the single-iterator rule |
| **B. Directory toggle on existing Load Video node** | Add a mode to Load Video that accepts a folder | ❌ Would need to iterate over videos AND frames (nested iteration) — same violation |
| **C. Frontend batch orchestration** | Frontend re-runs the existing chain once per video, patching the file path in the JSON before each `/run` call | ✅ Clean: one iterator per run, no node changes, fully surgical |

### Chosen: Option C — Frontend batch orchestration

**How it works:**
1. User selects a folder via a new "Batch Folder" control in the run toolbar.
2. Frontend scans the folder for video files (matching the same extensions Load Video supports: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.gif`).
3. For each video in the queue:
   a. Frontend calls `toBackendJson()` to serialize the current chain normally.
   b. Finds the Load Video node(s) in the JSON by `schemaId === "chainner:image:load_video"`.
   c. **Patches** that node's input 0 (file path) from its stored value to the current video's absolute path.
   d. Optionally patches Save Video nodes' input 2 (Video Name) to the current video's filename stem (see §4).
   e. POSTs the patched JSON to `/run` and awaits completion.
4. After all videos are done (including error handling), shows a summary.

**Why this is safe for existing single-video behavior:**
- Nothing changes in the chain's node definitions, inputs, or connections.
- The single-video "Run" button (F5 or green button) is untouched. It continues to serialize and POST the chain exactly as before.
- Batch mode is a separate code path that only activates when a batch folder is set.

**Constraint:** Batch mode requires exactly one `chainner:image:load_video` node in the chain. If there are zero or more than one, the UI shows an error before starting.

---

## 3. Orchestration — How the Chain Re-runs Per Video

### Queue sequencing

```
batch folder selected
        ↓
scan folder → sorted list of video file paths
        ↓
for each path in queue:
    patch chain JSON (Load Video input 0 → path)
    patch chain JSON (Save Video input 2 → stem, if applicable)
    await backend.run(patchedJson)
    if error → push to failedQueue, log error, continue
        ↓
retry pass: for each path in failedQueue:
    repeat same patched run
    if error again → push to finalFailures
        ↓
show summary report (processed count, failed list with error messages)
```

### File scanning

```ts
// extensions matching VideoFileInput in load_video.py
const VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.gif', '.m4v', '.wmv'];
```

Files are sorted lexicographically (the natural order users expect). Subdirectories are not scanned (no recursion) unless the user asks for it later.

### Awaiting completion

The `/run` endpoint is async — it returns when execution completes or errors. The frontend's `backend.run()` call already awaits the response (`src/renderer/contexts/ExecutionContext.tsx:481`). Batch mode wraps the same call and `await`s it in a loop.

### SSE events during batch

Existing SSE events (`node-start`, `node-progress`, `node-finish`) continue to fire per-video, so the existing progress UI works naturally for each video in the batch. A new batch-level progress indicator shows "Video 3 of 12".

---

## 4. Save-Node Filename Propagation

### The problem

Save Video input 2 is "Video Name" — the output filename stem. In single-video mode the user types this once. In batch mode it must update per video or all outputs would overwrite each other.

### Solution: patch Save Video input 2 before each `/run`

When building the patched JSON for each video:

1. Find all `"chainner:image:save_video"` nodes in the JSON.
2. For each, check input 2:
   - If `{"type": "value", "value": <string>}` (static, user-typed) → replace value with `stem(currentVideoPath)` (the filename without extension).
   - If `{"type": "edge", ...}` (connected to another node) → leave unchanged. The user has deliberately wired this; respect their decision.
3. This ensures the output is named after the source video with no extra configuration.

### Opt-out

A checkbox "Auto-name outputs from source filename" (on by default) controls this behavior. When unchecked, Save Video input 2 is not patched — but the user is warned that outputs may overwrite each other.

---

## 5. Error Handling

### Per-video failure (skip → defer → retry-once → summary)

```ts
interface BatchError {
    path: string;
    attempt: 1 | 2;
    message: string;
}
```

**Main pass:**
- Catch any error/rejection from `backend.run()`.
- Log `{path, attempt: 1, message: error.message}`.
- Add path to `failedQueue`.
- Continue to next video immediately.

**Retry pass (after main queue exhausted):**
- For each path in `failedQueue`:
  - Run exactly once more with the same patched JSON.
  - If succeeds → removed from failures.
  - If fails again → add to `finalFailures` with `attempt: 2`.

**Summary report:**
- Modal dialog showing:
  - Total processed: N
  - Succeeded: N
  - Failed after retry: list of `{filename, errorMessage}`
- Option to save the summary as a text file.
- No failure is silent.

### Interrupted batch

If the user clicks "Stop" during a batch, the current video's `/run` is aborted (via the existing `backend.abort()`) and the batch loop exits cleanly. Remaining videos are not processed. A partial summary is shown.

---

## 6. Regression Safety

### How single-video behavior is preserved

- The existing `runNodes()` function in `ExecutionContext.tsx` is **not modified**. The F5 key and Run button call it unchanged.
- Batch mode has its own `runBatch()` function that calls `backend.run()` independently.
- The Load Video node, Save Video node, and all other nodes are **not modified**.
- The backend `/run` endpoint is **not modified**.

### Verification checks (Phase 4)

1. Open a chain with a single Load Video → Save Video, set a specific file path, run normally → verify the output is produced and named correctly (same as before the feature).
2. Load an existing `.chn` chain file → verify it loads and runs without changes.
3. Run batch mode with 3+ test videos → verify each is processed with a distinct output filename.
4. Deliberately corrupt one test video → verify it is skipped, the retry pass runs once more on it, and the final summary lists it as failed with an error message.
5. Verify no "nested iterator" error is thrown during batch (each run is a fresh single-iterator chain execution).

---

## 7. File-by-File Change List

### New files

| File | Purpose |
|------|---------|
| `src/renderer/contexts/BatchExecutionContext.tsx` | Batch state: folder path, queue, current video, error tracking, retry logic |
| `src/renderer/components/node/BatchRunControls.tsx` | UI: folder picker, batch run button, per-video progress, summary modal |

### Modified files

| File | What changes |
|------|-------------|
| `src/renderer/App.tsx` (or wherever the top toolbar is assembled) | Mount `BatchRunControls` alongside existing run controls |
| `src/renderer/contexts/ExecutionContext.tsx` | Export `runNodes` or the underlying `backend.run` call so `BatchExecutionContext` can reuse it without duplication |

### Explicitly NOT modified

- `backend/src/packages/chaiNNer_standard/image/video_frames/load_video.py`
- `backend/src/packages/chaiNNer_standard/image/video_frames/save_video.py`
- `backend/src/server.py`
- `backend/src/process.py`
- `src/common/nodes/` (all node validation logic)
- Any `.chn` chain files

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| `/run` does not accept a second call while a run is in progress (server.py:210 rejects it) | `await` each run before starting the next — the sequential queue naturally prevents this |
| Patching JSON breaks some validation in the backend | The patched value is a valid absolute path string, same type as what a user would enter; backend validation is type-based, not value-based |
| Multiple Load Video nodes in chain | Pre-flight check: abort batch with a clear error message before the first `/run` |
| Save Video input 2 is an edge connection | Detect and skip patching; warn user that filenames may repeat if the connected node returns a fixed value |
| Large folder (100+ videos) + user wants to cancel mid-run | Each `/run` is awaited; "Stop" aborts the current video and exits the loop; partial summary shown |
| User has `Use limit` enabled on Load Video, limiting frames per video | This is the user's intentional setting; batch mode does not touch inputs 1 or 2 of Load Video |

---

## 9. Open Questions for User

1. **Subfolder scanning?** Should batch mode scan subdirectories recursively, or only the top-level folder? (Current proposal: top-level only.)
2. **Save directory per video?** Currently Save Video's output directory (input 1) is not patched — all videos go to the same output folder. Is that the desired behavior?
3. **Sort order?** Lexicographic (alphabetical) file ordering within the queue — is that acceptable?

---

> **Waiting for user approval before Phase 3 begins.**
