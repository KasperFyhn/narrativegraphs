import { GraphFilter } from '../types/graphFilter';

export type GraphFilterAction =
  | {
      type: 'SET_NODE_LIMIT';
      payload: number;
    }
  | {
      type: 'SET_EDGE_LIMIT';
      payload: number;
    }
  | {
      type: 'SET_NODE_FREQUENCY_RANGE';
      payload: { min?: number; max?: number };
    }
  | {
      type: 'SET_EDGE_FREQUENCY_RANGE';
      payload: { min?: number; max?: number };
    }
  | { type: 'SET_LABEL_SEARCH'; payload: string }
  | { type: 'SET_DATE_RANGE'; payload: { start?: Date; end?: Date } }
  | {
      type: 'TOGGLE_WHITELIST_ENTITY';
      payload: string;
    }
  | {
      type: 'ADD_WHITELIST_ENTITY';
      payload: string;
    }
  | {
      type: 'REMOVE_WHITELIST_ENTITY';
      payload: string;
    }
  | {
      type: 'ADD_BLACKLIST_ENTITY';
      payload: string;
    }
  | {
      type: 'REMOVE_BLACKLIST_ENTITY';
      payload: string;
    }
  | {
      type: 'CLEAR_WHITELIST';
    }
  | {
      type: 'CLEAR_BLACKLIST';
    }
  | { type: 'RESET_FILTER' };

function addToArray<T>(obj: T, array?: T[]): T[] {
  if (array === undefined) {
    array = [];
  } else if (array.includes(obj)) {
    return array;
  }
  return [...array, obj];
}

function removeFromArray<T>(obj: T, array?: T[]): T[] {
  if (array === undefined) {
    return [];
  }
  return array.filter((item: T) => item !== obj);
}

export function graphFilterReducer(
  state: GraphFilter,
  action: GraphFilterAction,
): GraphFilter {
  switch (action.type) {
    case 'SET_NODE_LIMIT':
      return {
        ...state,
        limitNodes: action.payload,
      };

    case 'SET_EDGE_LIMIT':
      return {
        ...state,
        limitEdges: action.payload,
      };

    case 'SET_NODE_FREQUENCY_RANGE':
      return {
        ...state,
        minimumNodeFrequency: action.payload.min,
        maximumNodeFrequency: action.payload.max,
      };

    case 'SET_EDGE_FREQUENCY_RANGE':
      return {
        ...state,
        minimumEdgeFrequency: action.payload.min,
        maximumEdgeFrequency: action.payload.max,
      };

    case 'SET_LABEL_SEARCH':
      const value = action.payload === '' ? undefined : action.payload;
      return {
        ...state,
        labelSearch: value,
      };

    case 'SET_DATE_RANGE':
      return {
        ...state,
        earliestDate: action.payload.start,
        latestDate: action.payload.end,
      };

    case 'TOGGLE_WHITELIST_ENTITY':
      const containsEntity =
        state.whitelistedEntityIds &&
        state.whitelistedEntityIds.includes(action.payload);
      return {
        ...state,
        whitelistedEntityIds: containsEntity
          ? removeFromArray(action.payload, state.whitelistedEntityIds)
          : addToArray(action.payload, state.whitelistedEntityIds),
      };

    case 'ADD_WHITELIST_ENTITY':
      return {
        ...state,
        whitelistedEntityIds: addToArray(
          action.payload,
          state.whitelistedEntityIds,
        ),
      };

    case 'ADD_BLACKLIST_ENTITY':
      const entityId = action.payload;
      if (
        state.whitelistedEntityIds &&
        state.whitelistedEntityIds.includes(entityId)
      ) {
        return state;
      }
      return {
        ...state,
        blacklistedEntityIds: addToArray(entityId, state.blacklistedEntityIds),
      };

    case 'REMOVE_WHITELIST_ENTITY':
      return {
        ...state,
        whitelistedEntityIds: removeFromArray(
          action.payload,
          state.whitelistedEntityIds,
        ),
      };

    case 'REMOVE_BLACKLIST_ENTITY':
      return {
        ...state,
        blacklistedEntityIds: removeFromArray(
          action.payload,
          state.blacklistedEntityIds,
        ),
      };

    case 'CLEAR_WHITELIST':
      return {
        ...state,
        whitelistedEntityIds: undefined,
      };

    case 'CLEAR_BLACKLIST':
      return {
        ...state,
        blacklistedEntityIds: undefined,
      };

    default:
      return state;
  }
}
