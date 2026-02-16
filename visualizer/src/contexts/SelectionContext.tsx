import React, {
  createContext,
  type ReactNode,
  useContext,
  useState,
} from 'react';
import { useGraphQuery } from '../hooks/useGraphQuery';

export interface SelectionContextType {
  hasSelection: boolean;
  setHasSelection: (value: boolean) => void;
  getEntityColor: (id: string | number, opacity?: number) => string;
}

const SelectionContext = createContext<SelectionContextType | undefined>(
  undefined,
);

interface SelectionContextProviderProps {
  children: ReactNode;
}

export const SelectionContextProvider: React.FC<
  SelectionContextProviderProps
> = ({ children }) => {
  const [hasSelection, setHasSelection] = useState(false);

  const { query } = useGraphQuery();

  const getEntityColor = (id: string | number, opacity = 1.0): string => {
    const entities = query.focusEntities || [];
    const colorIndex = entities.indexOf(String(id));
    if (colorIndex >= 0) {
      const hue = (colorIndex * 137.5) % 360;
      return `hsla(${hue}, 60%, 80%, ${opacity})`;
    } else {
      return 'lightgray';
    }
  };

  return (
    <SelectionContext.Provider
      value={{
        hasSelection,
        setHasSelection,
        getEntityColor,
      }}
    >
      {children}
    </SelectionContext.Provider>
  );
};

export const useSelectionContext = (): SelectionContextType => {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error(
      'useSelectionContext must be used within a SelectionContextProvider',
    );
  }
  return context;
};
