import React from 'react';
import { TextStats } from '../../../types/graph';

export interface Stat {
  name: string;
  value: string;
}

interface StatsDisplayProps extends React.PropsWithChildren {
  stats: TextStats;
  extra?: Stat[];
}

export const StatsDisplay: React.FC<StatsDisplayProps> = ({ stats, extra }) => {
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
      {extra &&
        extra.length > 0 &&
        extra?.map((stat) => (
          <p key={stat.name}>
            {stat.name}: {stat.value}
          </p>
        ))}
    </>
  );
};
