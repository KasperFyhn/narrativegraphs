import React from 'react';
import { useSelectionContext } from '../../../contexts/SelectionContext';

export interface EntityLabelProps {
  id: string | number;
  label: string;
}

export const EntityLabel: React.FC<EntityLabelProps> = ({
  id,
  label,
}: EntityLabelProps) => {
  const { getEntityColor } = useSelectionContext();
  return (
    <span
      key={id}
      style={{
        backgroundColor: getEntityColor(id),
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '0.9em',
        fontWeight: 500,
      }}
    >
      {label}
    </span>
  );
};
