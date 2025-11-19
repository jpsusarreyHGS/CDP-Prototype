"""Common connector definitions and data classes used by all integrations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import abc


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
    """Aggregated inventory response returned by connectors."""

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


class BaseConnector(abc.ABC):
    """Defines the interface that every platform connector must implement."""

    def __init__(self, name: str, credentials: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.credentials = credentials
        self.options = options or {}
        self._authenticated = False

    def collect_inventory(self) -> EntityInventory:
        """Authenticate (if needed) and gather inventory data."""

        if not self._authenticated:
            self.authenticate()
            self._authenticated = True
        schema = self.fetch_schema()
        return self.fetch_field_metrics(schema)

    @abc.abstractmethod
    def authenticate(self) -> None:
        """Establish an authenticated client or HTTP session."""

    @abc.abstractmethod
    def fetch_schema(self) -> List[FieldDefinition]:
        """Return the available customer related fields for the connector's entity."""

    @abc.abstractmethod
    def fetch_field_metrics(self, schema: List[FieldDefinition]) -> EntityInventory:
        """Return basic volume metrics for the supplied schema."""
