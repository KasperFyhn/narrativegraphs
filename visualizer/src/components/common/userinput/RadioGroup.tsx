import React from 'react';

interface RadioGroupProps {
  name: string;
  options: readonly string[];
  value: string;
  onChange: (value: string) => void;
  formatLabel?: (option: string) => string;
  direction?: 'row' | 'column';
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  options,
  value,
  onChange,
  formatLabel = (option) => option.charAt(0).toUpperCase() + option.slice(1),
  direction = 'column',
}: RadioGroupProps) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: direction,
        alignItems: 'flex-end',
      }}
    >
      {options.map((option) => (
        <label key={option}>
          {formatLabel(option)}
          <input
            type="radio"
            name={name}
            checked={value === option}
            onChange={() => onChange(option)}
          />
        </label>
      ))}
    </div>
  );
};
