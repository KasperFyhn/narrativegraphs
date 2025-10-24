import LogarithmicRangeSlider from '../../common/input/LogarithmicRangeSlider';
import React from 'react';
import { useGraphFilter } from '../../../hooks/useGraphFilter';

export interface FrequencySliderProps {
  min: number;
  max: number;
  minValue: number;
  maxValue: number;
  onChange: (values: { minValue: number; maxValue: number }) => void;
}

const FrequencySlider: React.FC<FrequencySliderProps> = (
  props: FrequencySliderProps,
) => {
  return (
    <div style={{ minWidth: '150px' }}>
      <LogarithmicRangeSlider
        {...props}
        style={{ border: 'none', boxShadow: 'none', padding: '15px 10px' }}
      />
    </div>
  );
};

export const NodeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setNodeFrequencyRange } = useGraphFilter();
  return (
    <FrequencySlider
      onChange={(e) => {
        setNodeFrequencyRange(e.minValue, e.maxValue);
      }}
      min={dataBounds.minimumPossibleNodeFrequency}
      minValue={
        filter.minimumNodeFrequency || dataBounds.minimumPossibleNodeFrequency
      }
      maxValue={
        filter.maximumNodeFrequency || dataBounds.maximumPossibleNodeFrequency
      }
      max={dataBounds.maximumPossibleNodeFrequency}
    />
  );
};

export const EdgeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setEdgeFrequencyRange } = useGraphFilter();
  return (
    <FrequencySlider
      onChange={(e) => {
        setEdgeFrequencyRange(e.minValue, e.maxValue);
      }}
      min={dataBounds.minimumPossibleEdgeFrequency}
      minValue={
        filter.minimumEdgeFrequency || dataBounds.minimumPossibleEdgeFrequency
      }
      maxValue={
        filter.maximumEdgeFrequency || dataBounds.maximumPossibleEdgeFrequency
      }
      max={dataBounds.maximumPossibleEdgeFrequency}
    />
  );
};
