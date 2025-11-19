"""Salesforce connector that gathers schema metadata and simple field metrics."""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import BaseConnector, EntityInventory, FieldDefinition, FieldMetrics


class SalesforceConnector(BaseConnector):
    """Connector implementation that relies on the simple-salesforce SDK."""

    def __init__(self, name: str, credentials: Dict[str, str], options: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name=name, credentials=credentials, options=options)
        self.client = None

    def authenticate(self) -> None:
        from simple_salesforce import Salesforce  # imported lazily to keep dependency optional

        username = self.credentials.get("username")
        password = self.credentials.get("password")
        security_token = self.credentials.get("security_token")
        domain = self.options.get("domain", "login")
        if not all([username, password, security_token]):
            raise ValueError("Salesforce credentials are incomplete.")
        self.client = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def fetch_schema(self) -> List[FieldDefinition]:
        if self.client is None:
            raise RuntimeError("Salesforce client has not been authenticated.")
        object_name = self.options.get("object_name", "Contact")
        sf_object = getattr(self.client, object_name)
        description = sf_object.describe()
        schema = []
        for field in description.get("fields", []):
            schema.append(
                FieldDefinition(
                    name=field.get("name"),
                    data_type=field.get("type"),
                    label=field.get("label"),
                    mapped_name=self.options.get("field_mappings", {}).get(field.get("name")),
                )
            )
        return schema

    def fetch_field_metrics(self, schema: List[FieldDefinition]) -> EntityInventory:
        if self.client is None:
            raise RuntimeError("Salesforce client has not been authenticated.")
        object_name = self.options.get("object_name", "Contact")
        fields_to_profile = self.options.get("fields")
        if not fields_to_profile:
            fields_to_profile = [field.name for field in schema]
        total_records = self._fetch_total_records(object_name)
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in fields_to_profile:
                continue
            non_null = self._fetch_non_null_count(object_name, field.name)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        return EntityInventory(
            platform=self.name,
            entity=object_name,
            total_records=total_records,
            fields=field_metrics,
        )

    def _fetch_total_records(self, object_name: str) -> int:
        query = f"SELECT COUNT() FROM {object_name}"
        result = self.client.query(query)
        records = result.get("records", [])
        if records:
            key = next(iter(records[0]))
            return int(records[0][key])
        return int(result.get("totalSize", 0))

    def _fetch_non_null_count(self, object_name: str, field_name: str) -> int:
        query = f"SELECT COUNT() FROM {object_name} WHERE {field_name} != null"
        result = self.client.query(query)
        records = result.get("records", [])
        if records:
            key = next(iter(records[0]))
            return int(records[0][key])
        return int(result.get("totalSize", 0))
