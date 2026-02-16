import './App.css';
import { GraphViewer } from './components/graph/GraphViewer';
import React from 'react';
import { ServiceContextProvider } from './contexts/ServiceContext';
import { GraphQueryContextProvider } from './contexts/GraphQueryContext';
import { GraphOptionsContextProvider } from './contexts/GraphOptionsContext';
import { SelectionContextProvider } from './contexts/SelectionContext';

export const App: React.FC = () => {
  return (
    <ServiceContextProvider>
      <GraphOptionsContextProvider>
        <GraphQueryContextProvider>
          <SelectionContextProvider>
            <GraphViewer />
          </SelectionContextProvider>
        </GraphQueryContextProvider>
      </GraphOptionsContextProvider>
    </ServiceContextProvider>
  );
};
