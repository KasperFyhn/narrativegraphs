import React, { useState } from 'react';
import { NumberInput } from '@mantine/core';

export interface SubmittedNumberInputProps {
  startValue: number;
  onSubmit: (value: number) => void;
  label?: string;
}

export const SubmittedNumberInput: React.FC<SubmittedNumberInputProps> = ({
  startValue,
  onSubmit,
  label,
}: SubmittedNumberInputProps) => {
  const [value, setValue] = useState<number | string>(startValue);

  const submit = (): void => {
    if (typeof value === 'number') onSubmit(value);
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <NumberInput
        label={label}
        min={1}
        max={999}
        value={value}
        onChange={setValue}
        onBlur={submit}
        w={80}
      />
    </form>
  );
};
