import React from 'react';
import ConnectionForm from './components/ConnectionForm';
import ErrorBoundary from './components/ErrorBoundary';
import type { MFEConfig } from './types';
import './App.css';
import DynamicComponent from './components/Dynamic';
import Auth0ProviderWithHistory from './components/auth/auth0-provier-with-history';

const App: React.FC = () => {
  // MFE Configuration - update these values to match your MFE setup
  const askAnythingConfig: MFEConfig = {
    componentURL: 'http://localhost:8027/remoteEntry.js',
    componentName: 'AskAnything',
    componentClass: './AskAnythingComponentAuth',
    config: {
      "module_access": {
        "departments": [],
        "roles": [
          { "name": "agent" }
        ]
      }
    }
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
        <Auth0ProviderWithHistory>
          <ErrorBoundary>
            <DynamicComponent data={askAnythingConfig} />
          </ErrorBoundary>
        </Auth0ProviderWithHistory>
      </div>
    </div>
  );
};

export default App;

