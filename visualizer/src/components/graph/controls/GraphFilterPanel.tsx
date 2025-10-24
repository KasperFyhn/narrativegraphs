import React from 'react';
import '../graph.css';
import { ClipLoader } from 'react-spinners';
import { useGraphFilter } from '../../../hooks/useGraphFilter';
import { SubmittedNumberInput } from '../../common/input/SubmittedNumberInput';
import { SubmittedTextInput } from '../../common/input/SubmittedTextInput';
import { EdgeFrequencySlider, NodeFrequencySlider } from './FrequencySlider';
import { SubmittedDataRangeInput } from '../../common/input/SubmittedDateRangeInput';
import {
  EntityBlacklistControl,
  EntityWhitelistControl,
} from './EntityListControl';
import { CategorySelector } from './CategorySelector';
import { NamedInput } from '../../common/input/NamedInput';

export const GraphFilterPanel: React.FC = () => {
  const {
    dataBounds,
    filter,
    setNodeLimit,
    setEdgeLimit,
    setLabelSearch,
    setDateRange,
    historyControls,
  } = useGraphFilter();

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
      <NamedInput name={'Search'}>
        <SubmittedTextInput onSubmit={setLabelSearch} />
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
      <div className={'flex-container flex-container--vertical'}>
        <EntityWhitelistControl />
        <EntityBlacklistControl />
      </div>
    </div>
  );
};
