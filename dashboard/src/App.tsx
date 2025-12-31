import React from 'react';
import ConnectionForm from './components/ConnectionForm';
import ErrorBoundary from './components/ErrorBoundary';
import type { MFEConfig } from './types';
import './App.css';
import DynamicComponent from './components/Dynamic';

const App: React.FC = () => {
  // MFE Configuration - update these values to match your MFE setup
  const mfeConfig: MFEConfig = {
    componentURL: 'http://localhost:8027/remoteEntry.js',
    componentName: 'AskAnything',
    componentClass: './AskAnythingComponentAuth'
  };

  return (
    <div className="container">
      <header>
        <h1>Customer Data Platform Inventory Dashboard</h1>
        <p>Connect to Salesforce, HubSpot, and Google Analytics to view your data inventory</p>
      </header>

      <ConnectionForm />

      {/* MFE Container */}
      <div id="mfe-container" style={{ marginTop: '30px', padding: '20px', borderTop: '2px solid #e0e0e0' }}>
        <h2>Micro Frontend</h2>
        <ErrorBoundary>
          <DynamicComponent data={mfeConfig} />
        </ErrorBoundary>
      </div>
    </div>
  );
};

export default App;

