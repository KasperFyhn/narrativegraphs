import React from 'react';
import { Table } from '@mantine/core';
import { TextStats } from '../../../types/graph';

export interface Stat {
  name: string;
  value: string;
}

interface StatsDisplayProps {
  stats: TextStats;
  extra?: Stat[];
}

export const StatsDisplay: React.FC<StatsDisplayProps> = ({ stats, extra }) => {
  const rows: Stat[] = [
    { name: 'Frequency', value: String(stats.frequency) },
    { name: 'Document hits', value: String(stats.docFrequency) },
    ...(stats.firstOccurrence
      ? [{ name: 'Earliest date', value: stats.firstOccurrence.toString() }]
      : []),
    ...(stats.lastOccurrence
      ? [{ name: 'Latest date', value: stats.lastOccurrence.toString() }]
      : []),
    ...(stats.firstOccurrenceOrdinal
      ? [
          {
            name: 'Earliest time',
            value: stats.firstOccurrenceOrdinal.toString(),
          },
        ]
      : []),
    ...(stats.lastOccurrenceOrdinal
      ? [{ name: 'Latest time', value: stats.lastOccurrenceOrdinal.toString() }]
      : []),
    ...(extra ?? []),
  ];

  return (
    <Table withRowBorders={false} fz="sm">
      <Table.Tbody>
        {rows.map((row) => (
          <Table.Tr key={row.name}>
            <Table.Td fw={500}>{row.name}</Table.Td>
            <Table.Td>{row.value}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
};
