import React from 'react';
import { Text } from '@mantine/core';

export type Categories = Record<string, string[]>;

interface CategoriesDisplayProps {
  categories: Categories;
}

const capitalize = (s: string): string =>
  s.charAt(0).toUpperCase() + s.slice(1);

export const CategoriesDisplay: React.FC<CategoriesDisplayProps> = ({
  categories,
}) => {
  const entries = Object.entries(categories);

  if (entries.length === 0) return null;

  return (
    <>
      {entries.map(([name, values]) => (
        <Text key={name} size="sm">
          <Text span fw={500}>
            {capitalize(name)}:
          </Text>{' '}
          {values.join(', ')}
        </Text>
      ))}
    </>
  );
};
