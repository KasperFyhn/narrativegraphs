import React, { useState } from 'react';

export interface SubmittedNumberInputProps {
  startValue: number;
  onSubmit: (value: number) => void;
}

export const SubmittedNumberInput: React.FC<SubmittedNumberInputProps> = ({
  startValue,
  onSubmit,
}: SubmittedNumberInputProps) => {
  const [value, setValue] = useState(startValue);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(value);
      }}
    >
      <input
        min={1}
        max={999}
        type={'number'}
        value={value}
        onChange={(event) => {
          setValue(Number(event.target.value));
        }}
      />
    </form>
  );
};
