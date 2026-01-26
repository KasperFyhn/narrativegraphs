import React from 'react';
import { TextStats } from '../../../types/graph';

interface StatsDisplayProps {
  stats: TextStats;
}

export const StatsDisplay: React.FC<StatsDisplayProps> = ({ stats }) => {
  return (
    <>
      <p>Frequency: {stats.frequency}</p>
      <p>Document hits: {stats.docFrequency}</p>
      {stats.firstOccurrence && (
        <p>Earliest date: {stats.firstOccurrence.toString()}</p>
      )}
      {stats.lastOccurrence && (
        <p>Latest date: {stats.lastOccurrence.toString()}</p>
      )}
    </>
  );
};
