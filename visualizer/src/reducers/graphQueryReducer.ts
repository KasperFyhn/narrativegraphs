import { GraphQuery } from '../types/graphQuery';

export type GraphQueryAction =
  | {
      type: 'SET_CONNECTION_TYPE';
      payload: 'relation' | 'cooccurrence';
    }
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
      type: 'SET_WHITELIST_ENTITIES';
      payload: string[];
    }
  | {
      type: 'CLEAR_WHITELIST';
    };

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

export function graphQueryReducer(
  state: GraphQuery,
  action: GraphQueryAction,
): GraphQuery {
  switch (action.type) {
    case 'SET_CONNECTION_TYPE':
      return {
        ...state,
        connectionType: action.payload,
      };
    case 'TOGGLE_WHITELIST_ENTITY':
      const containsEntity =
        state.focusEntities && state.focusEntities.includes(action.payload);
      return {
        ...state,
        focusEntities: containsEntity
          ? removeFromArray(action.payload, state.focusEntities)
          : addToArray(action.payload, state.focusEntities),
      };

    case 'ADD_WHITELIST_ENTITY':
      return {
        ...state,
        focusEntities: addToArray(action.payload, state.focusEntities),
      };

    case 'SET_WHITELIST_ENTITIES':
      return {
        ...state,
        focusEntities: action.payload,
      };

    case 'REMOVE_WHITELIST_ENTITY':
      return {
        ...state,
        focusEntities: removeFromArray(action.payload, state.focusEntities),
      };

    case 'CLEAR_WHITELIST':
      return {
        ...state,
        focusEntities: undefined,
      };

    default:
      return state;
  }
}
