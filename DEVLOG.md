# DEVLOG — chainner-multivid

Reverse-chronological session log. Most recent entry first.

---

## 2026-05-20 — AMD GPU detection bug fixes + ONNX DirectML clarification

**Problem reported:** RX 9070 XT owner installed HIP SDK drivers but saw no AMD detection prompt in chaiNNer and GPU didn't appear as a PyTorch device option.

**Root causes found:**
1. `_get_amd_gpu_names_windows()` was calling `powershell` by bare name. Electron spawns the Python backend with a stripped PATH that omits `C:\Windows\System32\WindowsPowerShell\v1.0\`, so the subprocess threw `FileNotFoundError` which was silently caught — GPU detection always returned an empty list.
2. The PyTorch package description incorrectly stated "requires Python 3.12" as the reason for CPU-only mode. The real reason is that PyTorch publishes **no Windows ROCm wheels at all** (Linux only) — the Python version is irrelevant.
3. The ONNX package description said "does not support AMD GPUs, in linux" — which is misleading. On Windows without NVIDIA, chaiNNer already installs `onnxruntime-directml`, which gives DirectML GPU acceleration on any DX12 card including AMD.

**Fixes applied:**
- `backend/src/amd.py`: Build absolute path to `powershell.exe` from `%SystemRoot%` env var; added diagnostic logging at WARNING level for failures; added per-pattern match logging.
- `backend/src/packages/chaiNNer_pytorch/__init__.py`: Corrected AMD description — no Windows ROCm wheels exist, HIP SDK alone is insufficient, manual setup guide linked.
- `backend/src/packages/chaiNNer_onnx/__init__.py`: Added Windows/non-NVIDIA branch in description that correctly describes DirectML acceleration on AMD GPUs.
- `backend/src/packages/chaiNNer_onnx/settings.py`: Fixed two bugs: (1) GPU index dropdown was always shown even with no NVIDIA devices, appearing as a blank broken control — now hidden unless `nvidia.is_available`; (2) `get_providers()` default logic always fell through to `CPUExecutionProvider` even when `DmlExecutionProvider` was present (because `"CPUExecutionProvider" in providers` is always true) — priority is now CUDA → Dml → CPU.

**Key finding:** For AMD GPU acceleration in chaiNNer on Windows, the ONNX package (DirectML) is the correct path — not PyTorch. PyTorch GPU acceleration for AMD requires Linux + ROCm. With `onnxruntime-directml` installed, the Execution Provider dropdown now defaults to `Dml` automatically on AMD Windows systems.

---

## 2026-05-20 — v0.25.5-multivid released

All three platform jobs completed successfully (macOS 3m8s, Windows, Ubuntu 3m58s). Release published directly as non-draft — confirms the forge.config.js `draft: false` fix from v0.25.4 is working correctly. All 8 assets present. Marked as Latest.

---

## 2026-05-20 — v0.25.5-multivid: GitHub Actions Node.js 24 upgrade

Updated all 8 workflow files (release, release-test, make, lint-backend, lint-frontend, test-backend, test-frontend, wiki) from `actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v4/v5` to v6 across the board. GitHub is forcing Node.js 20 actions to Node.js 24 on June 2nd, 2026 — this update resolves the deprecation warnings before the deadline. Bumped to 0.25.5-multivid.

---

## 2026-05-20 — v0.25.4-multivid released + forge draft fix

Tagged `v0.25.4-multivid` and pushed to origin. All three platform jobs (macOS, Linux, Windows) completed successfully with all 8 assets uploaded.

Post-release: release was created as a draft because `draft: true` and `prerelease: true` were placed outside the `config` block in `forge.config.js`, causing electron-forge to apply them as top-level publisher defaults. Fixed by moving both properties inside `config` and setting them to `false`. Draft manually published via `gh release edit --draft=false --latest`.

---

## 2026-05-20 — v0.25.4-multivid: AMD ROCm detection + informational UI

**What was done:**
- Added `backend/src/amd.py`: Windows-only AMD GPU detection via PowerShell/WMI. Identifies ROCm-compatible cards (RDNA 2/3/4, Vega 20) by GPU name pattern matching. Exports `amd` singleton, `HIP_SDK_URL`, and `ROCM_PYTORCH_DOCS_URL`.
- Updated `backend/src/packages/chaiNNer_pytorch/__init__.py`: when a ROCm-compatible AMD GPU is detected on Windows, the PyTorch package description and install hint now name the detected GPU, explain that chaiNNer's Python 3.11 environment cannot host AMD's Windows ROCm wheels (which require Python 3.12), and provide direct links to the AMD HIP SDK download page and AMD's PyTorch-on-ROCm setup guide. Falls back to the existing NVIDIA/CPU messaging on all other platforms.
- Bumped version to `0.25.4-multivid`.

**Design decisions:**
- Auto-installing the ROCm PyTorch wheel was ruled out: AMD's Windows ROCm wheels are `cp312`-only and also require 4 additional `rocm_sdk_*` packages — incompatible with chaiNNer's bundled Python 3.11.5. Option B (Python 3.12 upgrade + full auto-install) deferred for a future release.
- Detection is best-effort: WMI query failure returns `AmdInfo.unavailable()` silently, so no startup crash on non-Windows or restricted environments.

**Next steps (deferred):**
- Option B: bump bundled Python to 3.12, add ROCm wheel auto-install when HIP SDK is detected.

---

## 2026-05-20 — Session wrap-up

**Current state:** `main` is clean, all changes committed and pushed. v0.25.3-multivid is publicly released.

**What's shipped in v0.25.3-multivid:**
- `Load Videos` generator node + `Save Videos` collector node (multi-video batch feature)
- `Resize To Side` — Force Even Dimensions toggle (H.264/H.265 compatibility)
- Full dependency refresh (electron-forge 7.11.1, TypeScript 5.9.3, react 18.3.1, chakra-ui 2.10.9, vite 5.4.21)
- All 8 TypeScript 5.9 compatibility fixes
- GitHub Actions updated (checkout@v4, setup-node@v4) + `--legacy-peer-deps` on all `npm ci` steps
- `run-test.bat` auto-pull/install/start for Windows testers

**Known deferred items:**
- Electron upgrade (25.x → 42): security CVEs, but significant effort; hold until Forge v8 stabilizes
- Dart Sass legacy-js-api warnings: cosmetic, no action until Dart Sass 2.0
- 47 npm vulnerabilities: all require major version jumps, same as upstream chaiNNer

**No open action items.**

---

## 2026-05-20 — Merge update/dependencies → main + bump to v0.25.3-multivid

**Done:**
- Merged `update/dependencies` into `main` (no-ff merge commit).
- Bumped version to `0.25.3-multivid` (`package.json` + `package-lock.json`).

**What this release contains over v0.25.2-multivid:**
- All dependency updates (electron-forge 7.11.1, TypeScript 5.9.3, chakra-ui 2.10.9, react 18.3.1, vite 5.4.21, etc.)
- GitHub Actions updated to `actions/checkout@v4` / `actions/setup-node@v4` (all 8 workflow files)
- Compatibility fixes: patch-package removal, rregex pinned to 1.10.11, chakra sub-packages explicitly listed
- `run-test.bat` now auto-pulls, installs with `--legacy-peer-deps`, and handles errors
- 8 TypeScript 5.9 errors resolved in upstream files

**Release attempt 1 failed:** all CI workflows use `npm ci` which doesn't accept the peer-dep conflict. Fixed by adding `--legacy-peer-deps` to every `npm ci` step across all 5 workflow files (`release.yml`, `release-test.yml`, `lint-frontend.yml`, `test-frontend.yml`, `make.yml`). Tag moved forward to include the fix.

**Release succeeded.** All 3 platform builds passed (Windows, macOS universal, Linux). Draft published at:
https://github.com/wyghst/chainner-multivid/releases/tag/v0.25.3-multivid

Assets: `.exe`, `.dmg` (universal), `.deb`, `.rpm`, `.zip` (Linux + Windows).

---

## 2026-05-20 — Fix TypeScript 5.9 errors (branch: update/dependencies)

**All 8 upstream TypeScript errors resolved. `npm run type-check:js` passes clean.**

Fixes applied (all in upstream files — minimal, surgical casts only):

| File | Error | Fix |
|------|-------|-----|
| `src/main/arguments.ts` (×4) | yargs `parseSync()` infers props as `unknown` in TS 5.9 | Added `as string \| undefined` / `as boolean` / `as string` casts at return sites |
| `src/main/squirrel.ts` (×1) | `rmdirSync` with `{recursive}` option removed from `@types/node` | Replaced with `rmSync(p, { recursive: true, force: true })` (modern Node API) |
| `src/renderer/components/node/NodeInputs.tsx` (×1) | `React.memo` return type broadened to `ReactNode` (includes `undefined`) in `@types/react@18.3`, incompatible with `InputItemRenderer` (`JSX.Element \| null`) | Cast memo component `as unknown as InputItemRenderer` |
| `src/renderer/components/NodeDocumentation/NodeDocs.tsx` (×2) | `item.id` typed as `InputId \| OutputId` in union component; `Array.includes` requires exact element type in TS 5.9 | Imported `InputId`/`OutputId`; added targeted casts in each ternary branch |

**Next:** Merge `update/dependencies` → `main`.

---

## 2026-05-19 — Vulnerability audit + compatibility fixes (branch: update/dependencies)

**App status:** working on Windows and Mac after the fixes below.

**Compatibility issues resolved during testing:**
- `patch-package` was erroring on every install because the patch targeted `@electron-forge/plugin-vite@7.4.0/dist/util/package.js` — that file no longer exists in 7.11.1. Patch deleted.
- `rregex@1.11.0` removed the `./lib/rregex.wasm` and `./lib/web` subpath exports that `src/common/rust-regex.ts` imports. Pinned back to `1.10.11` (exact, no `^`).
- `@chakra-ui/react@2.10.9` no longer installs `@chakra-ui/layout`, `@chakra-ui/image`, `@chakra-ui/checkbox`, `@chakra-ui/table`, `@chakra-ui/system` as transitive deps. `chakra-ui-markdown-renderer@4.1.0` imports them directly so they are now listed explicitly in `package.json`.
- `run-test.bat`: added `git pull` step, `call` prefix on all npm commands (missing `call` causes the cmd window to silently exit when npm finishes on Windows), `--no-audit` flag, and error pausing.

**npm audit — 47 vulnerabilities (6 low, 10 moderate, 31 high):**
All require breaking changes to fix — none were resolved by `npm audit fix`. The original upstream chaiNNer repo carries the same vulnerabilities.

| Group | Severity | Fix needed | Status |
|-------|----------|-----------|--------|
| Electron 25.x CVEs (18 issues) | High | Electron 42 | Deferred — dedicated upgrade effort |
| `@electron-forge` chain | Mixed | Forge v8 (alpha) | Deferred — pre-release |
| `@octokit` ReDoS | Moderate | `@octokit/rest` v22 | Deferred — publish-only, not runtime |
| `esbuild` dev server | Moderate | esbuild update | Dev-only, no production impact |
| `tmp` via inquirer | Low | Would downgrade forge | Skip |

Electron CVEs are the most notable but require a targeted Electron upgrade as a separate branch/effort. For a local desktop tool the practical attack surface is narrow.

**Dart Sass legacy-js-api warnings:** cosmetic, emitted by Vite's Sass integration. No action needed until Dart Sass 2.0 is released.

**Known TypeScript errors (8):** surfaced by TypeScript 5.9 being stricter than 5.0. All in upstream files, none in our feature code. To fix before merging to main.

**Next:** Fix the 8 TS type errors, then merge `update/dependencies` → `main`.

---

## 2026-05-19 — Dependency updates (branch: update/dependencies)

**Approach:** patch/minor bumps only. Major version jumps skipped (React 19, Chakra 3, Electron 42, uuid 14, prettier 3, stylelint 17, use-context-selector 2, etc.) — each would require targeted code changes and testing.

**npm packages updated:**
- `electron` 25.8.4 → 25.9.8 (within v25, via `npm update`)
- `@electron-forge/*` 7.4.0 → 7.11.1 (all packages, manually — were pinned)
- `typescript` 5.0.4 → 5.9.3 (latest v5)
- `vite` 5.4.6 → 5.4.21
- `vitest` 1.4.0 → 1.6.1
- `react` / `react-dom` 18.1.0 → 18.3.1 (stayed in v18)
- `@chakra-ui/react` 2.8.2 → 2.10.9 (stayed in v2)
- `@emotion/react` / `@emotion/styled` → latest v11
- `@types/react` / `@types/react-dom` → latest v18
- `use-context-selector` 1.4.0 → 1.4.4
- All other patch/minor deps via `npm update --legacy-peer-deps`

**GitHub Actions updated:**
- `actions/checkout@v3` → `actions/checkout@v4` (all 8 workflow files)
- `actions/setup-node@v3` → `actions/setup-node@v4` (all applicable files)

**Peer dependency notes:**
- `eslint-plugin-prefer-arrow-functions` pinned to `3.1.4` (v3.9.1 requires eslint 9; project stays on eslint 8)
- `--legacy-peer-deps` used throughout because `use-context-selector@1.4.4` pulls in a `react-native` optional peer that wants `@types/react@^19`

**Python backend packages:** left as-is. chaiNNer uses its own package installer; versions are pinned by the upstream team for inter-package compatibility. PyTorch is already at 2.7.0 (current). Updating these without testing the ML pipeline is too risky.

**Known type errors after update (8 total — all in upstream files, not our code):**
TypeScript 5.9 is stricter than 5.0 and caught pre-existing issues:
- `src/main/arguments.ts` (4 errors) — `unknown` type narrowing now required
- `src/main/squirrel.ts` (1 error) — function arity changed in a dependency
- `src/renderer/components/node/NodeInputs.tsx` (1 error) — `memo` type tightened in `@types/react@18.3`
- `src/renderer/components/NodeDocumentation/NodeDocs.tsx` (2 errors) — `InputId`/`OutputId` union narrowing

These need to be fixed before merging to main. Diagnose per-error during testing.

**Next:** Test the app, fix the 8 type errors, then merge `update/dependencies` → `main`.

---

## 2026-05-19 — Release v0.25.2-multivid

**Done:**
- Bumped version to `0.25.2-multivid` in `package.json` / `package-lock.json`.
- Merged `feature/multi-video-batch` into `main` via PR #1.
- Tagged `v0.25.2-multivid` and triggered the inherited `release.yml` GitHub Actions workflow.

**Two bugs fixed before the release build succeeded:**

1. **Wrong publish target** — `forge.config.js` used `packageJson.author.name` / `packageJson.productName` to build the GitHub repo path, which resolved to `chaiNNer-org/chaiNNer` (the upstream). The `GITHUB_TOKEN` has no write access there. Fixed by hardcoding `owner: 'wyghst', name: 'chainner-multivid'` in the publisher config.

2. **Token write permission** — even after fixing the repo path, the token was blocked. Required two steps: (a) add `permissions: contents: write` to the release workflow job, and (b) set the repo's Actions workflow permissions to "Read and write" under Settings → Actions → General.

**How to release in future:** bump version with `npm version <ver> --no-git-tag-version`, commit, push to `main`, then `git tag v<ver> && git push origin v<ver>`. The workflow fires automatically.

---

## 2026-05-19 — Feature complete + merge to main

**Done:**
- Confirmed Resize To Side "Force Even Dimensions" toggle works end-to-end.
- Full Phase 4 verification passed: Load Videos → Resize To Side → Save Videos chain produces one output file per source video with correct audio, FPS, directory, and even-pixel dimensions.
- Merged `feature/multi-video-batch` into `main` via PR #1.

**Feature summary (all shipped):**
- `Load Videos` generator node — scans a folder, iterates all frames from all videos as one flat stream; outputs Frame, FrameIndex, VideoIndex, VideoName, FPS, AudioStream (iterated), TotalVideos, Directory (static)
- `Save Videos` collector node — detects VideoName change to open a new FFmpeg writer per source video; carries audio and native FPS through
- `Resize To Side` — new "Force Even Dimensions" toggle snaps output to nearest even pixel, satisfying H.264/H.265 libx265

**Status:** Complete. No open items.

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
