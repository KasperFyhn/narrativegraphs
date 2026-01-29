import React from 'react';

interface AltLabelsDisplayProps {
  altLabels?: string[];
}

export const AltLabelsDisplay: React.FC<AltLabelsDisplayProps> = ({
  altLabels,
}) => {
  if (!altLabels || altLabels.length === 0) return null;

  return (
    <p>
      Alternative Labels:{' '}
      <i>
        {altLabels.slice(0, 10).join(', ')}
        {altLabels.length > 10 ? '...' : ''}
      </i>
    </p>
  );
};
