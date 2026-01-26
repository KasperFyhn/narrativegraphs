import { GraphFilter } from '../types/graphQuery';

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
  | { type: 'SET_DATE_RANGE'; payload: { start?: Date; end?: Date } }
  | {
      type: 'ADD_BLACKLIST_ENTITY';
      payload: string[];
    }
  | {
      type: 'REMOVE_BLACKLIST_ENTITY';
      payload: string;
    }
  | {
      type: 'CLEAR_BLACKLIST';
    }
  | {
      type: 'TOGGLE_CATEGORY';
      payload: {
        name: string;
        value: string;
      };
    }
  | {
      type: 'RESET_CATEGORY';
      payload: string;
    }
  | {
      type: 'ADD_CATEGORY';
      payload: {
        name: string;
        value: string;
      };
    }
  | {
      type: 'REMOVE_CATEGORY';
      payload: {
        name: string;
        value: string;
      };
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

function removeFromArray<T>(obj: T, array?: T[]): T[] | undefined {
  if (array === undefined) {
    return [];
  }
  const result = array.filter((item: T) => item !== obj);
  return result.length === 0 ? undefined : result;
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

    case 'SET_DATE_RANGE':
      return {
        ...state,
        earliestDate: action.payload.start,
        latestDate: action.payload.end,
      };

    case 'ADD_BLACKLIST_ENTITY':
      const entityIds = action.payload;
      let result = state.blacklistedEntityIds;
      for (const entityId of entityIds) {
        result = addToArray(entityId, result);
      }
      return {
        ...state,
        blacklistedEntityIds: result,
      };

    case 'REMOVE_BLACKLIST_ENTITY':
      return {
        ...state,
        blacklistedEntityIds: removeFromArray(
          action.payload,
          state.blacklistedEntityIds,
        ),
      };

    case 'CLEAR_BLACKLIST':
      return {
        ...state,
        blacklistedEntityIds: undefined,
      };

    case 'TOGGLE_CATEGORY':
      const containsCategory =
        state.categories &&
        state.categories[action.payload.name] &&
        state.categories[action.payload.name]?.includes(action.payload.value);
      return {
        ...state,
        categories: {
          ...state.categories,
          [action.payload.name]: containsCategory
            ? removeFromArray(
                action.payload.value,
                state.categories?.[action.payload.name],
              )
            : addToArray(
                action.payload.value,
                state.categories?.[action.payload.name],
              ),
        },
      };
    case 'RESET_CATEGORY':
      return {
        ...state,
        categories: {
          ...state.categories,
          [action.payload]: undefined,
        },
      };

    case 'ADD_CATEGORY':
      return {
        ...state,
        categories: {
          ...state.categories,
          [action.payload.name]: addToArray(
            action.payload.value,
            state.categories?.[action.payload.name],
          ),
        },
      };
    case 'REMOVE_CATEGORY':
      return {
        ...state,
        categories: {
          ...state.categories,
          [action.payload.name]: removeFromArray(
            action.payload.value,
            state.categories?.[action.payload.name],
          ),
        },
      };

    default:
      return state;
  }
}
