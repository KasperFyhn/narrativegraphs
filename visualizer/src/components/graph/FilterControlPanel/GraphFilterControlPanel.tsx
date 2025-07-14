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

export const GraphFilterControlPanel: React.FC = () => {
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
      <div className={'flex-container'}>
        <span className={'option-span'}>Limit nodes:&nbsp;</span>
        <SubmittedNumberInput
          startValue={filter.limitNodes}
          onSubmit={setNodeLimit}
        />
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Node Frequency:&nbsp;</span>
        <NodeFrequencySlider />
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Limit edges:&nbsp;</span>
        <SubmittedNumberInput
          startValue={filter.limitEdges}
          onSubmit={setEdgeLimit}
        />
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Edge Frequency:&nbsp;</span>
        <EdgeFrequencySlider />
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Search nodes:</span>
        <SubmittedTextInput onSubmit={setLabelSearch} />
      </div>
      {dataBounds.categories && (
        <div className={'flex-container'}>
          <details>
            <summary>
              <span className={'option-span'}>Categories</span>
            </summary>
            <div>
              {dataBounds.categories.map((category) => (
                <div key={category}>
                  <input
                    type="checkbox"
                    onChange={(event) => {
                      console.log('Changed:', category);
                      console.log('Event:', event);
                    }}
                  />
                  {category}
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
      {dataBounds.earliestDate && dataBounds.latestDate && (
        <div className={'flex-container'}>
          <span className={'option-span'}>Date Filter:</span>
          <SubmittedDataRangeInput
            min={dataBounds.earliestDate}
            max={dataBounds.latestDate}
            onSubmit={setDateRange}
          />
        </div>
      )}
      <div className={'flex-container flex-container--vertical'}>
        <EntityWhitelistControl />
        <EntityBlacklistControl />
      </div>
    </div>
  );
};
