import { useContext, useMemo } from 'react';
import { GraphFilterContext } from '../contexts/GraphFilterContext';
import { GraphFilter } from '../types/graphFilter';

export function useGraphFilters() {
  const context = useContext(GraphFilterContext);

  if (!context) {
    throw new Error('useGraphFilters must be used within GraphFilterProvider');
  }

  const { filters, dispatch } = context;

  // Memoized action creators
  const actions = useMemo(
    () => ({
      setNodeLimits: (limitNodes: number, limitEdges: number) =>
        dispatch({
          type: 'SET_NODE_LIMITS',
          payload: { limitNodes, limitEdges },
        }),

      setFrequencyRange: (min: number, max: number, target: 'node' | 'edge') =>
        dispatch({
          type: 'SET_FREQUENCY_RANGE',
          payload: { min, max, target },
        }),

      setDateRange: (earliest?: Date, latest?: Date) =>
        dispatch({ type: 'SET_DATE_RANGE', payload: { earliest, latest } }),

      setSearch: (query: string) =>
        dispatch({ type: 'SET_SEARCH', payload: query }),

      toggleSupernodes: () => dispatch({ type: 'TOGGLE_SUPERNODES' }),

      updateEntityLists: (whitelist?: string[], blacklist?: string[]) =>
        dispatch({
          type: 'UPDATE_ENTITY_LISTS',
          payload: { whitelist, blacklist },
        }),

      resetFilters: () => dispatch({ type: 'RESET_FILTERS' }),

      bulkUpdate: (updates: Partial<GraphFilter>) =>
        dispatch({ type: 'BULK_UPDATE', payload: updates }),
    }),
    [dispatch],
  );

  return {
    filters,
    ...actions,
  };
}
