import './App.css';
import { GraphViewer } from './components/graph/GraphViewer';
import React from 'react';
import { ServiceContextProvider } from './contexts/ServiceContext';

export function App() {
  return (
    <ServiceContextProvider>
      <GraphViewer />
    </ServiceContextProvider>
  );
}

export default App;
