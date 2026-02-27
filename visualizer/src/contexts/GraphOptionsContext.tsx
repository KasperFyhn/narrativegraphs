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

// Maps a 0–100 precision value to vis-network stabilization parameters.
// Higher precision = more iterations + lower minVelocity (finer stopping threshold).
export function layoutPrecisionToParams(precision: number): {
  iterations: number;
  minVelocity: number;
} {
  const t = precision / 100;
  return {
    iterations: Math.round(50 + 950 * t), // 50 → 1000
    minVelocity: 3.0 - 2.9 * t, // 3.0 → 0.1
  };
}

export interface GraphOptionsContextType {
  options: Options;
  setOptions: React.Dispatch<React.SetStateAction<Options>>;
  layoutPrecision: number;
  setLayoutPrecision: React.Dispatch<React.SetStateAction<number>>;
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
  const [layoutPrecision, setLayoutPrecision] = useState(50);

  return (
    <GraphOptionsContext.Provider
      value={{ options, setOptions, layoutPrecision, setLayoutPrecision }}
    >
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
