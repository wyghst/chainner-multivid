import { basename, extname, join } from 'path';
import { memo, useCallback, useRef, useState } from 'react';
import { useReactFlow } from 'reactflow';
import { createContext, useContext } from 'use-context-selector';
import { BackendJsonNode } from '../../common/common-types';
import { optimizeChain } from '../../common/nodes/optimize';
import { toBackendJson } from '../../common/nodes/toBackendJson';
import { useSettings } from '../hooks/useSettings';
import { ipcRenderer } from '../safeIpc';
import { AlertBoxContext, AlertType } from './AlertBoxContext';
import { BackendContext } from './BackendContext';

const LOAD_VIDEO_SCHEMA_ID = 'chainner:image:load_video';
const SAVE_VIDEO_SCHEMA_ID = 'chainner:image:save_video';

// Must match VideoFileInput filetypes in file_inputs.py
const VIDEO_EXTENSIONS = new Set([
    '.mp4', '.h264', '.hevc', '.webm', '.avi', '.gif',
    '.mov', '.mkv', '.flv', '.m4v', '.avs',
]);

export interface BatchError {
    file: string;
    error: string;
}

export interface BatchSummary {
    processed: number;
    failed: BatchError[];
}

export interface BatchExecutionContextValue {
    batchFolder: string | undefined;
    setBatchFolder: (folder: string | undefined) => void;
    isBatchRunning: boolean;
    batchProgress: { current: number; total: number } | undefined;
    lastSummary: BatchSummary | undefined;
    clearSummary: () => void;
    runBatch: () => Promise<void>;
    cancelBatch: () => void;
}

export const BatchExecutionContext = createContext<BatchExecutionContextValue>({
    batchFolder: undefined,
    setBatchFolder: () => {},
    isBatchRunning: false,
    batchProgress: undefined,
    lastSummary: undefined,
    clearSummary: () => {},
    runBatch: async () => {},
    cancelBatch: () => {},
});

const patchForVideo = (nodes: BackendJsonNode[], videoPath: string): BackendJsonNode[] => {
    const stem = basename(videoPath, extname(videoPath));

    return nodes.map((node): BackendJsonNode => {
        if (node.schemaId === LOAD_VIDEO_SCHEMA_ID) {
            const inputs = [...node.inputs];
            inputs[0] = { type: 'value', value: videoPath };
            return { ...node, inputs };
        }
        if (node.schemaId === SAVE_VIDEO_SCHEMA_ID) {
            const inputs = [...node.inputs];
            // Only patch static values — leave edge connections alone
            if (inputs[2]?.type === 'value') {
                inputs[2] = { type: 'value', value: stem };
            }
            return { ...node, inputs };
        }
        return node;
    });
};

// eslint-disable-next-line @typescript-eslint/ban-types
export const BatchExecutionProvider = memo(({ children }: React.PropsWithChildren<{}>) => {
    const { backend, schemata, passthrough } = useContext(BackendContext);
    const { packageSettings, experimentalFeatures } = useSettings();
    const { sendAlert, sendToast } = useContext(AlertBoxContext);
    const { getNodes, getEdges } = useReactFlow();

    const [batchFolder, setBatchFolder] = useState<string | undefined>();
    const [isBatchRunning, setIsBatchRunning] = useState(false);
    const [batchProgress, setBatchProgress] = useState<{ current: number; total: number } | undefined>();
    const [lastSummary, setLastSummary] = useState<BatchSummary | undefined>();

    const cancelRef = useRef(false);

    const cancelBatch = useCallback(() => {
        cancelRef.current = true;
    }, []);

    const clearSummary = useCallback(() => setLastSummary(undefined), []);

    const runBatch = useCallback(async () => {
        if (!batchFolder) {
            sendAlert({ type: AlertType.ERROR, message: 'Select a batch folder first.' });
            return;
        }

        // Optimize chain once — validates it and trims dead nodes
        const { nodes: optNodes, edges: optEdges, report } = optimizeChain(
            getNodes(),
            getEdges(),
            schemata,
            passthrough
        );

        if (optNodes.length === 0) {
            const message = report.removedSideEffectFree > 0
                ? 'There are no nodes that have an effect.'
                : report.removedDisabled > 0
                    ? 'All nodes are disabled.'
                    : 'There are no nodes to run.';
            sendAlert({ type: AlertType.ERROR, message });
            return;
        }

        const loadVideoNodes = optNodes.filter(n => n.data.schemaId === LOAD_VIDEO_SCHEMA_ID);
        if (loadVideoNodes.length === 0) {
            sendAlert({ type: AlertType.ERROR, message: 'Batch mode requires a "Load Video" node in the chain.' });
            return;
        }
        if (loadVideoNodes.length > 1) {
            sendAlert({ type: AlertType.ERROR, message: 'Batch mode requires exactly one "Load Video" node. Found multiple.' });
            return;
        }

        // Scan folder for video files
        let allFiles: string[];
        try {
            allFiles = await ipcRenderer.invoke('fs-readdir', batchFolder);
        } catch (err) {
            sendAlert({ type: AlertType.ERROR, message: `Could not read folder: ${String(err)}` });
            return;
        }

        const videoFiles = allFiles
            .filter(f => VIDEO_EXTENSIONS.has(extname(f).toLowerCase()))
            .sort();

        if (videoFiles.length === 0) {
            sendAlert({ type: AlertType.ERROR, message: 'No video files found in the selected folder.' });
            return;
        }

        // Serialize the base chain once — we'll patch it per video
        const baseJson = toBackendJson(optNodes, optEdges, schemata);

        setIsBatchRunning(true);
        setLastSummary(undefined);
        cancelRef.current = false;

        const firstPassFailures: string[] = [];
        let processed = 0;

        const runOne = async (filename: string): Promise<boolean> => {
            const videoPath = join(batchFolder, filename);
            const patched = patchForVideo(baseJson, videoPath);
            try {
                const response = await backend.run({
                    data: patched,
                    options: packageSettings,
                    sendBroadcastData: true,
                    useExperimentalFeatures: experimentalFeatures,
                });
                return response.type === 'success';
            } catch {
                return false;
            }
        };

        // Main pass
        for (let i = 0; i < videoFiles.length; i++) {
            if (cancelRef.current) break;
            setBatchProgress({ current: i + 1, total: videoFiles.length });
            const ok = await runOne(videoFiles[i]);
            if (ok) {
                processed++;
            } else {
                firstPassFailures.push(videoFiles[i]);
            }
        }

        // Retry pass
        const finalFailures: BatchError[] = [];
        if (!cancelRef.current && firstPassFailures.length > 0) {
            sendToast({
                status: 'info',
                description: `Retrying ${firstPassFailures.length} failed video${firstPassFailures.length !== 1 ? 's' : ''}…`,
                id: 'batch-retry',
                duration: 3000,
                position: 'bottom',
            });

            for (const file of firstPassFailures) {
                if (cancelRef.current) break;
                const ok = await runOne(file);
                if (ok) {
                    processed++;
                } else {
                    finalFailures.push({ file, error: 'Failed after retry — see execution log.' });
                }
            }
        }

        setLastSummary({ processed, failed: finalFailures });
        setIsBatchRunning(false);
        setBatchProgress(undefined);
    }, [
        batchFolder,
        getNodes,
        getEdges,
        schemata,
        passthrough,
        backend,
        packageSettings,
        experimentalFeatures,
        sendAlert,
        sendToast,
    ]);

    return (
        <BatchExecutionContext.Provider value={{
            batchFolder,
            setBatchFolder,
            isBatchRunning,
            batchProgress,
            lastSummary,
            clearSummary,
            runBatch,
            cancelBatch,
        }}>
            {children}
        </BatchExecutionContext.Provider>
    );
});
