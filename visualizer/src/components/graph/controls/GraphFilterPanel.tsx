import React from 'react';
import '../graph.css';
import { Stack, Group, Button, Text } from '@mantine/core';
import { ClipLoader } from 'react-spinners';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { SubmittedNumberInput } from '../../common/userinput/SubmittedNumberInput';
import {
  EdgeFrequencySlider,
  NodeFrequencySlider,
} from './subcomponents/FrequencySlider';
import { SubmittedDataRangeInput } from '../../common/userinput/SubmittedDateRangeInput';
import { EntityBlacklistControl } from './subcomponents/EntityListControl';
import { CategorySelector } from './subcomponents/CategorySelector';

export const GraphFilterPanel: React.FC = () => {
  const {
    dataBounds,
    filter,
    setNodeLimit,
    setEdgeLimit,
    setDateRange,
    historyControls,
  } = useGraphQuery();

  if (!dataBounds) {
    return (
      <Group>
        <ClipLoader loading={true} />
      </Group>
    );
  }

  return (
    <Stack gap="md">
      <Group>
        <Button
          size="xs"
          onClick={historyControls.undo}
          disabled={!historyControls.canUndo}
        >
          Undo
        </Button>
        <Button
          size="xs"
          onClick={historyControls.redo}
          disabled={!historyControls.canRedo}
        >
          Redo
        </Button>
      </Group>

      <SubmittedNumberInput
        label="Limit Nodes"
        startValue={filter.limitNodes}
        onSubmit={setNodeLimit}
      />
      <SubmittedNumberInput
        label="Limit Edges"
        startValue={filter.limitEdges}
        onSubmit={setEdgeLimit}
      />

      <Stack gap={4}>
        <Text size="sm">Node Frequency</Text>
        <NodeFrequencySlider />
      </Stack>
      <Stack gap={4}>
        <Text size="sm">Edge Frequency</Text>
        <EdgeFrequencySlider />
      </Stack>

      {dataBounds.categories && (
        <Stack gap={4}>
          <Text size="sm">Categories</Text>
          <CategorySelector />
        </Stack>
      )}

      {dataBounds.earliestDate && dataBounds.latestDate && (
        <SubmittedDataRangeInput
          label="Date Range"
          min={dataBounds.earliestDate}
          max={dataBounds.latestDate}
          onSubmit={setDateRange}
        />
      )}

      <EntityBlacklistControl />
    </Stack>
  );
};
