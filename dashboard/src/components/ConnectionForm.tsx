import React, { useState } from 'react';
import type { Platform } from '../types';
import { buildRequestPayload } from '../utils/formBuilder';
import { fetchInventory } from '../services/api';
import ResultsDisplay from './ResultsDisplay';

const ConnectionForm: React.FC = () => {
  const [platform, setPlatform] = useState<Platform>('google_analytics');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Form field refs - we'll use controlled components
  const [formData, setFormData] = useState({
    // GA fields
    gaType: 'service_account',
    gaProjectId: '',
    gaPrivateKeyId: '',
    gaPrivateKey: '',
    gaClientEmail: '',
    gaClientId: '',
    gaAuthUri: 'https://accounts.google.com/o/oauth2/auth',
    gaTokenUri: 'https://oauth2.googleapis.com/token',
    gaAuthProviderCertUrl: 'https://www.googleapis.com/oauth2/v1/certs',
    gaClientCertUrl: '',
    gaUniverseDomain: 'googleapis.com',
    gaPropertyId: '',
    gaFields: 'totalUsers,sessions,eventCount,screenPageViews',
    gaStartDate: '30daysAgo',
    gaEndDate: 'today',
    // Salesforce fields
    sfUsername: '',
    sfPassword: '',
    sfSecurityToken: '',
    sfDomain: 'login',
    // HubSpot fields
    hsAccessToken: '',
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload = buildRequestPayload(platform, formData);
      const data = await fetchInventory(payload);
      setResults(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Error details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setError(null);
    try {
      const { testConnection } = await import('../services/api');
      const data = await testConnection();
      setResults({ test: true, message: data.message || 'Connection successful!' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <div className="input-panel">
        <h2>Connection Details</h2>
        
        <form id="inventoryForm" onSubmit={handleSubmit}>
          <section className="form-section">
            <h3>Platform Connection</h3>
            <div className="form-group">
              <label htmlFor="platform">Select Platform</label>
              <select
                id="platform"
                value={platform}
                onChange={(e) => setPlatform(e.target.value as Platform)}
                required
              >
                <option value="google_analytics">Google Analytics</option>
                <option value="salesforce">Salesforce</option>
                <option value="hubspot">HubSpot</option>
              </select>
            </div>
          </section>

          {/* Google Analytics Connection */}
          {platform === 'google_analytics' && (
            <section id="gaConnection" className="form-section connection-section">
              <h3>Google Analytics Connection</h3>
              <div className="form-group">
                <label htmlFor="gaType">Connection Type</label>
                <input
                  type="text"
                  id="gaType"
                  value={formData.gaType}
                  readOnly
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaProjectId">Project ID</label>
                <input
                  type="text"
                  id="gaProjectId"
                  value={formData.gaProjectId}
                  onChange={(e) => handleInputChange('gaProjectId', e.target.value)}
                  placeholder="vigilant-result-451923-s9"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaPrivateKeyId">Private Key ID</label>
                <input
                  type="text"
                  id="gaPrivateKeyId"
                  value={formData.gaPrivateKeyId}
                  onChange={(e) => handleInputChange('gaPrivateKeyId', e.target.value)}
                  placeholder="cc5f40cf7a60fe193afde11f91e4eff6ddbca6d5"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaPrivateKey">Private Key</label>
                <textarea
                  id="gaPrivateKey"
                  rows={8}
                  value={formData.gaPrivateKey}
                  onChange={(e) => handleInputChange('gaPrivateKey', e.target.value)}
                  placeholder="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
                  required
                />
                <small>Paste your full private key including BEGIN and END markers. Newlines will be automatically escaped.</small>
              </div>
              <div className="form-group">
                <label htmlFor="gaClientEmail">Client Email</label>
                <input
                  type="email"
                  id="gaClientEmail"
                  value={formData.gaClientEmail}
                  onChange={(e) => handleInputChange('gaClientEmail', e.target.value)}
                  placeholder="service-account@project.iam.gserviceaccount.com"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaClientId">Client ID</label>
                <input
                  type="text"
                  id="gaClientId"
                  value={formData.gaClientId}
                  onChange={(e) => handleInputChange('gaClientId', e.target.value)}
                  placeholder="113419803986734923050"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaAuthUri">Auth URI</label>
                <input
                  type="url"
                  id="gaAuthUri"
                  value={formData.gaAuthUri}
                  onChange={(e) => handleInputChange('gaAuthUri', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaTokenUri">Token URI</label>
                <input
                  type="url"
                  id="gaTokenUri"
                  value={formData.gaTokenUri}
                  onChange={(e) => handleInputChange('gaTokenUri', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaAuthProviderCertUrl">Auth Provider X509 Cert URL</label>
                <input
                  type="url"
                  id="gaAuthProviderCertUrl"
                  value={formData.gaAuthProviderCertUrl}
                  onChange={(e) => handleInputChange('gaAuthProviderCertUrl', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaClientCertUrl">Client X509 Cert URL</label>
                <input
                  type="url"
                  id="gaClientCertUrl"
                  value={formData.gaClientCertUrl}
                  onChange={(e) => handleInputChange('gaClientCertUrl', e.target.value)}
                  placeholder="https://www.googleapis.com/robot/v1/metadata/x509/..."
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="gaUniverseDomain">Universe Domain</label>
                <input
                  type="text"
                  id="gaUniverseDomain"
                  value={formData.gaUniverseDomain}
                  onChange={(e) => handleInputChange('gaUniverseDomain', e.target.value)}
                  required
                />
              </div>
              
              <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '2px solid #e0e0e0' }}>
                <h3 style={{ marginBottom: '15px' }}>Query Options</h3>
                <p style={{ marginBottom: '15px', color: '#666', fontSize: '0.9rem' }}>
                  <strong>Note:</strong> This will display a single table with all common GA4 metrics: Total Users, Sessions, Event Count, Screen Page Views, New Users, Conversions, Total Revenue, Average Session Duration, Engagement Rate, and Bounce Rate.
                </p>
                <div className="form-group">
                  <label htmlFor="gaPropertyId">Property ID</label>
                  <input
                    type="text"
                    id="gaPropertyId"
                    value={formData.gaPropertyId}
                    onChange={(e) => handleInputChange('gaPropertyId', e.target.value)}
                    placeholder="280556903"
                    required
                  />
                  <small>Your GA4 Property ID (numeric)</small>
                </div>
                <div className="form-group">
                  <label htmlFor="gaFields">Fields (comma-separated)</label>
                  <input
                    type="text"
                    id="gaFields"
                    value={formData.gaFields}
                    onChange={(e) => handleInputChange('gaFields', e.target.value)}
                    placeholder="totalUsers,sessions,eventCount,screenPageViews"
                    required
                  />
                  <small>Common GA4 metrics: totalUsers, sessions, eventCount, screenPageViews</small>
                </div>
                <div className="form-group">
                  <label htmlFor="gaStartDate">Start Date</label>
                  <input
                    type="text"
                    id="gaStartDate"
                    value={formData.gaStartDate}
                    onChange={(e) => handleInputChange('gaStartDate', e.target.value)}
                    placeholder="30daysAgo or YYYY-MM-DD"
                    required
                  />
                  <small>Use relative dates like "30daysAgo" or absolute dates like "2024-11-25"</small>
                </div>
                <div className="form-group">
                  <label htmlFor="gaEndDate">End Date</label>
                  <input
                    type="text"
                    id="gaEndDate"
                    value={formData.gaEndDate}
                    onChange={(e) => handleInputChange('gaEndDate', e.target.value)}
                    placeholder="today or YYYY-MM-DD"
                    required
                  />
                </div>
              </div>
            </section>
          )}

          {/* Salesforce Connection */}
          {platform === 'salesforce' && (
            <section id="sfConnection" className="form-section connection-section">
              <h3>Salesforce Connection</h3>
              <p style={{ marginBottom: '15px', color: '#666', fontSize: '0.9rem' }}>
                <strong>Note:</strong> This will retrieve and display data for Contact and Case objects.
              </p>
              <div className="form-group">
                <label htmlFor="sfUsername">Username</label>
                <input
                  type="text"
                  id="sfUsername"
                  value={formData.sfUsername}
                  onChange={(e) => handleInputChange('sfUsername', e.target.value)}
                  placeholder="your-username@example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="sfPassword">Password</label>
                <input
                  type="password"
                  id="sfPassword"
                  value={formData.sfPassword}
                  onChange={(e) => handleInputChange('sfPassword', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="sfSecurityToken">Security Token</label>
                <input
                  type="text"
                  id="sfSecurityToken"
                  value={formData.sfSecurityToken}
                  onChange={(e) => handleInputChange('sfSecurityToken', e.target.value)}
                  required
                />
                <small>If you changed your password, you may need to reset your security token in Salesforce.</small>
              </div>
              <div className="form-group">
                <label htmlFor="sfDomain">Domain</label>
                <select
                  id="sfDomain"
                  value={formData.sfDomain}
                  onChange={(e) => handleInputChange('sfDomain', e.target.value)}
                  required
                >
                  <option value="login">Production (login.salesforce.com)</option>
                  <option value="test">Sandbox (test.salesforce.com)</option>
                </select>
                <small>Select "Sandbox" if you're connecting to a Salesforce sandbox environment.</small>
              </div>
            </section>
          )}

          {/* HubSpot Connection */}
          {platform === 'hubspot' && (
            <section id="hsConnection" className="form-section connection-section">
              <h3>HubSpot Connection</h3>
              <div className="form-group">
                <label htmlFor="hsAccessToken">Access Token</label>
                <input
                  type="text"
                  id="hsAccessToken"
                  value={formData.hsAccessToken}
                  onChange={(e) => handleInputChange('hsAccessToken', e.target.value)}
                  placeholder="pat-na1-..."
                  required
                />
                <small>This will retrieve and display data for Contacts and Deals.</small>
              </div>
            </section>
          )}

          <button type="submit" className="submit-btn" disabled={loading}>
            <span id="submitText">{loading ? 'Fetching...' : 'Fetch Inventory'}</span>
            {loading && <span id="submitLoader" className="loader" style={{ display: 'inline-block' }}></span>}
          </button>
        </form>
        
        <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e0e0e0' }}>
          <button
            type="button"
            id="testBtn"
            className="submit-btn"
            style={{ background: '#28a745' }}
            onClick={handleTestConnection}
            disabled={loading}
          >
            Test API Connection
          </button>
        </div>
      </div>

      <div className="output-panel">
        <h2>Results</h2>
        <ResultsDisplay results={results} error={error} loading={loading} />
      </div>
    </div>
  );
};

export default ConnectionForm;

