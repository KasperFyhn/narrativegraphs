import {
  GraphFilter,
  GraphFilterAction,
  initialGraphFilter,
} from '../types/graphFilter';

export function graphFilterReducer(
  state: GraphFilter,
  action: GraphFilterAction,
): GraphFilter {
  switch (action.type) {
    case 'SET_NODE_LIMITS':
      return { ...state, ...action.payload };

    case 'SET_FREQUENCY_RANGE': {
      const { min, max, target } = action.payload;
      const minKey =
        `minimum${target === 'node' ? 'Node' : 'Edge'}Frequency` as keyof GraphFilter;
      const maxKey =
        `maximum${target === 'node' ? 'Node' : 'Edge'}Frequency` as keyof GraphFilter;

      return {
        ...state,
        [minKey]: min,
        [maxKey]: max,
      };
    }

    case 'SET_DATE_RANGE':
      return {
        ...state,
        earliestDate: action.payload.earliest,
        latestDate: action.payload.latest,
      };

    case 'SET_SEARCH':
      return { ...state, labelSearch: action.payload };

    case 'TOGGLE_SUPERNODES':
      return { ...state, onlySupernodes: !state.onlySupernodes };

    case 'UPDATE_ENTITY_LISTS':
      return {
        ...state,
        whitelistedEntityIds: action.payload.whitelist,
        blacklistedEntityIds: action.payload.blacklist,
      };

    case 'RESET_FILTERS':
      return { ...initialGraphFilter };

    case 'BULK_UPDATE':
      return { ...state, ...action.payload };

    default:
      return state;
  }
}
