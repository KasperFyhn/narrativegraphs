import React from 'react';
import { Badge } from '@mantine/core';
import { useSelectionContext } from '../../../contexts/SelectionContext';

export interface EntityLabelProps {
  id: string | number;
  label: string;
  rightSection?: React.ReactNode;
}

export const EntityLabel: React.FC<EntityLabelProps> = ({
  id,
  label,
  rightSection,
}) => {
  const { getEntityColor } = useSelectionContext();
  return (
    <Badge
      radius="sm"
      rightSection={rightSection}
      tt="none"
      fw={500}
      style={{
        backgroundColor: getEntityColor(id),
        color: 'black',
        height: 'auto',
        paddingTop: 3,
        paddingBottom: 3,
      }}
    >
      {label}
    </Badge>
  );
};
