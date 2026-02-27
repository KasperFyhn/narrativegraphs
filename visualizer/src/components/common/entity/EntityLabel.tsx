import React from 'react';
import { Badge } from '@mantine/core';
import { useSelectionContext } from '../../../contexts/SelectionContext';

export interface EntityLabelProps {
  id: string | number;
  label: string;
}

export const EntityLabel: React.FC<EntityLabelProps> = ({ id, label }) => {
  const { getEntityColor } = useSelectionContext();
  return (
    <Badge
      radius="sm"
      style={{
        backgroundColor: getEntityColor(id),
        color: 'black',
        textTransform: 'none',
        fontWeight: 500,
      }}
    >
      {label}
    </Badge>
  );
};
