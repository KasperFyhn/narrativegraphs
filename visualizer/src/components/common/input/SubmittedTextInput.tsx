import React, { useState } from 'react';

export interface SubmittedTextInputProps {
  startValue?: string;
  onSubmit: (value: string) => void;
}

export const SubmittedTextInput: React.FC<SubmittedTextInputProps> = ({
  startValue,
  onSubmit,
}: SubmittedTextInputProps) => {
  const [value, setValue] = useState(startValue || '');

  return (
    <form
      style={{ margin: 0 }}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(value);
      }}
    >
      <input
        type={'search'}
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
    </form>
  );
};
