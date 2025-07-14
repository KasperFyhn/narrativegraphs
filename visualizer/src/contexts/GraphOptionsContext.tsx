import React, {
  createContext,
  type ReactNode,
  useContext,
  useState,
} from 'react';
import { Options } from 'react-vis-graph-wrapper';

export function isSmoothEnabled(options: Options): boolean {
  if (typeof options.edges?.smooth === 'boolean') {
    return options.edges.smooth;
  } else if (
    typeof options.edges?.smooth === 'object' &&
    'enabled' in options.edges.smooth
  ) {
    return options.edges.smooth.enabled;
  } else {
    return false;
  }
}

export interface GraphOptionsContextType {
  options: Options;
  setOptions: React.Dispatch<React.SetStateAction<Options>>;
}

const GraphOptionsContext = createContext<GraphOptionsContextType | undefined>(
  undefined,
);

interface GraphOptionsContextProviderProps {
  children: ReactNode;
}

export const GraphOptionsContextProvider: React.FC<
  GraphOptionsContextProviderProps
> = ({ children }) => {
  const [options, setOptions] = useState<Options>({
    physics: {
      enabled: true,
      barnesHut: {
        springLength: 300,
      },
    },
    edges: {
      smooth: true,
      font: {
        align: 'top',
      },
    },
  });

  return (
    <GraphOptionsContext.Provider value={{ options, setOptions }}>
      {children}
    </GraphOptionsContext.Provider>
  );
};

export const useGraphOptionsContext = (): GraphOptionsContextType => {
  const context = useContext(GraphOptionsContext);
  if (!context) {
    throw new Error(
      'useGraphOptionsContext must be used within a GraphOptionsProvider',
    );
  }
  return context;
};
