import React from 'react';
import { Radio, Group, Stack } from '@mantine/core';

interface RadioGroupProps {
  name: string;
  options: readonly string[];
  value: string;
  onChange: (value: string) => void;
  formatLabel?: (option: string) => string;
  direction?: 'row' | 'column';
  label?: string;
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  options,
  value,
  onChange,
  formatLabel = (option) => option.charAt(0).toUpperCase() + option.slice(1),
  direction = 'column',
  label,
}: RadioGroupProps) => {
  const radios = options.map((option) => (
    <Radio key={option} value={option} label={formatLabel(option)} />
  ));

  return (
    <Radio.Group name={name} value={value} onChange={onChange} label={label}>
      {direction === 'row' ? (
        <Group mt={label ? 'xs' : 0} gap="sm">
          {radios}
        </Group>
      ) : (
        <Stack mt={label ? 'xs' : 0} gap="xs">
          {radios}
        </Stack>
      )}
    </Radio.Group>
  );
};
