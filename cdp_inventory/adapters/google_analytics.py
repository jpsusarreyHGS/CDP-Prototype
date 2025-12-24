"""Google Analytics 4 connector using the Analytics Data API."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Sequence, Union

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
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


LOGGER = logging.getLogger(__name__)


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
            try:
                info = json.loads(service_account_info)
            except json.JSONDecodeError as e:
                LOGGER.error(f"Failed to parse service_account_info JSON: {e}")
                raise ValueError(f"Invalid JSON in service_account_info: {str(e)}") from e
            
            service_account_email = info.get("client_email", "unknown")
            LOGGER.info(f"Authenticating GA4 client with service account: {service_account_email}")
            
            # Validate and log private key format (without exposing the full key)
            private_key = info.get("private_key", "")
            if private_key:
                pk_preview = private_key[:50] + "..." if len(private_key) > 50 else private_key
                LOGGER.debug(f"Private key preview: {pk_preview}")
                LOGGER.debug(f"Private key length: {len(private_key)}")
                LOGGER.debug(f"Private key has newlines: {'\\n' in private_key or chr(10) in private_key}")
                # Check if it starts and ends correctly
                if not private_key.startswith("-----BEGIN"):
                    raise ValueError(
                        "Private key format error: Does not start with '-----BEGIN PRIVATE KEY-----'. "
                        "The private key may not be properly formatted."
                    )
                if not private_key.strip().endswith("-----END PRIVATE KEY-----"):
                    raise ValueError(
                        "Private key format error: Does not end with '-----END PRIVATE KEY-----'. "
                        "The private key may not be properly formatted."
                    )
            else:
                raise ValueError("Private key is missing from service account info")
            
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    info,
                    scopes=["https://www.googleapis.com/auth/analytics.readonly"],
                )
                LOGGER.info("GA4 authentication successful")
            except Exception as e:
                error_msg = str(e)
                LOGGER.error(f"GA4 authentication failed: {error_msg}")
                if "PEM" in error_msg or "InvalidByte" in error_msg or "cryptography" in error_msg.lower():
                    raise ValueError(
                        f"Private key parsing error: {error_msg}. "
                        "This usually means the private key format is incorrect. "
                        "Ensure your JSON request has the private key with \\n escape sequences for newlines, "
                        "and that the entire key (including BEGIN and END markers) is included."
                    ) from e
                raise
        else:
            path = Path(service_account_file).expanduser()
            # Try to read the email from the file for better error messages
            try:
                with open(path, 'r') as f:
                    file_info = json.load(f)
                    service_account_email = file_info.get("client_email", "unknown")
            except Exception:
                service_account_email = "unknown"
            credentials = service_account.Credentials.from_service_account_file(
                str(path),
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        # Store service account email for better error messages
        self._service_account_email = service_account_email
        
        # Create client and verify connection
        LOGGER.info("Creating GA4 BetaAnalyticsDataClient...")
        client = BetaAnalyticsDataClient(credentials=credentials)
        LOGGER.info(f"GA4 client created successfully. Service account: {service_account_email}")
        
        return client

    def fetch_schema(self, user: User, options) -> List[FieldDefinition]:
        LOGGER.info("=" * 60)
        LOGGER.info("Starting GA4 schema fetch")
        LOGGER.info("=" * 60)
        
        client = self._authenticate(user)
        LOGGER.info("Client authenticated, proceeding with schema fetch")
        
        property_id = options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        
        property_path = f"properties/{property_id}"
        LOGGER.info(f"Fetching GA4 metadata for property: {property_path}")
        LOGGER.debug(f"Options received: {json.dumps(options, indent=2)}")
        
        metadata_request = GetMetadataRequest(name=f"{property_path}/metadata")
        LOGGER.debug(f"Metadata request: {metadata_request.name}")
        
        try:
            metadata = client.get_metadata(metadata_request)
            LOGGER.info(f"✓ Successfully retrieved GA4 metadata")
            LOGGER.info(f"  - Total dimensions available: {len(metadata.dimensions)}")
            LOGGER.info(f"  - Total metrics available: {len(metadata.metrics)}")
            LOGGER.debug(f"  - Sample dimensions: {[d.api_name for d in metadata.dimensions[:5]]}")
            LOGGER.debug(f"  - Sample metrics: {[m.api_name for m in metadata.metrics[:5]]}")
        except Exception as e:
            service_account_email = getattr(self, '_service_account_email', 'unknown')
            error_msg = str(e)
            if "403" in error_msg or "permission" in error_msg.lower():
                raise ValueError(
                    f"Permission denied for property {property_id}. "
                    f"The service account '{service_account_email}' must be granted access to this property. "
                    f"Go to Google Analytics Admin → Property → Property access management and add this service account email with at least 'Viewer' role."
                ) from e
            raise
        target_fields = set(options.get("fields", []))
        LOGGER.info(f"Target fields requested: {list(target_fields) if target_fields else 'ALL FIELDS'}")
        
        schema: List[FieldDefinition] = []
        matched_fields = set()
        
        LOGGER.debug("Processing dimensions...")
        for dimension in metadata.dimensions:
            if target_fields and dimension.api_name not in target_fields:
                continue
            matched_fields.add(dimension.api_name)
            schema.append(
                FieldDefinition(
                    name=dimension.api_name,
                    data_type="dimension",
                    label=dimension.ui_name,
                    mapped_name=options.get("field_mappings", {}).get(dimension.api_name),
                )
            )
            LOGGER.debug(f"  ✓ Added dimension: {dimension.api_name} ({dimension.ui_name})")
        
        LOGGER.debug("Processing metrics...")
        for metric in metadata.metrics:
            if target_fields and metric.api_name not in target_fields:
                continue
            matched_fields.add(metric.api_name)
            schema.append(
                FieldDefinition(
                    name=metric.api_name,
                    data_type="metric",
                    label=metric.ui_name,
                    mapped_name=options.get("field_mappings", {}).get(metric.api_name),
                )
            )
            LOGGER.debug(f"  ✓ Added metric: {metric.api_name} ({metric.ui_name})")
        
        # Warn if requested fields don't exist in GA4
        if target_fields:
            unmatched_fields = target_fields - matched_fields
            if unmatched_fields:
                LOGGER.warning(
                    f"⚠ Requested fields not found in GA4: {unmatched_fields}. "
                    f"GA4 uses different field names (e.g., 'userPseudoId', 'sessionSource', 'eventName'). "
                    f"To see all available fields, omit the 'fields' parameter or use valid GA4 field names."
                )
        
        LOGGER.info(f"Schema fetch complete. Returning {len(schema)} fields ({len([s for s in schema if s.data_type == 'dimension'])} dimensions, {len([s for s in schema if s.data_type == 'metric'])} metrics)")
        LOGGER.info("=" * 60)
        
        return schema

    def fetch_field_metrics(self, user: User, schema: List[FieldDefinition], options) -> EntityInventory:
        LOGGER.info("=" * 60)
        LOGGER.info("Starting GA4 field metrics fetch")
        LOGGER.info("=" * 60)
        
        client = self._authenticate(user)
        LOGGER.info("Client authenticated, proceeding with metrics fetch")
        
        property_id = options.get("property_id")
        if not property_id:
            raise ValueError("property_id is required for Google Analytics connector.")
        
        property_name = f"properties/{property_id}"
        LOGGER.info(f"Property: {property_name}")
        
        metrics = options.get("metrics", ["totalUsers"])
        LOGGER.info(f"Metrics for total records calculation: {metrics}")
        
        target_fields = options.get("fields")
        if not target_fields:
            target_fields = [field.name for field in schema]
        LOGGER.info(f"Target fields to process: {len(target_fields)} fields")
        LOGGER.debug(f"Field names: {target_fields}")
        
        try:
            LOGGER.info("Fetching total records...")
            total_records = self._run_total_records(client, property_name, metrics, options)
            LOGGER.info(f"✓ Total records retrieved: {total_records}")
        except Exception as e:
            service_account_email = getattr(self, '_service_account_email', 'unknown')
            error_msg = str(e)
            if "403" in error_msg or "permission" in error_msg.lower():
                raise ValueError(
                    f"Permission denied for property {property_id}. "
                    f"The service account '{service_account_email}' must be granted access to this property. "
                    f"Go to Google Analytics Admin → Property → Property access management and add this service account email with at least 'Viewer' role."
                ) from e
            raise
        field_metrics: List[FieldMetrics] = []
        LOGGER.info(f"Processing {len([f for f in schema if f.name in target_fields])} fields for metrics...")
        
        for idx, field in enumerate(schema, 1):
            if field.name not in target_fields:
                continue
            
            LOGGER.info(f"[{idx}/{len([f for f in schema if f.name in target_fields])}] Processing field: {field.name} ({field.data_type})")
            
            if field.data_type == "metric":
                LOGGER.debug(f"  Fetching metric sum for {field.name}...")
                non_null = self._run_metric_sum(client, property_name, field.name, options)
                LOGGER.info(f"  ✓ Metric {field.name}: {non_null}")
            else:
                LOGGER.debug(f"  Fetching dimension count for {field.name}...")
                non_null = self._run_dimension_count(client, property_name, field.name, options)
                LOGGER.info(f"  ✓ Dimension {field.name} non-null count: {non_null}")
            
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
            completeness_str = f"{completeness:.4f}" if completeness is not None else "N/A"
            LOGGER.debug(f"  Completeness: {completeness_str}")
        
        LOGGER.info(f"✓ Processed {len(field_metrics)} fields successfully")
        LOGGER.info("=" * 60)
        LOGGER.info("GA4 field metrics fetch complete")
        LOGGER.info(f"Final result: {total_records} total records, {len(field_metrics)} fields")
        LOGGER.info("=" * 60)
        
        return EntityInventory(
            platform=self.get_name(),
            entity="users",
            total_records=total_records,
            fields=field_metrics,
        )

    def _run_total_records(self, client: BetaAnalyticsDataClient, property_name: str, metrics: Sequence[str], options) -> int:

        metric_objs = [Metric(name=metric) for metric in metrics]
        date_ranges = self._get_date_ranges(options)
        date_range_str = f"{date_ranges[0].start_date} to {date_ranges[0].end_date}" if date_ranges else "no date range"
        LOGGER.info(f"Querying GA4 property {property_name} for metrics {metrics} (date range: {date_range_str})")
        LOGGER.debug(f"  Request details: property={property_name}, metrics={[m.name for m in metric_objs]}")
        
        request = RunReportRequest(property=property_name, metrics=metric_objs, date_ranges=date_ranges)
        print(f"[DEBUG] Sending RunReportRequest to GA4 API...")
        print(f"[DEBUG]   Request property: {request.property}")
        print(f"[DEBUG]   Request metrics: {[m.name for m in request.metrics]}")
        print(f"[DEBUG]   Request date_ranges: {[(dr.start_date, dr.end_date) for dr in request.date_ranges]}")
        LOGGER.info(f"Sending RunReportRequest: property={request.property}, metrics={[m.name for m in request.metrics]}, date_ranges={[(dr.start_date, dr.end_date) for dr in request.date_ranges]}")
        
        try:
            response = client.run_report(request)
            print(f"[DEBUG] ✓ GA4 API response received")
            LOGGER.info("✓ GA4 API response received")
        except Exception as e:
            print(f"[ERROR] ✗ GA4 API call failed: {type(e).__name__}: {str(e)}")
            print(f"[ERROR]   Error details: {repr(e)}")
            LOGGER.error(f"✗ GA4 API call failed: {type(e).__name__}: {str(e)}")
            LOGGER.error(f"  Error details: {repr(e)}")
            raise
        
        # Detailed response inspection
        has_totals = bool(response.totals)
        row_count = len(response.rows) if hasattr(response, 'rows') and response.rows else 0
        dimension_headers = [h.name for h in response.dimension_headers] if hasattr(response, 'dimension_headers') and response.dimension_headers else []
        metric_headers = [h.name for h in response.metric_headers] if hasattr(response, 'metric_headers') and response.metric_headers else []
        
        print(f"[DEBUG] Response details:")
        print(f"[DEBUG]   - Has totals: {has_totals}")
        print(f"[DEBUG]   - Row count: {row_count}")
        print(f"[DEBUG]   - Dimension headers: {dimension_headers}")
        print(f"[DEBUG]   - Metric headers: {metric_headers}")
        print(f"[DEBUG]   - Response object type: {type(response)}")
        LOGGER.info(f"  Response details:")
        LOGGER.info(f"    - Has totals: {has_totals}")
        LOGGER.info(f"    - Row count: {row_count}")
        LOGGER.info(f"    - Dimension headers: {dimension_headers}")
        LOGGER.info(f"    - Metric headers: {metric_headers}")
        LOGGER.debug(f"    - Response object type: {type(response)}")
        LOGGER.debug(f"    - Response attributes: {dir(response)}")
        
        # Log first few rows if they exist
        if hasattr(response, 'rows') and response.rows:
            print(f"[DEBUG]   - Sample rows (first 3):")
            LOGGER.info(f"    - Sample rows (first 3):")
            for i, row in enumerate(response.rows[:3], 1):
                dimension_values = [dv.value for dv in row.dimension_values] if hasattr(row, 'dimension_values') else []
                metric_values = [mv.value for mv in row.metric_values] if hasattr(row, 'metric_values') else []
                print(f"[DEBUG]     Row {i}: dimensions={dimension_values}, metrics={metric_values}")
                LOGGER.info(f"      Row {i}: dimensions={dimension_values}, metrics={metric_values}")
        
        # Log totals details
        # GA4 returns data in 'totals' when there are dimensions, but in 'rows' when there are no dimensions
        if response.totals:
            print(f"[DEBUG]   - Totals found: {len(response.totals)} total row(s)")
            LOGGER.info(f"    - Totals found: {len(response.totals)} total row(s)")
            for i, total in enumerate(response.totals, 1):
                print(f"[DEBUG]     Total {i}:")
                LOGGER.info(f"      Total {i}:")
                if hasattr(total, 'metric_values') and total.metric_values:
                    for j, metric_value in enumerate(total.metric_values, 1):
                        metric_name = metric_headers[j-1] if j <= len(metric_headers) else f"metric_{j}"
                        print(f"[DEBUG]       {metric_name}: {metric_value.value} (raw type: {type(metric_value.value)})")
                        LOGGER.info(f"        {metric_name}: {metric_value.value} (raw type: {type(metric_value.value)})")
            
            first_metric = response.totals[0].metric_values[0]
            raw_value = first_metric.value
            # Handle both integer and float values - convert to float first, then round to 2 decimal places
            if raw_value:
                try:
                    value = round(float(raw_value), 2)
                except (ValueError, TypeError):
                    value = 0
            else:
                value = 0
            LOGGER.info(f"  ✓ Total records (from {metrics[0]}): {value} (raw: {raw_value})")
            LOGGER.debug(f"    - Total rows in response: {len(response.totals)}")
            return value
        elif response.rows and len(response.rows) > 0:
            # When there are no dimensions, GA4 returns data in rows instead of totals
            print(f"[DEBUG]   - No totals, but found {len(response.rows)} row(s) - using first row for totals")
            LOGGER.info(f"    - No totals, but found {len(response.rows)} row(s) - using first row for totals")
            
            first_row = response.rows[0]
            if hasattr(first_row, 'metric_values') and first_row.metric_values:
                first_metric = first_row.metric_values[0]
                raw_value = first_metric.value
                # Handle both integer and float values - convert to float first, then round to 2 decimal places
                if raw_value:
                    try:
                        value = round(float(raw_value), 2)
                    except (ValueError, TypeError):
                        value = 0
                else:
                    value = 0
                print(f"[DEBUG]   ✓ Total records from first row (metric {metrics[0]}): {value} (raw: {raw_value})")
                LOGGER.info(f"  ✓ Total records (from {metrics[0]}): {value} (raw: {raw_value})")
                return value
        else:
            print(f"[WARNING] ⚠ No totals in GA4 response for property {property_name}")
            print(f"[WARNING]   Response has rows: {bool(hasattr(response, 'rows') and response.rows)}")
            print(f"[WARNING]   Row count: {row_count}")
            print(f"[WARNING]   Metric headers: {metric_headers}")
            print(f"[WARNING]   Dimension headers: {dimension_headers}")
            LOGGER.warning(f"⚠ No totals in GA4 response for property {property_name}")
            LOGGER.warning(f"  This may indicate:")
            LOGGER.warning(f"    1. No data exists in the date range: {date_range_str}")
            LOGGER.warning(f"    2. Property ID {property_name} is incorrect")
            LOGGER.warning(f"    3. Property has no traffic/events configured")
            
            # Additional debugging: check if response has any other useful info
            print(f"[DEBUG]   Checking response attributes...")
            if hasattr(response, 'row_count'):
                print(f"[DEBUG]   - Response row_count attribute: {response.row_count}")
                LOGGER.debug(f"    - Response row_count attribute: {response.row_count}")
            if hasattr(response, 'kind'):
                print(f"[DEBUG]   - Response kind: {response.kind}")
                LOGGER.debug(f"    - Response kind: {response.kind}")
            if hasattr(response, 'metadata'):
                print(f"[DEBUG]   - Response metadata: {response.metadata}")
                LOGGER.debug(f"    - Response metadata: {response.metadata}")
            
            # Try to see what's actually in the response
            print(f"[DEBUG]   Full response object: {response}")
            print(f"[DEBUG]   Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            return 0

    def _run_metric_sum(self, client: BetaAnalyticsDataClient, property_name: str, metric_name: str, options) -> Union[int, float]:

        date_ranges = self._get_date_ranges(options)
        date_range_str = f"{date_ranges[0].start_date} to {date_ranges[0].end_date}" if date_ranges else "no date range"
        LOGGER.debug(f"  Querying metric '{metric_name}' for property {property_name} (date range: {date_range_str})")
        
        request = RunReportRequest(property=property_name, metrics=[Metric(name=metric_name)], date_ranges=date_ranges)
        
        try:
            response = client.run_report(request)
            LOGGER.debug(f"    API response received for metric {metric_name}")
        except Exception as e:
            LOGGER.error(f"    ✗ API call failed for metric {metric_name}: {type(e).__name__}: {str(e)}")
            raise
        
        LOGGER.debug(f"    Response has totals: {bool(response.totals)}")
        LOGGER.debug(f"    Response has rows: {bool(hasattr(response, 'rows') and response.rows)}")
        
        if response.totals:
            raw_value = response.totals[0].metric_values[0].value
            # Handle both integer and float values - convert to float first, then round to 2 decimal places
            if raw_value:
                try:
                    value = round(float(raw_value), 2)
                except (ValueError, TypeError):
                    value = 0
            else:
                value = 0
            LOGGER.debug(f"    Metric {metric_name}: {value} (raw: {raw_value}, type: {type(raw_value)})")
            return value
        elif response.rows and len(response.rows) > 0:
            # When there are no dimensions, GA4 returns data in rows instead of totals
            first_row = response.rows[0]
            if hasattr(first_row, 'metric_values') and first_row.metric_values:
                raw_value = first_row.metric_values[0].value
                # Handle both integer and float values - convert to float first, then round to 2 decimal places
                if raw_value:
                    try:
                        value = round(float(raw_value), 2)
                    except (ValueError, TypeError):
                        value = 0
                else:
                    value = 0
                LOGGER.debug(f"    Metric {metric_name} (from row): {value} (raw: {raw_value}, type: {type(raw_value)})")
                return value
        
        LOGGER.warning(f"    ⚠ No totals or rows for metric {metric_name}, returning 0")
        LOGGER.debug(f"    Response details: totals={response.totals}, rows={len(response.rows) if hasattr(response, 'rows') and response.rows else 0}")
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
        date_ranges = self._get_date_ranges(options)
        request = RunReportRequest(
            property=property_name,
            dimensions=[Dimension(name=dimension_name)],
            metrics=[self._default_metric(options)],
            dimension_filter=filter_expression,
            date_ranges=date_ranges,
        )
        response = client.run_report(request)
        if response.totals:
            raw_value = response.totals[0].metric_values[0].value
            # Handle both integer and float values - convert to float first, then round to 2 decimal places
            if raw_value:
                try:
                    return round(float(raw_value), 2)
                except (ValueError, TypeError):
                    return 0
            return 0
        return 0

    def _get_date_ranges(self, options) -> List[DateRange]:
        """Get date ranges from options or use default (last 365 days)."""
        date_ranges = options.get("date_ranges")
        if date_ranges:
            # If provided, expect list of dicts with 'start_date' and 'end_date'
            return [
                DateRange(start_date=dr.get("start_date"), end_date=dr.get("end_date"))
                for dr in date_ranges
            ]
        # Default: last 365 days
        # Use "365daysAgo" and "today" as relative dates
        return [DateRange(start_date="365daysAgo", end_date="today")]

    def _default_metric(self, options):

        metric_name = options.get("completeness_metric", "totalUsers")
        return Metric(name=metric_name)
