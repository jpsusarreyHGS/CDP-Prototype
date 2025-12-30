import React from 'react';
import type { InventoryResponse } from '../types';
import { formatNumber, escapeHtml, syntaxHighlight } from '../utils/helpers';
import { METRIC_DISPLAY_NAMES } from '../constants';

interface ResultsDisplayProps {
  results: InventoryResponse | null;
  error: string | null;
  loading: boolean;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, error, loading }) => {
  if (loading) {
    return (
      <div className="placeholder">
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        <h3>Error</h3>
        <p>{escapeHtml(error)}</p>
        <p style={{ marginTop: '10px', fontSize: '0.9rem', color: '#666' }}>
          Make sure your API server is running at http://127.0.0.1:8000
        </p>
      </div>
    );
  }

  if (!results || Object.keys(results).length === 0) {
    return (
      <div className="placeholder">
        <p>👈 Fill out the form and click "Fetch Inventory" to see results</p>
      </div>
    );
  }

  // Handle test connection result
  if ((results as any).test) {
    return (
      <div className="success-message">
        <h3>✓ API Connection Successful!</h3>
        <p>Server response: {(results as any).message || JSON.stringify(results)}</p>
        <p style={{ marginTop: '10px', fontSize: '0.9rem' }}>
          API is running at: http://127.0.0.1:8000
        </p>
      </div>
    );
  }

  let html = '<div class="results-content">';
  
  // Check for errors
  if (results._errors) {
    html += '<div class="error-message"><h3>Errors</h3><ul>';
    for (const [platform, error] of Object.entries(results._errors)) {
      html += `<li><strong>${platform}:</strong> ${error}</li>`;
    }
    html += '</ul></div>';
  }
  
  let hasData = false;
  
  for (const [platformName, platformData] of Object.entries(results)) {
    if (platformName === '_errors') continue;
    
    const entity = platformData.entity || 'N/A';
    const totalRecords = platformData.total_records || 0;
    
    const fieldNames: string[] = [];
    const nonNullCounts: number[] = [];
    
    if (platformData.fields && platformData.fields.length > 0) {
      platformData.fields.forEach(field => {
        fieldNames.push(field.name || 'N/A');
        nonNullCounts.push(field.non_null_count || 0);
      });
    }
    
    if (fieldNames.length > 0 || totalRecords > 0) {
      hasData = true;
      
      html += '<div class="table-container">';
      let platformLabel = platformData.platform || platformName;
      let viewName: string | null = null;
      
      if (platformName.includes('-')) {
        const parts = platformName.split('-');
        platformLabel = parts[0];
        viewName = parts.slice(1).join('-');
        
        if (platformData._display_name) {
          viewName = platformData._display_name;
        } else if (platformLabel === 'Google Analytics') {
          viewName = METRIC_DISPLAY_NAMES[viewName] || viewName;
        }
        
        platformLabel = `${platformLabel} - ${viewName}`;
      }
      
      html += `<div class="platform-label">${escapeHtml(platformLabel)}</div>`;
      html += '<table class="inventory-table">';
      html += '<tbody>';
      
      html += '<tr class="details-row">';
      html += `<td class="entity-cell">${escapeHtml(entity)}</td>`;
      fieldNames.forEach(fieldName => {
        html += `<td class="field-name-cell">${escapeHtml(fieldName)}</td>`;
      });
      html += `<td class="number-cell total-records-cell">${formatNumber(totalRecords)}</td>`;
      html += '</tr>';
      
      html += '<tr class="counts-row">';
      html += '<td class="entity-cell">Non-Null Counts</td>';
      nonNullCounts.forEach(count => {
        html += `<td class="number-cell">${formatNumber(count)}</td>`;
      });
      html += `<td class="number-cell total-records-cell">${formatNumber(totalRecords)}</td>`;
      html += '</tr>';
      
      html += '</tbody>';
      html += '</table>';
      html += '</div>';
    }
  }
  
  if (!hasData) {
    html += '<p style="color: #888; margin-top: 15px;">No field data available.</p>';
  }
  
  html += `<div style="margin-top: 30px;">`;
  html += `<details class="json-viewer-details">`;
  html += `<summary style="cursor: pointer; font-weight: 600; margin-bottom: 15px; color: #667eea;">Raw JSON Response (Click to expand/collapse)</summary>`;
  html += `<div class="json-viewer">${syntaxHighlight(JSON.stringify(results, null, 2))}</div>`;
  html += `</details>`;
  html += `</div>`;
  
  html += '</div>';
  
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
};

export default ResultsDisplay;

