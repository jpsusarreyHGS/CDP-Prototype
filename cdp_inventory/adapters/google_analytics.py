"""Google Analytics 4 connector using the Analytics Data API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Sequence

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    Dimension,
    Filter,
    FilterExpression,
    GetMetadataRequest,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account

from .base import BaseAdapter, EntityInventory, FieldDefinition, FieldMetrics
from ..types import User


class GoogleAnalyticsAdapter(BaseAdapter):
    """Fetches GA4 metadata and basic user volume metrics."""

    def __init__(self) -> None:
        super().__init__()

    def get_name(self) -> str:
        return "Google Analytics"

    def _authenticate(self, user: User):
        """Build an authenticated GA4 client using a user's connection details."""

        connection = next((conn for conn in user.connections if conn.get("name") == "google_analytics"), None)
        if connection is None:
            raise ValueError("User does not have a Google Analytics connection configured.")
        service_account_info = connection.get("service_account_info")
        service_account_file = connection.get("service_account_file")
        if not service_account_info and not service_account_file:
            raise ValueError("Either service_account_info or service_account_file must be provided for GA4.")
        if service_account_info:
            info = json.loads(service_account_info)
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        else:
            path = Path(service_account_file).expanduser()
            credentials = service_account.Credentials.from_service_account_file(
                str(path),
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        return BetaAnalyticsDataClient(credentials=credentials)

    def fetch_schema(self, user: User, options) -> List[FieldDefinition]:
        client = self._authenticate(user)
        property_id = options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        metadata_request = GetMetadataRequest(name=f"properties/{property_id}/metadata")
        metadata = client.get_metadata(metadata_request)
        target_fields = set(options.get("fields", []))
        schema: List[FieldDefinition] = []
        for dimension in metadata.dimensions:
            if target_fields and dimension.api_name not in target_fields:
                continue
            schema.append(
                FieldDefinition(
                    name=dimension.api_name,
                    data_type="dimension",
                    label=dimension.ui_name,
                    mapped_name=options.get("field_mappings", {}).get(dimension.api_name),
                )
            )
        for metric in metadata.metrics:
            if target_fields and metric.api_name not in target_fields:
                continue
            schema.append(
                FieldDefinition(
                    name=metric.api_name,
                    data_type="metric",
                    label=metric.ui_name,
                    mapped_name=options.get("field_mappings", {}).get(metric.api_name),
                )
            )
        return schema

    def fetch_field_metrics(self, user: User, schema: List[FieldDefinition], options) -> EntityInventory:
        client = self._authenticate(user)
        property_id = options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        metrics = options.get("metrics", ["totalUsers"])
        target_fields = options.get("fields")
        if not target_fields:
            target_fields = [field.name for field in schema]
        property_name = f"properties/{property_id}"
        total_records = self._run_total_records(client, property_name, metrics)
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in target_fields:
                continue
            if field.data_type == "metric":
                non_null = self._run_metric_sum(client, property_name, field.name)
            else:
                non_null = self._run_dimension_count(client, property_name, field.name, options)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        return EntityInventory(
            platform=self.get_name(),
            entity="users",
            total_records=total_records,
            fields=field_metrics,
        )

    def _run_total_records(self, client: BetaAnalyticsDataClient, property_name: str, metrics: Sequence[str]) -> int:

        metric_objs = [Metric(name=metric) for metric in metrics]
        request = RunReportRequest(property=property_name, metrics=metric_objs)
        response = client.run_report(request)
        if response.totals:
            first_metric = response.totals[0].metric_values[0]
            return int(first_metric.value or 0)
        return 0

    def _run_metric_sum(self, client: BetaAnalyticsDataClient, property_name: str, metric_name: str) -> int:

        request = RunReportRequest(property=property_name, metrics=[Metric(name=metric_name)])
        response = client.run_report(request)
        if response.totals:
            return int(response.totals[0].metric_values[0].value or 0)
        return 0

    def _run_dimension_count(
        self,
        client: BetaAnalyticsDataClient,
        property_name: str,
        dimension_name: str,
        options,
    ) -> int:

        filter_expression = FilterExpression(
            not_expression=FilterExpression(
                filter=Filter(
                    field_name=dimension_name,
                    string_filter=Filter.StringFilter(value="(not set)", match_type=Filter.StringFilter.MatchType.EXACT),
                )
            )
        )
        request = RunReportRequest(
            property=property_name,
            dimensions=[Dimension(name=dimension_name)],
            metrics=[self._default_metric(options)],
            dimension_filter=filter_expression,
        )
        response = client.run_report(request)
        if response.totals:
            return int(response.totals[0].metric_values[0].value or 0)
        return 0

    def _default_metric(self, options):

        metric_name = options.get("completeness_metric", "totalUsers")
        return Metric(name=metric_name)
