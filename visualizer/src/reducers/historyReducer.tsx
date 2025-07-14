import React, { useCallback, useMemo, useReducer } from 'react';

interface StateWithHistory<T> {
  past: T[];
  present: T;
  future: T[];
}

type HistoryAction<T> =
  | { type: 'UNDO' }
  | { type: 'REDO'; limit?: number }
  | { type: 'UPDATE'; payload: T; limit?: number }
  | { type: 'CLEAR_HISTORY' };

export interface HistoryControls {
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  clearHistory: () => void;
}

export function historyReducer<T>(
  state: StateWithHistory<T>,
  action: HistoryAction<T>,
): StateWithHistory<T> {
  switch (action.type) {
    case 'UNDO':
      if (state.past.length === 0) return state;

      const previous = state.past[state.past.length - 1];
      const newPast = state.past.slice(0, state.past.length - 1);

      return {
        past: newPast,
        present: previous,
        future: [state.present, ...state.future],
      };

    case 'REDO':
      if (state.future.length === 0) return state;

      const next = state.future[0];
      const newFuture = state.future.slice(1, action.limit);

      return {
        past: [...state.past, state.present],
        present: next,
        future: newFuture,
      };

    case 'UPDATE':
      return {
        past: [...state.past, state.present],
        present: action.payload,
        future: [], // Clear future when new action is taken
      };

    default:
      return state;
  }
}

export function useReducerWithHistory<State, Action>(
  reducer: (state: State, action: Action) => State,
  initialState: State,
  limit?: number,
): [State, React.Dispatch<Action>, HistoryControls] {
  const initialHistory: StateWithHistory<State> = {
    past: [],
    present: initialState,
    future: [],
  };

  const [history, dispatchHistory] = useReducer(
    historyReducer<State>,
    initialHistory,
  );

  const dispatch = useCallback(
    (action: Action) => {
      const newState = reducer(history.present, action);
      dispatchHistory({ type: 'UPDATE', payload: newState, limit: limit });
    },
    [reducer, history.present, limit],
  );

  const historyControls: HistoryControls = useMemo(
    () => ({
      undo: () => dispatchHistory({ type: 'UNDO' }),
      redo: () => dispatchHistory({ type: 'REDO' }),
      canUndo: history.past.length > 0,
      canRedo: history.future.length > 0,
      clearHistory: () => dispatchHistory({ type: 'CLEAR_HISTORY' }),
    }),
    [history.past.length, history.future.length],
  );

  return [history.present, dispatch, historyControls];
}
