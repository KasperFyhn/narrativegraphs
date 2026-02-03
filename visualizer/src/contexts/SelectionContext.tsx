import React, {
  createContext,
  type ReactNode,
  useContext,
  useState,
} from 'react';

export interface SelectionContextType {
  hasSelection: boolean;
  setHasSelection: (value: boolean) => void;
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

  return (
    <SelectionContext.Provider value={{ hasSelection, setHasSelection }}>
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