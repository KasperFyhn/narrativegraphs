import './App.css';
import { GraphViewer } from './components/graph/GraphViewer';
import React from 'react';
import { ServiceContextProvider } from './contexts/ServiceContext';
import { GraphFilterContextProvider } from './contexts/GraphFilterContext';
import { GraphOptionsContextProvider } from './contexts/GraphOptionsContext';

export const App: React.FC = () => {
  return (
    <ServiceContextProvider>
      <GraphOptionsContextProvider>
        <GraphFilterContextProvider>
          <GraphViewer />
        </GraphFilterContextProvider>
      </GraphOptionsContextProvider>
    </ServiceContextProvider>
  );
};
