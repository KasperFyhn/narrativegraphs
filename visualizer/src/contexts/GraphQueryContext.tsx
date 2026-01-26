import {
  createContext,
  type ReactNode,
  useContext,
  useState,
  useEffect,
  useReducer,
} from 'react';
import { DataBounds, GraphFilter, GraphQuery } from '../types/graphQuery';
import {
  GraphFilterAction,
  graphFilterReducer,
} from '../reducers/graphFilterReducer';
import { initialGraphQuery } from '../types/graphQuery';
import React from 'react';
import { useServiceContext } from './ServiceContext';
import { ClipLoader } from 'react-spinners';
import {
  HistoryControls,
  useReducerWithHistory,
} from '../reducers/historyReducer';
import {
  GraphQueryAction,
  graphQueryReducer,
} from '../reducers/graphQueryReducer';

export interface GraphQueryContextType {
  query: GraphQuery;
  dispatchQueryAction: React.Dispatch<GraphQueryAction>;
  filter: GraphFilter;
  dispatchFilterAction: React.Dispatch<GraphFilterAction>;
  dataBounds: DataBounds;
  historyControls: HistoryControls;
}

const GraphQueryContext = createContext<GraphQueryContextType | undefined>(
  undefined,
);

interface GraphQueryContextProviderProps {
  children: ReactNode;
  initialFilter?: GraphFilter;
}

export const GraphQueryContextProvider: React.FC<
  GraphQueryContextProviderProps
> = ({ children, initialFilter = initialGraphQuery }) => {
  const [query, dispatchQueryAction] = useReducer(graphQueryReducer, {
    connectionType: 'relation',
  });

  const [filter, dispatchFilterAction, historyControls] = useReducerWithHistory(
    graphFilterReducer,
    initialFilter,
  );

  const { graphService } = useServiceContext();

  const [dataBounds, setDataBounds] = useState<DataBounds>();
  useEffect(() => {
    graphService.getDataBounds().then((r: DataBounds) => setDataBounds(r));
  }, [graphService]);

  if (dataBounds === undefined) {
    return <ClipLoader loading={true} />;
  }

  return (
    <GraphQueryContext.Provider
      value={{
        query,
        dispatchQueryAction,
        filter,
        dispatchFilterAction,
        dataBounds,
        historyControls,
      }}
    >
      {children}
    </GraphQueryContext.Provider>
  );
};

export const useGraphQueryContext = (): GraphQueryContextType => {
  const context = useContext(GraphQueryContext);
  if (!context) {
    throw new Error(
      'useGraphQueryContext must be used within a GraphQueryProvider',
    );
  }
  return context;
};
