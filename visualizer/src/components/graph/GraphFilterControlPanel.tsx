import React, { useEffect, useState } from 'react';
import './graph.css';
import LogarithmicRangeSlider from '../common/LogarithmicRangeSlider';
import { DataBounds, GraphFilter } from '../../types/graphFilter';
import { ClipLoader } from 'react-spinners';
import { useServiceContext } from '../../contexts/ServiceContext';

interface GraphFilterControlPanelProps {
  graphFilter: GraphFilter;
  setGraphFilter: React.Dispatch<React.SetStateAction<GraphFilter>>;
}

export const GraphFilterControlPanel: React.FC<
  GraphFilterControlPanelProps
> = ({ graphFilter, setGraphFilter }: GraphFilterControlPanelProps) => {
  const { graphService } = useServiceContext();

  const [dataBounds, setDataBounds] = useState<DataBounds>();
  useEffect(() => {
    graphService.getDataBounds().then((r: DataBounds) => setDataBounds(r));
  }, [graphService]);

  const [limitNodes, setLimitNodes] = useState<number>(graphFilter.limitNodes);
  const [limitEdges, setLimitEdges] = useState<number>(graphFilter.limitEdges);
  const [search, setSearch] = useState<string | undefined>(
    graphFilter.labelSearch,
  );

  const setMinAndMaxNodeFrequency = (min: number, max: number): void => {
    if (
      min === graphFilter.minimumNodeFrequency &&
      max === graphFilter.maximumNodeFrequency
    ) {
      return;
    }
    setGraphFilter({
      ...graphFilter,
      minimumNodeFrequency: min,
      maximumNodeFrequency: max,
    });
  };
  const setMinAndMaxEdgeFrequency = (min: number, max: number): void => {
    if (
      min === graphFilter.minimumEdgeFrequency &&
      max === graphFilter.maximumEdgeFrequency
    ) {
      return;
    }
    setGraphFilter({
      ...graphFilter,
      minimumEdgeFrequency: min,
      maximumEdgeFrequency: max,
    });
  };

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
        <span className={'option-span'}>Only supernodes:</span>
        <input
          type={'checkbox'}
          checked={graphFilter.onlySupernodes || false}
          onChange={(event) =>
            setGraphFilter((prevState) => ({
              ...prevState,
              onlySupernodes: event.target.checked,
            }))
          }
        />
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Limit nodes:&nbsp;</span>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setGraphFilter((prevState) => ({
              ...prevState,
              limitNodes: limitNodes,
            }));
          }}
        >
          <input
            min={1}
            max={999}
            type={'number'}
            value={limitNodes}
            onChange={(event) => {
              setLimitNodes(Number(event.target.value));
            }}
          />
        </form>
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Node Frequency:&nbsp;</span>
        <div style={{ width: '250px' }}>
          <LogarithmicRangeSlider
            onChange={(e) => {
              setMinAndMaxNodeFrequency(e.minValue, e.maxValue);
            }}
            min={dataBounds.minimumPossibleNodeFrequency}
            minValue={
              graphFilter.minimumNodeFrequency ||
              dataBounds.minimumPossibleNodeFrequency
            }
            maxValue={
              graphFilter.maximumNodeFrequency ||
              dataBounds.maximumPossibleNodeFrequency
            }
            max={dataBounds.maximumPossibleNodeFrequency}
            style={{ border: 'none', boxShadow: 'none', padding: '15px 10px' }}
          />
        </div>
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Limit edges:&nbsp;</span>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setGraphFilter((prevState) => ({
              ...prevState,
              limitEdges: limitEdges,
            }));
          }}
        >
          <input
            min={1}
            max={999}
            type={'number'}
            value={limitEdges}
            onChange={(event) => {
              setLimitEdges(Number(event.target.value));
            }}
          />
        </form>
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Edge Frequency:&nbsp;</span>
        <div style={{ width: '250px' }}>
          <LogarithmicRangeSlider
            onChange={(e) => {
              setMinAndMaxEdgeFrequency(e.minValue, e.maxValue);
            }}
            min={dataBounds.minimumPossibleEdgeFrequency}
            minValue={
              graphFilter.minimumEdgeFrequency ||
              dataBounds.minimumPossibleEdgeFrequency
            }
            maxValue={
              graphFilter.maximumEdgeFrequency ||
              dataBounds.maximumPossibleEdgeFrequency
            }
            max={dataBounds.maximumPossibleEdgeFrequency}
            style={{ border: 'none', boxShadow: 'none', padding: '15px 10px' }}
          ></LogarithmicRangeSlider>
        </div>
      </div>
      <div className={'flex-container'}>
        <span className={'option-span'}>Search nodes:</span>
        <form
          style={{ margin: 0 }}
          onSubmit={(event) => {
            event.preventDefault();
            setGraphFilter((prevState) => ({
              ...prevState,
              labelSearch: search || undefined,
            }));
          }}
        >
          <input
            type={'search'}
            value={search || ''}
            onChange={(event) => {
              const value = event.target.value;
              setSearch(value);
              if (value === '') {
                setGraphFilter((prevState) => ({
                  ...prevState,
                  labelSearch: undefined,
                }));
              }
            }}
          />
        </form>
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
          <div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const startDateStr = formData.get('startDate') as string;
                const endDateStr = formData.get('endDate') as string;

                const startDate = startDateStr ? new Date(startDateStr) : null;
                const endDate = endDateStr ? new Date(endDateStr) : null;

                if (
                  startDate &&
                  endDate &&
                  dataBounds.earliestDate &&
                  dataBounds?.latestDate
                ) {
                  // Clamp both dates to bounds
                  const clampedStartDate =
                    startDate < dataBounds.earliestDate
                      ? dataBounds.earliestDate
                      : startDate > dataBounds.latestDate
                        ? dataBounds.latestDate
                        : startDate;

                  const clampedEndDate =
                    endDate < dataBounds.earliestDate
                      ? dataBounds.earliestDate
                      : endDate > dataBounds.latestDate
                        ? dataBounds.latestDate
                        : endDate;

                  // Ensure start <= end
                  const finalStartDate =
                    clampedStartDate > clampedEndDate
                      ? clampedEndDate
                      : clampedStartDate;
                  const finalEndDate =
                    clampedEndDate < finalStartDate
                      ? finalStartDate
                      : clampedEndDate;

                  setGraphFilter({
                    ...graphFilter,
                    earliestDate: finalStartDate,
                    latestDate: finalEndDate,
                  });
                }
              }}
            >
              <input
                type="date"
                name="startDate"
                min={dataBounds.earliestDate.toLocaleDateString('en-CA')}
                max={dataBounds.latestDate.toLocaleDateString('en-CA')}
                defaultValue={dataBounds.earliestDate.toLocaleDateString(
                  'en-CA',
                )}
              />
              <input
                type="date"
                name="endDate"
                min={dataBounds.earliestDate.toLocaleDateString('en-CA')}
                max={dataBounds.latestDate.toLocaleDateString('en-CA')}
                defaultValue={dataBounds.latestDate.toLocaleDateString('en-CA')}
              />
              <button type="submit">Apply Filter</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
