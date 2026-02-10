# Customer Data Inventory Service

This repository has a FastAPI backend and a React frontend. The repository inspects
customer data surfaces (Salesforce, HubSpot, Google Analytics) and produces a
normalized inventory that describes what fields exist and how much data is
available for each of them.

<img width="1900" height="915" alt="image" src="https://github.com/user-attachments/assets/72a80a29-6f9c-48dc-829f-2833dfc9f64e" />


## Project structure

```
cdp_inventory/
  adapter/        # Individual platform adapter
dashboard/        # frontend app 
  src/
    components/
      auth/
        auth0-provider-with-history.tsx  #Needed in order to plugin AskAnything mfe
      ConnectionForm.tsx                 #Form component to collect user information
      Dynamic.tsx                        #Needed in order to display mfe
      ErrorBoundary.tsx                  #Creates boundary for MFE
      ResultsDisplay.tsx                 #Component to display queried tables

config/
  config.yaml        # Switched to user input credential rather than config file credentials
routers/
  inventory_aggregator.py    #API endpoint to give metric for a specified set of platforms
main.py              # CLI entry point
requirements.txt     # Python dependencies
```

## Running the inventory

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Export the environment variables referenced in `config/config.yaml` for each
   platform's credentials (for example `SALESFORCE_USERNAME`).
4. Execute the CLI: `uvicorn main:app`.
5. cd dashboard
6. Execute the CLI: `npm run dev`

The script prints a JSON payload that mirrors the Phase 1 inventory specification
by listing each platform, the available customer entity, the inspected fields,
and simple volume statistics (record counts and non-null counts).

## Dashboard

The dashboard uses webpack bundler in order to work with the Module Federation (so that mfe can be used).
Update ConnectionForm.tsx when adding new platforms



## Extending with additional platforms

Adding a new platform is as simple as:

1. Creating a new adapter class under `cdp_inventory/connectors/` that derives
   from `BaseAdapter` and implements `get_name`, `fetch_schema`, and
   `fetch_field_metrics`.
2. Registering the connector in `CONNECTOR_REGISTRY` inside
   `cdp_inventory/aggregator/inventory_runner.py`.
3. Updating the configuration file and Adapter Registry in adapter_factory with the new platform entry and the required
   credentials.

Using Adapters:
1. Adapter act as a singleton service
2. Provide user object to adapter in order to fetch schema and field metrics
3. Use the adapter factory to specify which combination of adapters will be needed to access a client's data

This adapter-driven structure keeps the aggregator logic untouched as the
integration library grows.
