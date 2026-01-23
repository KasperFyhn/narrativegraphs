import { useMemo } from 'react';

import { DataBounds, GraphFilter, GraphQuery } from '../types/graphQuery';
import { useGraphQueryContext } from '../contexts/GraphQueryContext';
import { HistoryControls } from '../reducers/historyReducer';

export type ConnectionType = 'relation' | 'cooccurrence';

interface GraphQueryActions {
  setConnectionType: (connectionType: ConnectionType) => void;
  toggleFocusEntityId: (entityId: string) => void;
  addFocusEntityId: (entityId: string) => void;
  removeFocusEntityId: (entityId: string) => void;
  setFocusEntities: (entityIds: string[]) => void;
  clearFocusEntities: () => void;
}

interface GraphFilterActions {
  setNodeLimit: (limit: number) => void;
  setEdgeLimit: (limit: number) => void;
  setNodeFrequencyRange: (min: number, max: number) => void;
  setEdgeFrequencyRange: (min: number, max: number) => void;
  setDateRange: (start: Date, end: Date) => void;
  addBlacklistedEntityId: (...entityIds: string[]) => void;
  removeBlacklistedEntityId: (entityId: string) => void;
  clearBlacklist: () => void;
  toggleCategoryValue: (name: string, value: string) => void;
  addCategory: (name: string, value: string) => void;
  removeCategory: (name: string, value: string) => void;
  resetCategory: (name: string) => void;
  resetFilter: () => void;
}

export interface GraphQueryAccessors
  extends GraphQueryActions,
    GraphFilterActions {
  query: GraphQuery;
  dataBounds: DataBounds;
  filter: GraphFilter;
  historyControls: HistoryControls;
}

export function useGraphQuery(): GraphQueryAccessors {
  const context = useGraphQueryContext();

  const {
    query,
    dispatchQueryAction,
    filter,
    dataBounds,
    dispatchFilterAction,
    historyControls,
  } = context;

  // Memoized action creators
  const queryActions = useMemo(
    (): GraphQueryActions => ({
      setConnectionType: (connectionType) => {
        dispatchQueryAction({
          type: 'SET_CONNECTION_TYPE',
          payload: connectionType,
        });
      },
      toggleFocusEntityId: (entityId: string) =>
        dispatchQueryAction({
          type: 'TOGGLE_WHITELIST_ENTITY',
          payload: entityId,
        }),
      addFocusEntityId: (entityId: string) =>
        dispatchQueryAction({
          type: 'ADD_WHITELIST_ENTITY',
          payload: entityId,
        }),
      removeFocusEntityId: (entityId: string) =>
        dispatchQueryAction({
          type: 'REMOVE_WHITELIST_ENTITY',
          payload: entityId,
        }),
      setFocusEntities: (entityIds: string[]) =>
        dispatchQueryAction({
          type: 'SET_WHITELIST_ENTITIES',
          payload: entityIds,
        }),
      clearFocusEntities: () =>
        dispatchQueryAction({ type: 'CLEAR_WHITELIST' }),
    }),
    [dispatchQueryAction],
  );
  const filterActions = useMemo(
    (): GraphFilterActions => ({
      setNodeLimit: (limit: number) =>
        dispatchFilterAction({ type: 'SET_NODE_LIMIT', payload: limit }),
      setEdgeLimit: (limit: number) =>
        dispatchFilterAction({ type: 'SET_EDGE_LIMIT', payload: limit }),
      setNodeFrequencyRange: (min: number, max: number) =>
        dispatchFilterAction({
          type: 'SET_NODE_FREQUENCY_RANGE',
          payload: { min, max },
        }),
      setEdgeFrequencyRange: (min: number, max: number) =>
        dispatchFilterAction({
          type: 'SET_EDGE_FREQUENCY_RANGE',
          payload: { min, max },
        }),
      setDateRange: (start: Date, end: Date) =>
        dispatchFilterAction({
          type: 'SET_DATE_RANGE',
          payload: { start, end },
        }),

      addBlacklistedEntityId: (...entityIds: string[]) =>
        dispatchFilterAction({
          type: 'ADD_BLACKLIST_ENTITY',
          payload: entityIds,
        }),
      removeBlacklistedEntityId: (entityId: string) =>
        dispatchFilterAction({
          type: 'REMOVE_BLACKLIST_ENTITY',
          payload: entityId,
        }),
      clearBlacklist: () => dispatchFilterAction({ type: 'CLEAR_BLACKLIST' }),
      toggleCategoryValue: (name: string, value: string) =>
        dispatchFilterAction({
          type: 'TOGGLE_CATEGORY',
          payload: { name, value },
        }),
      addCategory: (name: string, value: string) =>
        dispatchFilterAction({
          type: 'ADD_CATEGORY',
          payload: { name, value },
        }),
      removeCategory: (name: string, value: string) =>
        dispatchFilterAction({
          type: 'REMOVE_CATEGORY',
          payload: { name, value },
        }),
      resetCategory: (name: string) =>
        dispatchFilterAction({ type: 'RESET_CATEGORY', payload: name }),
      resetFilter: () => dispatchFilterAction({ type: 'RESET_FILTER' }),
    }),
    [dispatchFilterAction],
  );
  return {
    query,
    dataBounds,
    filter,
    historyControls,
    ...queryActions,
    ...filterActions,
  };
}
