import React from 'react';
import { Text } from '@mantine/core';

interface AltLabelsDisplayProps {
  altLabels?: string[];
}

export const AltLabelsDisplay: React.FC<AltLabelsDisplayProps> = ({
  altLabels,
}) => {
  if (!altLabels || altLabels.length === 0) return null;

  return (
    <Text size="sm">
      <Text span fw={500}>
        Alternative Labels:
      </Text>{' '}
      <Text span fs="italic">
        {altLabels.slice(0, 10).join(', ')}
        {altLabels.length > 10 ? '...' : ''}
      </Text>
    </Text>
  );
};
