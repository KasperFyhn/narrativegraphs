import React from 'react';

interface AltLabelsDisplayProps {
  altLabels?: string[];
}

export const AltLabelsDisplay: React.FC<AltLabelsDisplayProps> = ({
  altLabels,
}) => {
  if (!altLabels || altLabels.length === 0) return null;

  return (
    <div>
      Alternative Labels:
      <ul>
        {altLabels.map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
    </div>
  );
};
