"""High level orchestration logic for collecting data inventory results."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

import yaml

from ..connectors.base import BaseConnector, EntityInventory
from ..connectors.google_analytics import GoogleAnalyticsConnector
from ..connectors.hubspot import HubSpotConnector
from ..connectors.salesforce import SalesforceConnector

LOGGER = logging.getLogger(__name__)

CONNECTOR_REGISTRY: Dict[str, type[BaseConnector]] = {
    "salesforce": SalesforceConnector,
    "hubspot": HubSpotConnector,
    "google_analytics": GoogleAnalyticsConnector,
}


class InventoryAggregator:
    """Loads configuration, instantiates connectors, and normalizes results."""

    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.platform_configs = self._load_config()

    def _load_config(self) -> List[Dict]:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file) or {}
        platforms = raw_config.get("platforms")
        if not platforms:
            raise ValueError("Configuration file must declare at least one platform.")
        return platforms

    def run(self) -> Dict[str, EntityInventory]:
        results: Dict[str, EntityInventory] = {}
        for platform_config in self.platform_configs:
            name = platform_config.get("name")
            connector_key = platform_config.get("connector")
            if not name or not connector_key:
                raise ValueError("Each platform entry must include name and connector fields.")
            connector_class = CONNECTOR_REGISTRY.get(connector_key)
            if connector_class is None:
                raise ValueError(f"Unsupported connector '{connector_key}'.")
            credentials = self._resolve_values(platform_config.get("credentials", {}))
            options = platform_config.get("options", {})
            connector = connector_class(name=name, credentials=credentials, options=options)
            try:
                results[name] = connector.collect_inventory()
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.exception("Failed to collect inventory for %s", name)
                results[name] = EntityInventory(
                    platform=name,
                    entity=options.get("object_name") or options.get("object_type") or options.get("entity", "unknown"),
                    total_records=None,
                    fields=[],
                    metadata={"error": str(exc)},
                )
        return results

    def to_json(self, results: Dict[str, EntityInventory]) -> str:
        serializable = {name: inventory.to_dict() for name, inventory in results.items()}
        return json.dumps(serializable, indent=2)

    @staticmethod
    def _resolve_values(payload: Dict[str, str]) -> Dict[str, str]:
        resolved: Dict[str, str] = {}
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("env:"):
                env_key = value.split(":", maxsplit=1)[1]
                resolved[key] = os.environ.get(env_key)
            else:
                resolved[key] = value
            if resolved[key] is None:
                raise ValueError(f"Credential value for '{key}' could not be resolved.")
        return resolved
