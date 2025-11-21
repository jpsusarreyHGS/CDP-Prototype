"""HubSpot connector built on the official hubspot-api-client SDK."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from hubspot import HubSpot
from hubspot.crm.objects import ApiException

from .base import BaseConnector, EntityInventory, FieldDefinition, FieldMetrics


class HubSpotConnector(BaseConnector):
    """Collects schema metadata and volume metrics for HubSpot objects."""

    def __init__(self, name: str, credentials: Dict[str, str], options: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name=name, credentials=credentials, options=options)
        self.client = None

    def authenticate(self) -> None:

        access_token = self.credentials.get("access_token")
        if not access_token:
            raise ValueError("HubSpot access token is required.")
        self.client = HubSpot(access_token=access_token)

    def fetch_schema(self) -> List[FieldDefinition]:
        if self.client is None:
            raise RuntimeError("HubSpot client has not been authenticated.")
        object_type = self.options.get("object_type", "contacts")
        properties_api = self.client.crm.properties.core_api
        schema = []
        for prop in properties_api.get_all(object_type=object_type):
            schema.append(
                FieldDefinition(
                    name=prop.name,
                    data_type=prop.type,
                    label=prop.label,
                    mapped_name=self.options.get("field_mappings", {}).get(prop.name),
                )
            )
        return schema

    def fetch_field_metrics(self, schema: List[FieldDefinition]) -> EntityInventory:
        if self.client is None:
            raise RuntimeError("HubSpot client has not been authenticated.")
        object_type = self.options.get("object_type", "contacts")
        fields_to_profile = self.options.get("fields")
        if not fields_to_profile:
            fields_to_profile = [field.name for field in schema]
        total_records, non_null_counts = self._iterate_records(object_type, fields_to_profile)
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in fields_to_profile:
                continue
            non_null = non_null_counts.get(field.name, 0)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        return EntityInventory(platform=self.name, entity=object_type, total_records=total_records, fields=field_metrics)

    def _iterate_records(self, object_type: str, fields: List[str]) -> Tuple[int, Dict[str, int]]:

        basic_api = self.client.crm.objects.basic_api
        limit = self.options.get("page_size", 100)
        after: Optional[str] = None
        total_records = 0
        non_null_counts: Dict[str, int] = {field: 0 for field in fields}
        while True:
            try:
                page = basic_api.get_page(
                    object_type=object_type,
                    properties=fields,
                    limit=limit,
                    after=after,
                )
            except ApiException as exc:
                raise RuntimeError(f"HubSpot pagination failed: {exc}") from exc
            results = page.results or []
            total_records += len(results)
            for record in results:
                properties = record.properties or {}
                for field in fields:
                    value = properties.get(field)
                    if value not in (None, ""):
                        non_null_counts[field] += 1
            paging = getattr(page, "paging", None)
            next_link = getattr(paging, "next", None) if paging else None
            after = getattr(next_link, "after", None) if next_link else None
            if after is None:
                break
        return total_records, non_null_counts
