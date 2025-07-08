import './App.css';
import { GraphViewer } from './components/graph/GraphViewer';
import React from 'react';
import { ServiceContextProvider } from './contexts/ServiceContext';
import { GraphFilterContextProvider } from './contexts/GraphFilterContext';

export const App: React.FC = () => {
  return (
    <ServiceContextProvider>
      <GraphFilterContextProvider>
        <GraphViewer />
      </GraphFilterContextProvider>
    </ServiceContextProvider>
  );
};
