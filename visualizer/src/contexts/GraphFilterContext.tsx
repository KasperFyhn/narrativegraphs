import {
  createContext,
  useReducer,
  type ReactNode,
  useContext,
  useState,
  useEffect,
} from 'react';
import { DataBounds, GraphFilter } from '../types/graphFilter';
import {
  GraphFilterAction,
  graphFilterReducer,
} from '../reducers/graphFilterReducer';
import { initialGraphFilter } from '../types/graphFilter';
import React from 'react';
import { useServiceContext } from './ServiceContext';
import { ClipLoader } from 'react-spinners';

export interface GraphFilterContextType {
  filter: GraphFilter;
  dataBounds: DataBounds;
  dispatch: React.Dispatch<GraphFilterAction>;
}

const GraphFilterContext = createContext<GraphFilterContextType | undefined>(
  undefined,
);

interface GraphFilterContextProviderProps {
  children: ReactNode;
  initialFilter?: GraphFilter;
}

export const GraphFilterContextProvider: React.FC<
  GraphFilterContextProviderProps
> = ({ children, initialFilter = initialGraphFilter }) => {
  const [filter, dispatch] = useReducer(graphFilterReducer, initialFilter);

  const { graphService } = useServiceContext();

  const [dataBounds, setDataBounds] = useState<DataBounds>();
  useEffect(() => {
    graphService.getDataBounds().then((r: DataBounds) => setDataBounds(r));
  }, [graphService]);

  if (dataBounds === undefined) {
    return <ClipLoader loading={true} />;
  }

  return (
    <GraphFilterContext.Provider
      value={{ filter: filter, dataBounds: dataBounds, dispatch }}
    >
      {children}
    </GraphFilterContext.Provider>
  );
};

export const useGraphFilterContext = (): GraphFilterContextType => {
  const context = useContext(GraphFilterContext);
  if (!context) {
    throw new Error(
      'useGraphFilterContext must be used within a GraphFilterProvider',
    );
  }
  return context;
};
