import React from 'react';
import '../graph.css';
import { ClipLoader } from 'react-spinners';
import { useGraphQuery } from '../../../hooks/useGraphQuery';
import { SubmittedNumberInput } from '../../common/userinput/SubmittedNumberInput';
import {
  EdgeFrequencySlider,
  NodeFrequencySlider,
} from './subcomponents/FrequencySlider';
import { SubmittedDataRangeInput } from '../../common/userinput/SubmittedDateRangeInput';
import { EntityBlacklistControl } from './subcomponents/EntityListControl';
import { CategorySelector } from './subcomponents/CategorySelector';
import { NamedInput } from '../../common/userinput/NamedInput';

export const GraphFilterPanel: React.FC = () => {
  const {
    dataBounds,
    filter,
    setNodeLimit,
    setEdgeLimit,
    setDateRange,
    historyControls,
  } = useGraphQuery();

  if (!dataBounds) {
    return (
      <div className={'flex-container'}>
        <ClipLoader loading={true} />
      </div>
    );
  }

  return (
    <div className={'flex-container flex-container--vertical'}>
      <div className={'flex-container'}>
        <button
          onClick={historyControls.undo}
          disabled={!historyControls.canUndo}
        >
          Undo
        </button>
        <button
          onClick={historyControls.redo}
          disabled={!historyControls.canRedo}
        >
          Redo
        </button>
      </div>
      <NamedInput name={'Limit Nodes'}>
        <SubmittedNumberInput
          startValue={filter.limitNodes}
          onSubmit={setNodeLimit}
        />
      </NamedInput>
      <NamedInput name={'Limit edges'}>
        <SubmittedNumberInput
          startValue={filter.limitEdges}
          onSubmit={setEdgeLimit}
        />
      </NamedInput>
      <NamedInput name={'Node Frequency'}>
        <NodeFrequencySlider />
      </NamedInput>
      <NamedInput name={'Edge Frequency'}>
        <EdgeFrequencySlider />
      </NamedInput>
      {dataBounds.categories && (
        <NamedInput name={'Categories'}>
          <CategorySelector />
        </NamedInput>
      )}
      {dataBounds.earliestDate && dataBounds.latestDate && (
        <NamedInput name={'Date Range'}>
          <SubmittedDataRangeInput
            min={dataBounds.earliestDate}
            max={dataBounds.latestDate}
            onSubmit={setDateRange}
          />
        </NamedInput>
      )}
      <EntityBlacklistControl />
    </div>
  );
};
