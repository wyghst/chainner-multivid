import {
    Alert,
    AlertDescription,
    AlertIcon,
    AlertTitle,
    Box,
    Button,
    Divider,
    HStack,
    IconButton,
    Modal,
    ModalBody,
    ModalCloseButton,
    ModalContent,
    ModalFooter,
    ModalHeader,
    ModalOverlay,
    Text,
    Tooltip,
    VStack,
    useDisclosure,
} from '@chakra-ui/react';
import { memo, useEffect } from 'react';
import { useContext } from 'use-context-selector';
import { BsFolderFill } from 'react-icons/bs';
import { MdOutlineVideoLibrary } from 'react-icons/md';
import { log } from '../../../common/log';
import { ipcRenderer } from '../../safeIpc';
import { BatchExecutionContext } from '../../contexts/BatchExecutionContext';
import { ExecutionContext, ExecutionStatus } from '../../contexts/ExecutionContext';

const SummaryModal = memo(() => {
    const { lastSummary, clearSummary } = useContext(BatchExecutionContext);
    const { isOpen, onOpen, onClose } = useDisclosure();

    useEffect(() => {
        if (lastSummary) onOpen();
    }, [lastSummary, onOpen]);

    const handleClose = () => {
        clearSummary();
        onClose();
    };

    if (!lastSummary) return null;

    const { processed, failed } = lastSummary;
    const allGood = failed.length === 0;

    return (
        <Modal
            isOpen={isOpen}
            onClose={handleClose}
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Batch Complete</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                    <VStack
                        align="stretch"
                        spacing={3}
                    >
                        <Alert status={allGood ? 'success' : 'warning'}>
                            <AlertIcon />
                            <Box>
                                <AlertTitle>
                                    {allGood ? 'All videos processed' : 'Some videos failed'}
                                </AlertTitle>
                                <AlertDescription>
                                    {processed} video{processed !== 1 ? 's' : ''} processed
                                    successfully.
                                    {failed.length > 0 && (
                                        <> {failed.length} failed after retry.</>
                                    )}
                                </AlertDescription>
                            </Box>
                        </Alert>

                        {failed.length > 0 && (
                            <VStack
                                align="stretch"
                                maxH="200px"
                                overflowY="auto"
                                spacing={1}
                            >
                                {failed.map(({ file, error }) => (
                                    <Box key={file}>
                                        <Text
                                            fontSize="sm"
                                            fontWeight="bold"
                                        >
                                            {file}
                                        </Text>
                                        <Text
                                            color="gray.400"
                                            fontSize="xs"
                                        >
                                            {error}
                                        </Text>
                                    </Box>
                                ))}
                            </VStack>
                        )}
                    </VStack>
                </ModalBody>
                <ModalFooter>
                    <Button onClick={handleClose}>Close</Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
});

export const BatchControls = memo(() => {
    const {
        batchFolder,
        setBatchFolder,
        isBatchRunning,
        batchProgress,
        runBatch,
        cancelBatch,
    } = useContext(BatchExecutionContext);

    const { status } = useContext(ExecutionContext);
    const isExecuting = status !== ExecutionStatus.READY;

    const onPickFolder = async () => {
        const { canceled, filePaths } = await ipcRenderer.invoke(
            'dir-select',
            batchFolder ?? ''
        );
        if (!canceled && filePaths[0]) {
            setBatchFolder(filePaths[0]);
        }
    };

    const folderLabel = batchFolder
        ? batchFolder.split(/[\\/]/).pop() ?? batchFolder
        : 'Select folder…';

    return (
        <>
            <HStack spacing={1}>
                <Divider
                    borderColor="whiteAlpha.300"
                    h="28px"
                    orientation="vertical"
                />

                <Tooltip
                    borderRadius={8}
                    label={batchFolder ?? 'Pick a folder of videos to batch-process'}
                    px={2}
                    py={1}
                >
                    <Button
                        leftIcon={<BsFolderFill />}
                        maxW="180px"
                        size="sm"
                        variant="ghost"
                        // eslint-disable-next-line @typescript-eslint/no-misused-promises
                        onClick={onPickFolder}
                    >
                        <Text
                            isTruncated
                            maxW="120px"
                        >
                            {folderLabel}
                        </Text>
                    </Button>
                </Tooltip>

                {isBatchRunning ? (
                    <Tooltip
                        borderRadius={8}
                        label="Cancel batch after current video finishes"
                        px={2}
                        py={1}
                    >
                        <Button
                            colorScheme="orange"
                            size="sm"
                            variant="outline"
                            onClick={cancelBatch}
                        >
                            {batchProgress
                                ? `${batchProgress.current}/${batchProgress.total}`
                                : 'Cancel'}
                        </Button>
                    </Tooltip>
                ) : (
                    <Tooltip
                        borderRadius={8}
                        label={
                            !batchFolder
                                ? 'Select a folder first'
                                : isExecuting
                                    ? 'Wait for current run to finish'
                                    : 'Run chain on every video in the folder'
                        }
                        px={2}
                        py={1}
                    >
                        <IconButton
                            aria-label="Batch run"
                            colorScheme="purple"
                            icon={<MdOutlineVideoLibrary />}
                            isDisabled={!batchFolder || isExecuting}
                            size="sm"
                            variant="outline"
                            onClick={() => {
                                runBatch().catch(log.error);
                            }}
                        />
                    </Tooltip>
                )}
            </HStack>

            <SummaryModal />
        </>
    );
});
