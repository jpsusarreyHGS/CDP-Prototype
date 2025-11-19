"""Google Analytics 4 connector using the Analytics Data API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .base import BaseConnector, EntityInventory, FieldDefinition, FieldMetrics


class GoogleAnalyticsConnector(BaseConnector):
    """Fetches GA4 metadata and basic user volume metrics."""

    def __init__(self, name: str, credentials: Dict[str, str], options: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name=name, credentials=credentials, options=options)
        self.client = None

    def authenticate(self) -> None:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.oauth2 import service_account

        service_account_info = self.credentials.get("service_account_info")
        service_account_file = self.credentials.get("service_account_file")
        if not service_account_info and not service_account_file:
            raise ValueError("Either service_account_info or service_account_file must be provided for GA4.")
        if service_account_info:
            info = json.loads(service_account_info)
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
        else:
            path = Path(service_account_file).expanduser()
            credentials = service_account.Credentials.from_service_account_file(
                str(path), scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
        self.client = BetaAnalyticsDataClient(credentials=credentials)

    def fetch_schema(self) -> List[FieldDefinition]:
        if self.client is None:
            raise RuntimeError("Google Analytics client has not been authenticated.")
        from google.analytics.data_v1beta.types import GetMetadataRequest

        property_id = self.options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        metadata_request = GetMetadataRequest(name=f"properties/{property_id}/metadata")
        metadata = self.client.get_metadata(metadata_request)
        target_fields = set(self.options.get("fields", []))
        schema: List[FieldDefinition] = []
        for dimension in metadata.dimensions:
            if target_fields and dimension.api_name not in target_fields:
                continue
            schema.append(
                FieldDefinition(
                    name=dimension.api_name,
                    data_type="dimension",
                    label=dimension.ui_name,
                    mapped_name=self.options.get("field_mappings", {}).get(dimension.api_name),
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
                    mapped_name=self.options.get("field_mappings", {}).get(metric.api_name),
                )
            )
        return schema

    def fetch_field_metrics(self, schema: List[FieldDefinition]) -> EntityInventory:
        if self.client is None:
            raise RuntimeError("Google Analytics client has not been authenticated.")
        from google.analytics.data_v1beta.types import (
            Filter,
            FilterExpression,
            Metric,
            Dimension,
            RunReportRequest,
        )

        property_id = self.options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        metrics = self.options.get("metrics", ["totalUsers"])
        target_fields = self.options.get("fields")
        if not target_fields:
            target_fields = [field.name for field in schema]
        property_name = f"properties/{property_id}"
        total_records = self._run_total_records(property_name, metrics)
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in target_fields:
                continue
            if field.data_type == "metric":
                non_null = self._run_metric_sum(property_name, field.name)
            else:
                non_null = self._run_dimension_count(property_name, field.name)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        return EntityInventory(platform=self.name, entity="users", total_records=total_records, fields=field_metrics)

    def _run_total_records(self, property_name: str, metrics: Sequence[str]) -> int:
        from google.analytics.data_v1beta.types import Metric, RunReportRequest

        metric_objs = [Metric(name=metric) for metric in metrics]
        request = RunReportRequest(property=property_name, metrics=metric_objs)
        response = self.client.run_report(request)
        if response.totals:
            first_metric = response.totals[0].metric_values[0]
            return int(first_metric.value or 0)
        return 0

    def _run_metric_sum(self, property_name: str, metric_name: str) -> int:
        from google.analytics.data_v1beta.types import Metric, RunReportRequest

        request = RunReportRequest(property=property_name, metrics=[Metric(name=metric_name)])
        response = self.client.run_report(request)
        if response.totals:
            return int(response.totals[0].metric_values[0].value or 0)
        return 0

    def _run_dimension_count(self, property_name: str, dimension_name: str) -> int:
        from google.analytics.data_v1beta.types import (
            Dimension,
            Filter,
            FilterExpression,
            RunReportRequest,
        )

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
            metrics=[self._default_metric()],
            dimension_filter=filter_expression,
        )
        response = self.client.run_report(request)
        if response.totals:
            return int(response.totals[0].metric_values[0].value or 0)
        return 0

    def _default_metric(self):
        from google.analytics.data_v1beta.types import Metric

        metric_name = self.options.get("completeness_metric", "totalUsers")
        return Metric(name=metric_name)
