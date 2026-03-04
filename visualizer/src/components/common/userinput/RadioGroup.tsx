import React from 'react';
import { SegmentedControl, Stack, Text } from '@mantine/core';

interface RadioGroupProps {
  name?: string;
  options: readonly string[];
  value: string;
  onChange: (value: string) => void;
  formatLabel?: (option: string) => string;
  label?: string;
}

const defaultFormatLabel = (option: string): string =>
  option
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

export const RadioGroup: React.FC<RadioGroupProps> = ({
  options,
  value,
  onChange,
  formatLabel = defaultFormatLabel,
  label,
}) => {
  const data = options.map((o) => ({ value: o, label: formatLabel(o) }));

  return (
    <Stack gap={4}>
      {label && (
        <Text size="sm" fw={500}>
          {label}
        </Text>
      )}
      <SegmentedControl data={data} value={value} onChange={onChange} />
    </Stack>
  );
};
