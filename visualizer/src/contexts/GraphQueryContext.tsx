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
import { ConnectionType } from '../hooks/useGraphQuery';

export interface GraphQueryContextType {
  query: GraphQuery;
  dispatchQueryAction: React.Dispatch<GraphQueryAction>;
  filter: GraphFilter;
  dispatchFilterAction: React.Dispatch<GraphFilterAction>;
  connectionTypes: ConnectionType[];
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
  const { graphService } = useServiceContext();

  const [query, dispatchQueryAction] = useReducer(graphQueryReducer, {
    // hacky, but it's handled in the following code
    connectionType: undefined as unknown as ConnectionType,
  });

  const [filter, dispatchFilterAction, historyControls] = useReducerWithHistory(
    graphFilterReducer,
    initialFilter,
  );

  const [connectionTypes, setConnectionTypes] = useState<ConnectionType[]>();
  const [dataBounds, setDataBounds] = useState<DataBounds>();

  // Initialization: fetch types and initial bounds together
  useEffect(() => {
    graphService.getConnectionTypes().then(async (types) => {
      setConnectionTypes(types);
      dispatchQueryAction({ type: 'SET_CONNECTION_TYPE', payload: types[0] });
      const bounds = await graphService.getDataBounds(types[0]);
      setDataBounds(bounds);
    });
  }, [graphService]);

  // Refetch bounds when user changes connection type (skips during init)
  useEffect(() => {
    if (!connectionTypes || !query.connectionType) return;

    graphService
      .getDataBounds(query.connectionType)
      .then((r: DataBounds) => setDataBounds(r));
  }, [graphService, query.connectionType, connectionTypes]);

  if (connectionTypes === undefined || dataBounds === undefined) {
    return <ClipLoader loading={true} />;
  }

  return (
    <GraphQueryContext.Provider
      value={{
        query,
        dispatchQueryAction,
        filter,
        dispatchFilterAction,
        connectionTypes,
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
