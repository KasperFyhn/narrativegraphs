import React, { useState } from 'react';
import { Box, TextInput, ActionIcon } from '@mantine/core';
import { Search } from 'lucide-react';

export interface SubmittedTextInputProps {
  startValue?: string;
  onSubmit: (value: string) => void;
}

export const SubmittedTextInput: React.FC<SubmittedTextInputProps> = ({
  startValue,
  onSubmit,
}: SubmittedTextInputProps) => {
  const [value, setValue] = useState(startValue ?? '');

  return (
    <Box
      component="form"
      m={0}
      onSubmit={(e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(value);
      }}
    >
      <TextInput
        value={value}
        autoFocus
        rightSection={
          <ActionIcon type="submit" variant="subtle" size="sm">
            <Search size={14} />
          </ActionIcon>
        }
        onChange={(e) => {
          const newValue = e.target.value;
          setValue(newValue);
          if (newValue === '') onSubmit('');
        }}
      />
    </Box>
  );
};
