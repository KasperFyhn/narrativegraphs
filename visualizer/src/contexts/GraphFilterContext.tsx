import { createContext, useReducer, type ReactNode, useContext } from 'react';
import type { GraphFilter, GraphFilterAction } from '../types/graphFilter';
import { graphFilterReducer } from '../reducers/graphFilterReducer';
import { initialGraphFilter } from '../types/graphFilter';
import React from 'react';

interface GraphFilterContextType {
  filters: GraphFilter;
  dispatch: React.Dispatch<GraphFilterAction>;
}

export const GraphFilterContext = createContext<
  GraphFilterContextType | undefined
>(undefined);

interface GraphFilterProviderProps {
  children: ReactNode;
  initialFilters?: GraphFilter;
}

export const GraphFilterProvider: React.FC<GraphFilterProviderProps> = ({
  children,
  initialFilters = initialGraphFilter,
}: GraphFilterProviderProps) => {
  const [filters, dispatch] = useReducer(graphFilterReducer, initialFilters);

  return (
    <GraphFilterContext.Provider value={{ filters, dispatch }}>
      {children}
    </GraphFilterContext.Provider>
  );
};

export const useGraphFilterContext = (): GraphFilterContextType => {
  const context = useContext(GraphFilterContext);
  if (!context) {
    throw new Error(
      'useServiceContext must be used within a GraphFilterProvider',
    );
  }
  return context;
};
