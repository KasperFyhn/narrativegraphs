import React, {useEffect, useState} from "react";
import "./graph.css";
import LogarithmicRangeSlider from "../common/LogarithmicRangeSlider";
import {DataBounds, GraphFilter} from "../types/graphfilter";
import {useServiceContext} from "../service/ServiceContextProvider";
import {ClipLoader} from "react-spinners";

interface GraphFilterControlPanelProps {
  graphFilter: GraphFilter;
  setGraphFilter: React.Dispatch<React.SetStateAction<GraphFilter>>;
}

export const GraphFilterControlPanel = ({
                                          graphFilter,
                                          setGraphFilter,
                                        }: GraphFilterControlPanelProps) => {
  const {graphService} = useServiceContext();

  const [dataBounds, setDataBounds] = useState<DataBounds>();
  useEffect(() => {
    graphService.getDataBounds().then((r) => setDataBounds(r));
  }, [graphService]);

  const [limitNodes, setLimitNodes] = useState<number>(graphFilter.limitNodes);
  const [limitEdges, setLimitEdges] = useState<number>(graphFilter.limitEdges);
  const [search, setSearch] = useState<string | undefined>(
    graphFilter.labelSearch,
  );

  const setMinAndMaxNodeFrequency = (min: number, max: number) => {
    if (min === graphFilter.minimumNodeFrequency && max === graphFilter.maximumNodeFrequency) {
      return;
    }
    setGraphFilter({
      ...graphFilter,
      minimumNodeFrequency: min,
      maximumNodeFrequency: max,
    });
  };
  const setMinAndMaxEdgeFrequency = (min: number, max: number) => {
    if (min === graphFilter.minimumEdgeFrequency && max === graphFilter.maximumEdgeFrequency) {
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
      <div className={"flex-container"}>
        <ClipLoader loading={true}/>
      </div>
    );
  }

  return (
    <div className={"flex-container flex-container--vertical"}>
      <div className={"flex-container"}>
        <span className={"option-span"}>Only supernodes:</span>
        <input
          type={"checkbox"}
          checked={graphFilter.onlySupernodes || false}
          onChange={(event) =>
            setGraphFilter((prevState) => ({
              ...prevState,
              onlySupernodes: event.target.checked,
            }))
          }
        />
      </div>
      <div className={"flex-container"}>
        <span className={"option-span"}>Limit nodes:&nbsp;</span>
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
            type={"number"}
            value={limitNodes}
            onChange={(event) => {
              setLimitNodes(Number(event.target.value));
            }}
          />
        </form>
      </div>
      <div className={"flex-container"}>
        <span className={"option-span"}>Node Frequency:&nbsp;</span>
        <div style={{width: "250px"}}>
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
            style={{border: "none", boxShadow: "none", padding: "15px 10px"}}
          />
        </div>
      </div>
      <div className={"flex-container"}>
        <span className={"option-span"}>Limit edges:&nbsp;</span>
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
            type={"number"}
            value={limitEdges}
            onChange={(event) => {
              setLimitEdges(Number(event.target.value));
            }}
          />
        </form>
      </div>
      <div className={"flex-container"}>
        <span className={"option-span"}>Edge Frequency:&nbsp;</span>
        <div style={{width: "250px"}}>
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
            style={{border: "none", boxShadow: "none", padding: "15px 10px"}}
          ></LogarithmicRangeSlider>
        </div>
      </div>
      <div className={"flex-container"}>
        <span className={"option-span"}>Search nodes:</span>
        <form
          style={{margin: 0}}
          onSubmit={(event) => {
            event.preventDefault();
            setGraphFilter((prevState) => ({
              ...prevState,
              labelSearch: search || undefined,
            }));
          }}
        >
          <input
            type={"search"}
            value={search || ""}
            onChange={(event) => {
              let value = event.target.value;
              setSearch(value);
              if (value === "") {
                setGraphFilter((prevState) => ({
                  ...prevState,
                  labelSearch: undefined,
                }));
              }
            }}
          />
        </form>
      </div>
      {dataBounds.categories &&


          <div className={"flex-container"}>
              <details>
                  <summary>
                      <span className={"option-span"}>Categories</span>
                  </summary>
                  <div>
                    {dataBounds.categories.map((category) => (
                      <div key={category}>
                        <input
                          type="checkbox"
                          onChange={(event) => {
                            console.log("Changed:", category);
                          }}
                        />
                        {category}
                      </div>

                    ))}
                  </div>
              </details>

          </div>}
      {dataBounds.earliestDate && dataBounds.latestDate && <div className={"flex-container"}>
          <span className={"option-span"}>Date Filter:</span>
          <div>
              <input
                  type={"date"}
                  onChange={(event) =>
                    setGraphFilter({
                      ...graphFilter,
                      earliestDate: event.target.valueAsDate ?? undefined,
                    })
                  }
              />
              <input
                  type={"date"}
                  onChange={(event) =>
                    setGraphFilter({
                      ...graphFilter,
                      latestDate: event.target.valueAsDate ?? undefined,
                    })
                  }
              />
          </div>
      </div>}
    </div>
  );
};
