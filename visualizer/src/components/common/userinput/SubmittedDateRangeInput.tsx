import React, { useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';

export interface SubmittedDataRangeInputProps {
  min: Date;
  initStartDate?: Date;
  initEndDate?: Date;
  max: Date;
  onSubmit: (start: Date, end: Date) => void;
  label?: string;
}

export const SubmittedDataRangeInput: React.FC<
  SubmittedDataRangeInputProps
> = ({
  min,
  initStartDate,
  initEndDate,
  max,
  onSubmit,
  label,
}: SubmittedDataRangeInputProps) => {
  const [range, setRange] = useState<[Date | null, Date | null]>([
    initStartDate ?? min,
    initEndDate ?? max,
  ]);

  return (
    <Stack gap="xs">
      <DatePickerInput
        type="range"
        label={label}
        minDate={min}
        maxDate={max}
        value={range}
        onChange={(v) => setRange(v as [Date | null, Date | null])}
        clearable={false}
        size="xs"
      />
      <Button
        size="xs"
        onClick={() => {
          const [start, end] = range;
          if (start && end) onSubmit(start, end);
        }}
      >
        Apply
      </Button>
    </Stack>
  );
};
