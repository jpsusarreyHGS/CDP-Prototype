// API endpoint - adjust if your server is running on a different port
const API_BASE_URL = 'http://127.0.0.1:8000';

// Log API URL on page load for debugging
console.log('Dashboard loaded. API endpoint:', API_BASE_URL);

// Helper function to toggle required attribute based on visibility
function toggleRequiredFields(section, isVisible) {
    if (!section) return;
    // Use data-required attribute to track which fields should be required
    const requiredFields = section.querySelectorAll('[data-required="true"]');
    requiredFields.forEach(field => {
        if (isVisible) {
            field.setAttribute('required', 'required');
        } else {
            field.removeAttribute('required');
        }
    });
}

// Platform selection handler
document.getElementById('platform').addEventListener('change', function() {
    const platform = this.value;
    
    // Hide all connection sections and remove required attributes
    const gaSection = document.getElementById('gaConnection');
    const sfSection = document.getElementById('sfConnection');
    const hsSection = document.getElementById('hsConnection');
    
    toggleRequiredFields(gaSection, false);
    toggleRequiredFields(sfSection, false);
    toggleRequiredFields(hsSection, false);
    
    gaSection.style.display = 'none';
    sfSection.style.display = 'none';
    hsSection.style.display = 'none';
    
    // Show relevant connection section and add required attributes
    if (platform === 'google_analytics') {
        gaSection.style.display = 'block';
        toggleRequiredFields(gaSection, true);
    } else if (platform === 'salesforce') {
        sfSection.style.display = 'block';
        toggleRequiredFields(sfSection, true);
    } else if (platform === 'hubspot') {
        hsSection.style.display = 'block';
        toggleRequiredFields(hsSection, true);
    }
});

// Initialize: Make sure GA fields are required on page load since it's the default
document.addEventListener('DOMContentLoaded', function() {
    const gaSection = document.getElementById('gaConnection');
    if (gaSection && gaSection.style.display !== 'none') {
        toggleRequiredFields(gaSection, true);
    }
});

// Form submission handler
const form = document.getElementById('inventoryForm');
if (!form) {
    console.error('ERROR: Form element not found! Cannot attach submit handler.');
} else {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        console.log('=== Form submitted ===');
        
        // Check form validity
        if (!form.checkValidity()) {
            console.error('Form validation failed!');
            form.reportValidity();
            
            // Show which fields are invalid
            const invalidFields = form.querySelectorAll(':invalid');
            console.error('Invalid fields:', Array.from(invalidFields).map(f => f.id || f.name));
            
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <h3>Form Validation Error</h3>
                    <p>Please fill out all required fields marked with an asterisk (*).</p>
                    <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                        Check the form for highlighted fields that need to be completed.
                    </p>
                </div>
            `;
            return;
        }
    
    const submitBtn = document.querySelector('.submit-btn');
    const submitText = document.getElementById('submitText');
    const submitLoader = document.getElementById('submitLoader');
    const resultsContainer = document.getElementById('resultsContainer');
    
    // Show loading state
    submitBtn.disabled = true;
    submitText.textContent = 'Fetching...';
    submitLoader.style.display = 'block';
    
    // Clear previous results
    resultsContainer.innerHTML = '<div class="placeholder"><p>Loading...</p></div>';
    
    try {
        // Build request payload based on selected platform
        const platform = document.getElementById('platform').value;
        console.log('Selected platform:', platform);
        
        const payload = buildRequestPayload(platform);
        
        // Validate payload structure before stringifying
        if (!payload || !payload.user || !Array.isArray(payload.user.connections)) {
            throw new Error('Invalid payload structure. Please check your form inputs.');
        }
        
        // Ensure all connection objects have valid values (no undefined, null, or empty strings where required)
        payload.user.connections = payload.user.connections.map(conn => {
            const cleanConn = {};
            for (const [key, value] of Object.entries(conn)) {
                // Skip undefined values
                if (value === undefined) {
                    console.warn(`Warning: Connection field '${key}' is undefined, removing from payload`);
                    continue;
                }
                // Ensure string values are actually strings (not null or other types)
                if (typeof value === 'string') {
                    cleanConn[key] = value;
                } else if (value === null) {
                    // Convert null to empty string for string fields
                    console.warn(`Warning: Connection field '${key}' is null, converting to empty string`);
                    cleanConn[key] = '';
                } else {
                    // Keep other types as-is (numbers, booleans, etc.)
                    cleanConn[key] = value;
                }
            }
            // Validate that required fields exist
            if (cleanConn.name === 'hubspot' && !cleanConn.access_token) {
                throw new Error('HubSpot access_token is missing or empty');
            }
            if (cleanConn.name === 'salesforce' && (!cleanConn.username || !cleanConn.password || !cleanConn.security_token)) {
                throw new Error('Salesforce credentials are incomplete');
            }
            return cleanConn;
        });
        
        // Validate JSON structure before stringifying
        try {
            // Try to stringify and parse back to validate
            const testString = JSON.stringify(payload);
            const testParse = JSON.parse(testString);
            console.log('✓ JSON validation passed');
        } catch (jsonError) {
            console.error('✗ JSON validation failed before sending:', jsonError);
            console.error('Payload that failed validation:', JSON.stringify(payload, null, 2));
            throw new Error(`Invalid JSON structure: ${jsonError.message}. Please check the browser console for details.`);
        }
        
        let requestBody;
        try {
            requestBody = JSON.stringify(payload);
            console.log('✓ JSON stringify successful');
            
            // Verify no single quotes are in the JSON (should only have double quotes)
            if (requestBody.includes("'")) {
                console.warn('⚠ WARNING: Single quotes detected in JSON string! This is invalid JSON.');
                console.warn('JSON string:', requestBody);
                // Check if single quotes are being used as string delimiters (invalid JSON)
                const singleQuotePattern = /:\s*'([^']*)'/g;
                if (singleQuotePattern.test(requestBody)) {
                    console.error('✗ Found single-quoted string values in JSON! This is invalid.');
                    throw new Error('Invalid JSON format detected: single quotes found in string values. This should not happen with JSON.stringify(). Please clear your browser cache and try again.');
                }
            }
        } catch (jsonError) {
            console.error('✗ JSON stringify error:', jsonError);
            console.error('Payload that failed:', JSON.stringify(payload, null, 2));
            throw new Error(`Failed to serialize request payload: ${jsonError.message}`);
        }
        
        console.log('=== REQUEST DETAILS ===');
        console.log('API URL:', `${API_BASE_URL}/inventory/inventory`);
        console.log('Request payload (full object):', payload);
        console.log('Request body (JSON string):', requestBody);
        console.log('Request body length:', requestBody.length);
        console.log('Request body preview (first 200 chars):', requestBody.substring(0, 200));
        console.log('Content-Type: application/json');
        
        // Validate the JSON string is valid by parsing it
        try {
            const parsed = JSON.parse(requestBody);
            console.log('✓ Request body JSON is valid and parseable');
            // Verify the structure is correct
            if (!parsed.user || !Array.isArray(parsed.user.connections)) {
                throw new Error('Parsed JSON does not have expected structure');
            }
        } catch (parseError) {
            console.error('✗ Request body JSON is INVALID:', parseError);
            console.error('Invalid JSON string (full):', requestBody);
            throw new Error(`Generated invalid JSON: ${parseError.message}. Check browser console for full JSON string.`);
        }
        
        // Log connection details for debugging
        if (payload.user && payload.user.connections && payload.user.connections.length > 0) {
            payload.user.connections.forEach((conn, idx) => {
                console.log(`Connection ${idx + 1}:`, {
                    name: conn.name || conn.type || 'unknown',
                    keys: Object.keys(conn),
                    // Mask sensitive data
                    username: conn.username ? conn.username : (conn.client_email || 'N/A'),
                    passwordLength: conn.password ? conn.password.length : 0,
                    tokenLength: conn.security_token ? conn.security_token.length : 0
                });
            });
        }
        
        // Make API call
        console.log('Sending POST request...');
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/inventory/inventory`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: requestBody
            });
            console.log('✓ POST request sent successfully');
            console.log('Response status:', response.status);
            console.log('Response status text:', response.statusText);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        } catch (fetchError) {
            console.error('✗ Fetch error (request failed to send):', fetchError);
            throw new Error(`Failed to send request: ${fetchError.message}`);
        }
        
        let data;
        try {
            const responseText = await response.text();
            console.log('Response body (raw):', responseText);
            if (responseText) {
                data = JSON.parse(responseText);
            } else {
                data = {};
            }
        } catch (parseError) {
            console.error('✗ JSON parse error:', parseError);
            throw new Error(`Failed to parse response: ${parseError.message}. Response was: ${await response.text()}`);
        }
        console.log('Response data:', data);
        
        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            if (data.detail) {
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    errorMessage = data.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
                } else {
                    errorMessage = JSON.stringify(data.detail);
                }
            }
            throw new Error(errorMessage);
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error details:', error);
        console.error('Error stack:', error.stack);
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to API server. Make sure it's running at ${API_BASE_URL}`;
        }
        displayError(errorMessage);
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitText.textContent = 'Fetch Inventory';
        submitLoader.style.display = 'none';
    }
    });
    console.log('Form submit handler attached successfully');
}

// Test API connection button
document.addEventListener('DOMContentLoaded', function() {
    const testBtn = document.getElementById('testBtn');
    if (testBtn) {
        testBtn.addEventListener('click', async function() {
            console.log('Testing API connection...');
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = '<div class="placeholder"><p>Testing connection...</p></div>';
            
            try {
                const response = await fetch(`${API_BASE_URL}/`);
                const data = await response.json();
                resultsContainer.innerHTML = `
                    <div class="success-message">
                        <h3>✓ API Connection Successful!</h3>
                        <p>Server response: ${data.message || JSON.stringify(data)}</p>
                        <p style="margin-top: 10px; font-size: 0.9rem;">
                            API is running at: ${API_BASE_URL}
                        </p>
                    </div>
                `;
                console.log('API test successful:', data);
            } catch (error) {
                console.error('API test failed:', error);
                resultsContainer.innerHTML = `
                    <div class="error-message">
                        <h3>✗ API Connection Failed</h3>
                        <p>${error.message}</p>
                        <p style="margin-top: 10px; font-size: 0.9rem;">
                            Make sure your FastAPI server is running:<br>
                            <code>cd CDP-Prototype<br>python -m uvicorn main:app --reload</code>
                        </p>
                    </div>
                `;
            }
        });
        console.log('Test button handler attached');
    }
});

function buildRequestPayload(platform) {
    console.log('Building payload for platform:', platform);
    
    // User object with minimal required fields
    const user = {
        first_name: "string",
        last_name: "string",
        email: "string",
        phone: "string",
        connections: []
    };
    
    const options = {
        domain: "test"
    };
    
    // Build connection based on platform
    if (platform === 'google_analytics') {
        // Escape newlines in private key
        const privateKey = document.getElementById('gaPrivateKey').value.replace(/\n/g, '\\n');
        
        user.connections.push({
            type: document.getElementById('gaType').value,
            project_id: document.getElementById('gaProjectId').value,
            private_key_id: document.getElementById('gaPrivateKeyId').value,
            private_key: privateKey,
            client_email: document.getElementById('gaClientEmail').value,
            client_id: document.getElementById('gaClientId').value,
            auth_uri: document.getElementById('gaAuthUri').value,
            token_uri: document.getElementById('gaTokenUri').value,
            auth_provider_x509_cert_url: document.getElementById('gaAuthProviderCertUrl').value,
            client_x509_cert_url: document.getElementById('gaClientCertUrl').value,
            universe_domain: document.getElementById('gaUniverseDomain').value
        });
        
        // Google Analytics specific options
        const propertyIdEl = document.getElementById('gaPropertyId');
        const fieldsEl = document.getElementById('gaFields');
        const startDateEl = document.getElementById('gaStartDate');
        const endDateEl = document.getElementById('gaEndDate');
        
        if (!propertyIdEl || !fieldsEl || !startDateEl || !endDateEl) {
            throw new Error('Missing required Google Analytics form fields. Make sure all fields are visible.');
        }
        
        options.property_id = propertyIdEl.value;
        options.fields = fieldsEl.value.split(',').map(f => f.trim()).filter(f => f);
        
        // Add date range
        const startDate = startDateEl.value;
        const endDate = endDateEl.value;
        if (startDate && endDate) {
            options.date_ranges = [{
                start_date: startDate,
                end_date: endDate
            }];
        }
        
    } else if (platform === 'salesforce') {
        // Trim whitespace from credentials to avoid authentication issues
        const username = document.getElementById('sfUsername').value.trim();
        const password = document.getElementById('sfPassword').value.trim();
        const securityToken = document.getElementById('sfSecurityToken').value.trim();
        const domain = document.getElementById('sfDomain').value || 'login';
        
        if (!username || !password || !securityToken) {
            throw new Error('All Salesforce credentials are required (Username, Password, Security Token)');
        }
        
        console.log('Salesforce credentials (masked):', {
            username: username,
            password: '***' + (password.length > 0 ? ' (length: ' + password.length + ')' : ' (empty)'),
            securityToken: securityToken.substring(0, 4) + '***' + (securityToken.length > 4 ? ' (length: ' + securityToken.length + ')' : ''),
            domain: domain
        });
        
        user.connections.push({
            name: 'salesforce',
            username: username,
            password: password,
            security_token: securityToken
        });
        
        options.domain = domain;
        // Request both Contact and Case objects
        options.object_names = ['Contact', 'Case'];
        
    } else if (platform === 'hubspot') {
        // Get and validate HubSpot access token
        const accessTokenEl = document.getElementById('hsAccessToken');
        if (!accessTokenEl) {
            throw new Error('HubSpot access token field not found. Make sure the HubSpot connection section is visible.');
        }
        
        let accessToken = accessTokenEl.value.trim();
        if (!accessToken) {
            throw new Error('HubSpot access token is required. Please enter a valid access token.');
        }
        
        // Ensure access token is a proper string and doesn't contain problematic characters
        accessToken = String(accessToken);
        
        // Remove any quotes if accidentally included (though this shouldn't happen)
        if ((accessToken.startsWith('"') && accessToken.endsWith('"')) || 
            (accessToken.startsWith("'") && accessToken.endsWith("'"))) {
            accessToken = accessToken.slice(1, -1);
        }
        
        console.log('HubSpot access token (masked):', {
            length: accessToken.length,
            prefix: accessToken.substring(0, 6) + '...',
            type: typeof accessToken
        });
        
        // Create connection object explicitly to ensure proper structure
        const hubspotConnection = {
            name: 'hubspot',
            access_token: accessToken
        };
        
        console.log('HubSpot connection object:', JSON.stringify(hubspotConnection));
        user.connections.push(hubspotConnection);
        
        options.object_type = 'contacts';
        options.fields = ['email', 'phone', 'firstname', 'lastname'];
    }
    
    const payload = { user, options };
    console.log('Final payload:', JSON.stringify(payload, null, 2));
    return payload;
}

function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    
    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '<div class="error-message"><h3>No Data</h3><p>No inventory data was returned. Check your connection details and try again.</p></div>';
        return;
    }
    
    let html = '<div class="results-content">';
    
    // Check for errors
    if (data._errors) {
        html += '<div class="error-message"><h3>Errors</h3><ul>';
        for (const [platform, error] of Object.entries(data._errors)) {
            html += `<li><strong>${platform}:</strong> ${error}</li>`;
        }
        html += '</ul></div>';
    }
    
    // Process each platform's data and create a 2-row table
    let hasData = false;
    
    for (const [platformName, platformData] of Object.entries(data)) {
        if (platformName === '_errors') continue;
        
        const entity = platformData.entity || 'N/A';
        const totalRecords = platformData.total_records || 0;
        
        // Collect field names and non-null counts
        const fieldNames = [];
        const nonNullCounts = [];
        
        if (platformData.fields && platformData.fields.length > 0) {
            platformData.fields.forEach(field => {
                fieldNames.push(field.name || 'N/A');
                nonNullCounts.push(field.non_null_count || 0);
            });
        }
        
        // Only create table if we have data
        if (fieldNames.length > 0 || totalRecords > 0) {
            hasData = true;
            
            html += '<div class="table-container">';
            // Extract platform name (handle cases like "Salesforce-Contact" -> "Salesforce")
            let platformLabel = platformData.platform || platformName;
            if (platformName.includes('-')) {
                platformLabel = platformName.split('-')[0];
            }
            html += `<div class="platform-label">${escapeHtml(platformLabel)}</div>`;
            html += '<table class="inventory-table">';
            html += '<tbody>';
            
            // First row: Entity | Field names | Total Records
            html += '<tr class="details-row">';
            html += `<td class="entity-cell">${escapeHtml(entity)}</td>`;
            fieldNames.forEach(fieldName => {
                html += `<td class="field-name-cell">${escapeHtml(fieldName)}</td>`;
            });
            html += `<td class="number-cell total-records-cell">${formatNumber(totalRecords)}</td>`;
            html += '</tr>';
            
            // Second row: Non-Null Counts label | Non-null counts | Total Records
            html += '<tr class="counts-row">';
            html += '<td class="entity-cell">Non-Null Counts</td>'; // Label for the counts row
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
    
    // Add raw JSON viewer (collapsible)
    html += `<div style="margin-top: 30px;">`;
    html += `<details class="json-viewer-details">`;
    html += `<summary style="cursor: pointer; font-weight: 600; margin-bottom: 15px; color: #667eea;">Raw JSON Response (Click to expand/collapse)</summary>`;
    html += `<div class="json-viewer">${syntaxHighlight(JSON.stringify(data, null, 2))}</div>`;
    html += `</details>`;
    html += `</div>`;
    
    html += '</div>';
    container.innerHTML = html;
}

function displayError(message) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="error-message">
            <h3>Error</h3>
            <p>${escapeHtml(message)}</p>
            <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                Make sure your API server is running at ${API_BASE_URL}
            </p>
        </div>
    `;
}

function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function syntaxHighlight(json) {
    if (typeof json !== 'string') {
        json = JSON.stringify(json, null, 2);
    }
    
    json = escapeHtml(json);
    
    // Add syntax highlighting
    json = json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function(match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
    
    return json;
}

