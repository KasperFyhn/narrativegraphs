import 'reflect-metadata';
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { App } from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement,
);
root.render(<App />);
