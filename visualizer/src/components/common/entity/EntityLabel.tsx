import React from 'react';

export interface EntityLabelProps {
  id: string | number;
  label: string;
}

export const EntityLabel: React.FC<EntityLabelProps> = ({
  label,
}: EntityLabelProps) => {
  return (
    <span
      style={{
        borderRadius: '3px',
        padding: '2px',
        backgroundColor: 'cyan',
        overflow: 'hidden',
      }}
    >
      {label}
    </span>
  );
};
