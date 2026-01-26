import './App.css';
import { GraphViewer } from './components/graph/GraphViewer';
import React from 'react';
import { ServiceContextProvider } from './contexts/ServiceContext';
import { GraphQueryContextProvider } from './contexts/GraphQueryContext';
import { GraphOptionsContextProvider } from './contexts/GraphOptionsContext';

export const App: React.FC = () => {
  return (
    <ServiceContextProvider>
      <GraphOptionsContextProvider>
        <GraphQueryContextProvider>
          <GraphViewer />
        </GraphQueryContextProvider>
      </GraphOptionsContextProvider>
    </ServiceContextProvider>
  );
};
