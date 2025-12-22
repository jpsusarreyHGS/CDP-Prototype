"""Common connector definitions and data classes used by all integrations."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Annotated
import abc

from cdp_inventory.types import User

LOGGER = logging.getLogger(__name__)

@dataclass
class FieldDefinition:
    """Represents an available field on an upstream platform."""

    name: str
    data_type: Optional[str] = None
    label: Optional[str] = None
    mapped_name: Optional[str] = None


@dataclass
class FieldMetrics:
    """Holds volume statistics for a single field."""

    definition: FieldDefinition
    non_null_count: Optional[int] = None
    completeness_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": self.definition.name,
            "type": self.definition.data_type,
            "label": self.definition.label,
            "mapped_name": self.definition.mapped_name,
            "non_null_count": self.non_null_count,
        }
        if self.completeness_pct is not None:
            payload["completeness_pct"] = round(self.completeness_pct, 4)
        return payload


@dataclass
class EntityInventory:
    """Aggregated inventory response returned by adapters."""

    platform: str
    entity: str
    total_records: Optional[int]
    fields: List[FieldMetrics] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "entity": self.entity,
            "total_records": self.total_records,
            "fields": [field.to_dict() for field in self.fields],
            "metadata": self.metadata,
        }


class BaseAdapter(abc.ABC):
    """Defines the interface that every platform connector must implement."""

    def collect_inventory(self, user: User, options) -> EntityInventory:
        """Authenticate (if needed) and gather inventory data."""
        print("BASE ADAPTER: collect_inventory called", flush=True)
        adapter_name = self.get_name()
        print(f"[{adapter_name}] collect_inventory method called", flush=True)
        LOGGER.info(f"[{adapter_name}] Starting collect_inventory...")
        print(f"[{adapter_name}] Starting collect_inventory...", flush=True)
        try:
            print(f"[{adapter_name}] About to call fetch_schema...", flush=True)
            LOGGER.info(f"[{adapter_name}] Step 1: Fetching schema...")
            print(f"[{adapter_name}] Step 1: Fetching schema...", flush=True)
            print(f"[{adapter_name}] Calling self.fetch_schema(user, options) now...", flush=True)
            schema = self.fetch_schema(user, options)
            print(f"[{adapter_name}] fetch_schema returned, got {len(schema)} fields", flush=True)
            LOGGER.info(f"[{adapter_name}] Step 1 complete: Retrieved {len(schema)} fields from schema")
            LOGGER.info(f"[{adapter_name}] Step 2: Fetching field metrics...")
            inventory = self.fetch_field_metrics(user, schema, options)
            LOGGER.info(f"[{adapter_name}] Step 2 complete: Retrieved inventory with {inventory.total_records} total records")
            LOGGER.info(f"[{adapter_name}] collect_inventory complete!")
            return inventory
        except Exception as e:
            LOGGER.exception(f"[{adapter_name}] Error in collect_inventory: {type(e).__name__}: {str(e)}")
            raise

    def get_name(self) -> str:
        """Return the name of the platform."""

    @abc.abstractmethod
    def fetch_schema(self, user: User, options) -> List[FieldDefinition]:
        """Return the available customer related fields for the connector's entity."""

    @abc.abstractmethod
    def fetch_field_metrics(self, user: User, schema: List[FieldDefinition], options) -> EntityInventory:
        """Return basic volume metrics for the supplied schema."""