import { useMemo } from 'react';

import { DataBounds, GraphFilter } from '../types/graphFilter';
import { useGraphFilterContext } from '../contexts/GraphFilterContext';
import { HistoryControls } from '../reducers/historyReducer';

interface GraphFilterActions {
  setNodeLimit: (limit: number) => void;
  setEdgeLimit: (limit: number) => void;
  setNodeFrequencyRange: (min: number, max: number) => void;
  setEdgeFrequencyRange: (min: number, max: number) => void;
  setLabelSearch: (label: string) => void;
  setDateRange: (start: Date, end: Date) => void;
  toggleWhitelistedEntityId: (entityId: string) => void;
  addWhitelistedEntityId: (entityId: string) => void;
  removeWhitelistedEntityId: (entityId: string) => void;
  setWhitelistEntities: (entityIds: string[]) => void;
  addBlacklistedEntityId: (...entityIds: string[]) => void;
  removeBlacklistedEntityId: (entityId: string) => void;
  clearWhitelist: () => void;
  clearBlacklist: () => void;
  toggleCategoryValue: (name: string, value: string) => void;
  addCategory: (name: string, value: string) => void;
  removeCategory: (name: string, value: string) => void;
  resetCategory: (name: string) => void;
  resetFilter: () => void;
}

export interface GraphFilterAccessors extends GraphFilterActions {
  dataBounds: DataBounds;
  filter: GraphFilter;
  historyControls: HistoryControls;
}

export function useGraphFilter(): GraphFilterAccessors {
  const context = useGraphFilterContext();

  const { filter, dataBounds, dispatch, historyControls } = context;

  // Memoized action creators
  const actions = useMemo(
    (): GraphFilterActions => ({
      setNodeLimit: (limit: number) =>
        dispatch({ type: 'SET_NODE_LIMIT', payload: limit }),
      setEdgeLimit: (limit: number) =>
        dispatch({ type: 'SET_EDGE_LIMIT', payload: limit }),
      setNodeFrequencyRange: (min: number, max: number) =>
        dispatch({ type: 'SET_NODE_FREQUENCY_RANGE', payload: { min, max } }),
      setEdgeFrequencyRange: (min: number, max: number) =>
        dispatch({ type: 'SET_EDGE_FREQUENCY_RANGE', payload: { min, max } }),
      setLabelSearch: (label: string) =>
        dispatch({ type: 'SET_LABEL_SEARCH', payload: label }),
      setDateRange: (start: Date, end: Date) =>
        dispatch({ type: 'SET_DATE_RANGE', payload: { start, end } }),
      toggleWhitelistedEntityId: (entityId: string) =>
        dispatch({ type: 'TOGGLE_WHITELIST_ENTITY', payload: entityId }),
      addWhitelistedEntityId: (entityId: string) =>
        dispatch({ type: 'ADD_WHITELIST_ENTITY', payload: entityId }),
      removeWhitelistedEntityId: (entityId: string) =>
        dispatch({ type: 'REMOVE_WHITELIST_ENTITY', payload: entityId }),
      setWhitelistEntities: (entityIds: string[]) =>
        dispatch({ type: 'SET_WHITELIST_ENTITIES', payload: entityIds }),
      addBlacklistedEntityId: (...entityIds: string[]) =>
        dispatch({ type: 'ADD_BLACKLIST_ENTITY', payload: entityIds }),
      removeBlacklistedEntityId: (entityId: string) =>
        dispatch({ type: 'REMOVE_BLACKLIST_ENTITY', payload: entityId }),
      clearWhitelist: () => dispatch({ type: 'CLEAR_WHITELIST' }),
      clearBlacklist: () => dispatch({ type: 'CLEAR_BLACKLIST' }),
      toggleCategoryValue: (name: string, value: string) =>
        dispatch({ type: 'TOGGLE_CATEGORY', payload: { name, value } }),
      addCategory: (name: string, value: string) =>
        dispatch({ type: 'ADD_CATEGORY', payload: { name, value } }),
      removeCategory: (name: string, value: string) =>
        dispatch({ type: 'REMOVE_CATEGORY', payload: { name, value } }),
      resetCategory: (name: string) =>
        dispatch({ type: 'RESET_CATEGORY', payload: name }),
      resetFilter: () => dispatch({ type: 'RESET_FILTER' }),
    }),
    [dispatch],
  );
  return {
    dataBounds,
    filter,
    historyControls,
    ...actions,
  };
}
