# CDP Inventory Dashboard

A web-based dashboard for interacting with the Customer Data Platform Inventory API.

## Features

- **Multi-Platform Support**: Connect to Google Analytics, Salesforce, and HubSpot
- **Easy Form Interface**: Fill out connection details and query options
- **Real-time Results**: View inventory data in a clean, organized format
- **JSON Viewer**: See raw API responses with syntax highlighting

## Setup

1. Make sure your FastAPI server is running:
   ```bash
   cd CDP-Prototype
   python -m uvicorn main:app --reload
   ```

2. Open `index.html` in your web browser, or serve it using a local web server:
   ```bash
   # Using Python
   python -m http.server 8080
   
   # Then open http://localhost:8080/index.html
   ```

## Usage

1. **Select Platform**: Choose Google Analytics, Salesforce, or HubSpot from the dropdown
2. **Fill Connection Details**: Enter your credentials for the selected platform
3. **Set Query Options**: 
   - For GA4: Enter Property ID and select fields
   - For Salesforce: Enter domain and object name
   - For HubSpot: Enter object type
4. **Set Date Range**: Use relative dates like "30daysAgo" and "today" or absolute dates like "2024-11-25"
5. **Click "Fetch Inventory"**: View results in the right panel

## API Endpoint

The dashboard connects to: `http://127.0.0.1:8000/inventory/inventory`

If your server is running on a different port or host, edit the `API_BASE_URL` in `script.js`.

## Notes

- The private key field automatically escapes newlines for JSON
- All form fields are validated before submission
- Results are displayed with statistics and field-level details
- Raw JSON response is available for debugging

