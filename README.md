# Customer Data Inventory Service

This repository now includes a Python-based connector framework that inspects
customer data surfaces (Salesforce, HubSpot, Google Analytics) and produces a
normalized inventory that describes what fields exist and how much data is
available for each of them.

## Project structure

```
cdp_inventory/
  connectors/        # Individual platform connectors
  aggregator/        # Orchestrator that loads the configuration
config/
  config.yaml        # Example configuration for the initial three platforms
main.py              # CLI entry point
requirements.txt     # Python dependencies
```

## Running the inventory

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Export the environment variables referenced in `config/config.yaml` for each
   platform's credentials (for example `SALESFORCE_USERNAME`).
4. Execute the CLI: `python main.py --config config/config.yaml`.

The script prints a JSON payload that mirrors the Phase 1 inventory specification
by listing each platform, the available customer entity, the inspected fields,
and simple volume statistics (record counts and non-null counts).

## Extending with additional platforms

Adding a new platform is as simple as:

1. Creating a new connector class under `cdp_inventory/connectors/` that derives
   from `BaseConnector` and implements `authenticate`, `fetch_schema`, and
   `fetch_field_metrics`.
2. Registering the connector in `CONNECTOR_REGISTRY` inside
   `cdp_inventory/aggregator/inventory_runner.py`.
3. Updating the configuration file with the new platform entry and the required
   credentials.

This connector-driven structure keeps the aggregator logic untouched as the
integration library grows.
