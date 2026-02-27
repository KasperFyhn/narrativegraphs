import LogarithmicRangeSlider from '../../../common/userinput/LogarithmicRangeSlider';
import MultiRangeSlider from 'multi-range-slider-react';

import React from 'react';
import { useGraphQuery } from '../../../../hooks/useGraphQuery';

export interface FrequencySliderProps {
  min: number;
  max: number;
  minValue: number;
  maxValue: number;
  onChange: (values: { minValue: number; maxValue: number }) => void;
}

const RangeSlider: React.FC<FrequencySliderProps> = (
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
  const { dataBounds, filter, setNodeFrequencyRange } = useGraphQuery();
  return (
    <RangeSlider
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
  const { dataBounds, filter, setEdgeFrequencyRange } = useGraphQuery();
  return (
    <RangeSlider
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

export const OrdinalTimeFrequencySlider: React.FC = () => {
  const { dataBounds, filter, setOrdinalTimeRange } = useGraphQuery();
  if (
    dataBounds.earliestOrdinalTime === undefined ||
    dataBounds.latestOrdinalTime === undefined
  ) {
    return <p>NOT POSSIBLE</p>;
  }

  return (
    <div style={{ minWidth: '150px' }}>
      <MultiRangeSlider
        onChange={(e: { minValue: number; maxValue: number }) =>
          setOrdinalTimeRange(e.minValue, e.maxValue)
        }
        min={dataBounds.earliestOrdinalTime}
        max={dataBounds.latestOrdinalTime}
        minValue={filter.earliestOrdinalTime || dataBounds.earliestOrdinalTime}
        maxValue={filter.latestOrdinalTime || dataBounds.latestOrdinalTime}
        barInnerColor={'transparent'}
        ruler={false}
        style={{ border: 'none', boxShadow: 'none', padding: '15px 10px' }}
      />
    </div>
  );
};
