import { Box, Center, HStack } from '@chakra-ui/react';
import { memo } from 'react';
import { DependencyManagerButton } from '../DependencyManagerButton';
import { NodeDocumentationButton } from '../NodeDocumentation/NodeDocumentationModal';
import { SettingsButton } from '../SettingsModal';
import { SystemStats } from '../SystemStats';
import { AppInfo } from './AppInfo';
import { BatchControls } from './BatchControls';
import { ExecutionButtons } from './ExecutionButtons';
import { KoFiButton } from './KoFiButton';

export const Header = memo(() => {
    return (
        <Box
            alignItems="center"
            bg="var(--header-bg)"
            borderRadius="lg"
            borderWidth="0"
            display="flex"
            gap={4}
            h="56px"
            px={2}
            w="full"
        >
            <Box>
                <AppInfo />
            </Box>
            <Center flexGrow="1">
                <HStack spacing={2}>
                    <ExecutionButtons />
                    <BatchControls />
                </HStack>
            </Center>
            <HStack>
                <SystemStats />
                <NodeDocumentationButton />
                <DependencyManagerButton />
                <KoFiButton />
                <SettingsButton />
            </HStack>
        </Box>
    );
});
