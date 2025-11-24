"""Salesforce connector that gathers schema metadata and simple field metrics."""
from __future__ import annotations

from typing import Dict, List, Optional

from simple_salesforce import Salesforce

from .base import BaseAdapter, EntityInventory, FieldDefinition, FieldMetrics
from ..types import User


class SalesforceAdapter(BaseAdapter):
    """Connector implementation that relies on the simple-salesforce SDK."""

    def __init__(self) -> None:
        super().__init__()

    def _authenticate(self, user: User, options) -> Salesforce:
        """Creates API client object"""

        connection = [dict for dict in user.connections if "salesforce" == dict.get("name")]
        credentials = connection[0]
        username = credentials.get("username")
        password = credentials.get("password")
        security_token = credentials.get("security_token")
        domain = options.get("domain", "login")
        if not all([username, password, security_token]):
            raise ValueError("Salesforce credentials are incomplete.")
        return Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def get_name(self):
        return "Salesforce"

    def fetch_schema(self, user: User, options) -> List[FieldDefinition]:
        client = self._authenticate(user, options)
        object_name = options.get("object_name", "Contact")
        sf_object = getattr(client, object_name)
        description = sf_object.describe()
        schema = []
        for field in description.get("fields", []):
            schema.append(
                FieldDefinition(
                    name=field.get("name"),
                    data_type=field.get("type"),
                    label=field.get("label"),
                    mapped_name=options.get("field_mappings", {}).get(field.get("name")),
                )
            )
        return schema

    def fetch_field_metrics(self, user: User, schema: List[FieldDefinition], options) -> EntityInventory:
        client = self._authenticate(user, options)
        object_name = options.get("object_name", "Contact")
        fields_to_profile = options.get("fields")
        if not fields_to_profile:
            fields_to_profile = [field.name for field in schema]
        total_records = self._fetch_total_records(client, object_name)
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in fields_to_profile:
                continue
            non_null = self._fetch_non_null_count(client, object_name, field.name)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        return EntityInventory(
            platform="Salesforce",
            entity=object_name,
            total_records=total_records,
            fields=field_metrics,
        )

    def _fetch_total_records(self, client, object_name: str) -> int:
        query = f"SELECT COUNT() FROM {object_name}"
        result = client.query(query)
        records = result.get("records", [])
        if records:
            key = next(iter(records[0]))
            return int(records[0][key])
        return int(result.get("totalSize", 0))

    def _fetch_non_null_count(self, client, object_name: str, field_name: str) -> int:
        query = f"SELECT COUNT() FROM {object_name} WHERE {field_name} != null"
        result = client.query(query)
        records = result.get("records", [])
        if records:
            key = next(iter(records[0]))
            return int(records[0][key])
        return int(result.get("totalSize", 0))