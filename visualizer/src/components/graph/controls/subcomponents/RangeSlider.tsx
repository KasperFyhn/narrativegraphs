import LogarithmicRangeSlider from '../../../common/userinput/LogarithmicRangeSlider';
import React, { useEffect, useState } from 'react';
import { RangeSlider, Stack, Text } from '@mantine/core';
import { useGraphQuery } from '../../../../hooks/useGraphQuery';

export const NodeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setNodeFrequencyRange } = useGraphQuery();
  const minValue =
    filter.minimumNodeFrequency || dataBounds.minimumPossibleNodeFrequency;
  const maxValue =
    filter.maximumNodeFrequency || dataBounds.maximumPossibleNodeFrequency;
  return (
    <Stack gap={4}>
      <Text size="xs" c="dimmed">
        {minValue} – {maxValue}
      </Text>
      <LogarithmicRangeSlider
        onChange={(e) => setNodeFrequencyRange(e.minValue, e.maxValue)}
        min={dataBounds.minimumPossibleNodeFrequency}
        minValue={minValue}
        maxValue={maxValue}
        max={dataBounds.maximumPossibleNodeFrequency}
      />
    </Stack>
  );
};

export const EdgeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setEdgeFrequencyRange } = useGraphQuery();
  const minValue =
    filter.minimumEdgeFrequency || dataBounds.minimumPossibleEdgeFrequency;
  const maxValue =
    filter.maximumEdgeFrequency || dataBounds.maximumPossibleEdgeFrequency;
  return (
    <Stack gap={4}>
      <Text size="xs" c="dimmed">
        {minValue} – {maxValue}
      </Text>
      <LogarithmicRangeSlider
        onChange={(e) => setEdgeFrequencyRange(e.minValue, e.maxValue)}
        min={dataBounds.minimumPossibleEdgeFrequency}
        minValue={minValue}
        maxValue={maxValue}
        max={dataBounds.maximumPossibleEdgeFrequency}
      />
    </Stack>
  );
};

export const OrdinalTimeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setOrdinalTimeRange } = useGraphQuery();

  const min = dataBounds.earliestOrdinalTime;
  const max = dataBounds.latestOrdinalTime;

  const [value, setValue] = useState<[number, number]>([
    filter.earliestOrdinalTime ?? min ?? 0,
    filter.latestOrdinalTime ?? max ?? 0,
  ]);

  useEffect(() => {
    setValue([
      filter.earliestOrdinalTime ?? min ?? 0,
      filter.latestOrdinalTime ?? max ?? 0,
    ]);
  }, [filter.earliestOrdinalTime, filter.latestOrdinalTime, min, max]);

  if (min === undefined || max === undefined) {
    return null;
  }

  return (
    <Stack gap={4}>
      <Text size="xs" c="dimmed">
        {value[0]} – {value[1]}
      </Text>
      <RangeSlider
        min={min}
        max={max}
        value={value}
        onChange={setValue}
        onChangeEnd={([lo, hi]) => setOrdinalTimeRange(lo, hi)}
        size="sm"
        style={{ minWidth: 140 }}
      />
    </Stack>
  );
};
