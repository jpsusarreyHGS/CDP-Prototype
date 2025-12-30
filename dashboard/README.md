# CDP Inventory Dashboard

A TypeScript/React web-based dashboard for interacting with the Customer Data Platform Inventory API.

## Features

- **Multi-Platform Support**: Connect to Google Analytics, Salesforce, and HubSpot
- **Easy Form Interface**: Fill out connection details and query options
- **Real-time Results**: View inventory data in a clean, organized format
- **JSON Viewer**: See raw API responses with syntax highlighting
- **Micro Frontend Support**: Integrate remote React components via Module Federation
- **TypeScript**: Fully typed for better development experience

## Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- FastAPI server running (see Setup section)

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Make sure your FastAPI server is running:**
   ```bash
   cd CDP-Prototype
   python -m uvicorn main:app --reload
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

   The app will open at `http://localhost:3000`

4. **Build for production:**
   ```bash
   npm run build
   # or
   yarn build
   # or
   pnpm build
   ```

   The built files will be in the `dist` directory.

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

If your server is running on a different port or host, edit the `API_BASE_URL` in `src/constants/index.ts`.

## Micro Frontend Configuration

To configure the MFE integration, edit `src/App.tsx` and update the `mfeConfig` object:

```typescript
const mfeConfig: MFEConfig = {
  componentURL: 'http://localhost:8027/remoteEntry.js',
  componentName: 'mfe', // Update to match your MFE's scope name
  componentClass: './App' // Update to match your MFE's exposed module
};
```

## Project Structure

```
dashboard/
├── src/
│   ├── components/          # React components
│   │   ├── ConnectionForm.tsx
│   │   ├── ResultsDisplay.tsx
│   │   ├── DynamicComponent.tsx
│   │   └── MFELoader.tsx
│   ├── services/            # API services
│   │   └── api.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Utility functions
│   │   ├── helpers.ts
│   │   └── formBuilder.ts
│   ├── constants/           # Constants
│   │   └── index.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css
├── index.html               # HTML template
├── package.json
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite config
└── styles.css               # Styles (imported in App.css)
```

## Notes

- The private key field automatically escapes newlines for JSON
- All form fields are validated before submission
- Results are displayed with statistics and field-level details
- Raw JSON response is available for debugging
- TypeScript provides type safety throughout the application

