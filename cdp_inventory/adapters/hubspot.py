"""HubSpot connector built on the official hubspot-api-client SDK."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from hubspot import HubSpot
from hubspot.crm.objects import ApiException

from .base import BaseAdapter, EntityInventory, FieldDefinition, FieldMetrics
from ..types import User

LOGGER = logging.getLogger(__name__)


class HubSpotAdapter(BaseAdapter):
    """Collects schema metadata and volume metrics for HubSpot objects."""

    def __init__(self) -> None:
        super().__init__()

    def get_name(self) -> str:
        return "HubSpot"

    def _authenticate(self, user: User) -> HubSpot:
        """Instantiate an authenticated HubSpot client using the user's connection."""
        print("[HubSpot] _authenticate method called", flush=True)
        LOGGER.info("[HubSpot] Authenticating HubSpot client...")
        print("[HubSpot] Looking for HubSpot connection...", flush=True)
        connection = next((conn for conn in user.connections if conn.get("name") == "hubspot"), None)
        if connection is None:
            print("[HubSpot] ERROR: No HubSpot connection found", flush=True)
            raise ValueError("User does not have a HubSpot connection configured.")
        print(f"[HubSpot] Found connection, getting access_token...", flush=True)
        access_token = connection.get("access_token", "").strip()
        if not access_token:
            print("[HubSpot] ERROR: Access token is empty", flush=True)
            raise ValueError("HubSpot access token is required.")
        print(f"[HubSpot] Access token length: {len(access_token)} characters", flush=True)
        LOGGER.info(f"[HubSpot] Access token length: {len(access_token)} characters")
        print("[HubSpot] Creating HubSpot client instance...", flush=True)
        LOGGER.info("[HubSpot] Creating HubSpot client instance...")
        try:
            print("[HubSpot] Calling HubSpot(access_token=...) constructor...", flush=True)
            client = HubSpot(access_token=access_token)
            print("[HubSpot] HubSpot client created successfully", flush=True)
            LOGGER.info("[HubSpot] HubSpot client created successfully")
            return client
        except Exception as e:
            print(f"[HubSpot] ERROR creating HubSpot client: {type(e).__name__}: {str(e)}", flush=True)
            LOGGER.exception(f"[HubSpot] Error creating HubSpot client: {type(e).__name__}: {str(e)}")
            raise

    def fetch_schema(self, user: User, options) -> List[FieldDefinition]:
        print("[HubSpot] fetch_schema method called", flush=True)
        LOGGER.info("[HubSpot] fetch_schema called")
        print("[HubSpot] Step 1: Authenticating...", flush=True)
        LOGGER.info("[HubSpot] Step 1: Authenticating...")
        print("[HubSpot] About to call _authenticate(user)...", flush=True)
        client = self._authenticate(user)
        print("[HubSpot] _authenticate completed, got client", flush=True)
        object_type = options.get("object_type", "contacts")
        LOGGER.info(f"[HubSpot] Step 2: Fetching properties for object_type: {object_type}")
        properties_api = client.crm.properties.core_api
        LOGGER.info("[HubSpot] Step 3: Calling properties_api.get_all()...")
        try:
            response = properties_api.get_all(object_type=object_type)
            LOGGER.info("[HubSpot] Step 3: API call completed, processing response...")
            properties = response.results or []
            LOGGER.info(f"[HubSpot] Retrieved {len(properties)} properties from API")
        except ApiException as exc:
            LOGGER.exception(f"[HubSpot] ApiException during schema fetch: {exc}")
            error_msg = str(exc)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise ValueError(
                    "HubSpot authentication failed. Please verify your access token is correct and has not expired."
                ) from exc
            elif "403" in error_msg or "Forbidden" in error_msg:
                raise ValueError(
                    "HubSpot access denied. Please verify your access token has the required permissions."
                ) from exc
            else:
                raise ValueError(f"HubSpot API error: {exc.reason} - {exc.body}") from exc
        except Exception as exc:
            LOGGER.exception(f"[HubSpot] Unexpected error during schema fetch: {type(exc).__name__}: {str(exc)}")
            error_msg = str(exc)
            if "getheader" in error_msg or "HTTPResponse" in error_msg:
                raise ValueError(
                    "HubSpot API client compatibility error. This may be due to urllib3 version incompatibility. "
                    "Please ensure urllib3 < 2.0.0 is installed: pip install 'urllib3<2.0.0'"
                ) from exc
            else:
                raise ValueError(f"HubSpot API error: {error_msg}") from exc
        LOGGER.info("[HubSpot] Step 4: Building schema list...")
        schema = []
        for prop in properties:
            schema.append(
                FieldDefinition(
                    name=prop.name,
                    data_type=prop.type,
                    label=prop.label,
                    mapped_name=options.get("field_mappings", {}).get(prop.name),
                )
            )
        LOGGER.info(f"[HubSpot] Schema fetch complete. {len(schema)} fields defined")
        return schema

    def fetch_field_metrics(self, user: User, schema: List[FieldDefinition], options) -> EntityInventory:
        print("[HubSpot] fetch_field_metrics method called", flush=True)
        LOGGER.info("[HubSpot] fetch_field_metrics called")
        print("[HubSpot] Step 1: Authenticating...", flush=True)
        LOGGER.info("[HubSpot] Step 1: Authenticating...")
        print("[HubSpot] About to call _authenticate for fetch_field_metrics...", flush=True)
        client = self._authenticate(user)
        print("[HubSpot] Authentication complete for fetch_field_metrics", flush=True)
        object_type = options.get("object_type", "contacts")
        print(f"[HubSpot] Object type: {object_type}", flush=True)
        fields_to_profile = options.get("fields")
        if not fields_to_profile:
            fields_to_profile = [field.name for field in schema]
        
        # Print first 3 complete records to verify data
        self._print_complete_records(client, object_type, fields_to_profile)
        
        print(f"[HubSpot] Step 2: Iterating all records for {len(fields_to_profile)} fields: {fields_to_profile}", flush=True)
        LOGGER.info(f"[HubSpot] Step 2: Iterating all records for {len(fields_to_profile)} fields...")
        print("[HubSpot] About to call _iterate_records...", flush=True)
        total_records, non_null_counts = self._iterate_records(client, object_type, fields_to_profile, options)
        print(f"[HubSpot] _iterate_records completed: {total_records} total records", flush=True)
        LOGGER.info(f"[HubSpot] Step 3: Building field metrics from {len(schema)} schema fields...")
        field_metrics: List[FieldMetrics] = []
        for field in schema:
            if field.name not in fields_to_profile:
                continue
            non_null = non_null_counts.get(field.name, 0)
            completeness = (non_null / total_records) if total_records else None
            field_metrics.append(FieldMetrics(definition=field, non_null_count=non_null, completeness_pct=completeness))
        LOGGER.info(f"[HubSpot] fetch_field_metrics complete: {len(field_metrics)} field metrics created")
        return EntityInventory(
            platform=self.get_name(),
            entity=object_type,
            total_records=total_records,
            fields=field_metrics,
        )

    def _get_total_count(self, client: HubSpot, object_type: str, options) -> int:
        """Get total count of records efficiently by fetching just the first page."""
        basic_api = client.crm.objects.basic_api
        limit = 1  # Just need 1 record to get pagination info
        try:
            print("[HubSpot] Fetching first page to get total count...", flush=True)
            page = basic_api.get_page(
                object_type=object_type,
                properties=["id"],  # Only need id field
                limit=limit,
            )
            # Try to get total from pagination info
            paging = getattr(page, "paging", None)
            if paging:
                # Some HubSpot responses include total in paging
                total = getattr(paging, "total", None)
                if total:
                    print(f"[HubSpot] Got total from paging: {total}", flush=True)
                    return total
            
            # If no total in paging, we'll need to estimate or count pages
            # For now, we'll use a reasonable default or count by paginating
            # But to be fast, let's just fetch a few pages and estimate
            print("[HubSpot] Total not in paging, estimating from pagination...", flush=True)
            # Fetch a few pages to estimate
            after = None
            page_count = 0
            max_pages_to_check = 10
            for _ in range(max_pages_to_check):
                page = basic_api.get_page(
                    object_type=object_type,
                    properties=["id"],
                    limit=100,
                    after=after,
                )
                page_count += 1
                results = page.results or []
                if len(results) < 100:  # Last page
                    break
                paging = getattr(page, "paging", None)
                next_link = getattr(paging, "next", None) if paging else None
                after = getattr(next_link, "after", None) if next_link else None
                if after is None:
                    break
            
            # Estimate: if we got full pages, there are likely more
            # For now, return a large number or use the sample approach
            print(f"[HubSpot] Estimated {page_count} pages (at least {page_count * 100} records)", flush=True)
            # Return a placeholder - we'll use sample_size for the actual calculation
            return page_count * 100 if page_count > 0 else 0
        except Exception as e:
            print(f"[HubSpot] Error getting total count: {e}, using sample-based approach", flush=True)
            LOGGER.warning(f"[HubSpot] Could not get total count: {e}")
            return 0  # Will use sample size as total
    
    def _sample_records(
        self,
        client: HubSpot,
        object_type: str,
        fields: List[str],
        sample_size: int,
        options,
    ) -> Dict[str, int]:
        """Sample a limited number of records to estimate field completeness."""
        basic_api = client.crm.objects.basic_api
        limit = options.get("page_size", 100)
        after: Optional[str] = None
        records_processed = 0
        non_null_counts: Dict[str, int] = {field: 0 for field in fields}
        page_num = 0
        
        print(f"[HubSpot] Sampling up to {sample_size} records...", flush=True)
        LOGGER.info(f"[HubSpot] Sampling up to {sample_size} records...")
        
        while records_processed < sample_size:
            page_num += 1
            try:
                page = basic_api.get_page(
                    object_type=object_type,
                    properties=fields,
                    limit=min(limit, sample_size - records_processed),
                    after=after,
                )
            except ApiException as exc:
                LOGGER.exception(f"[HubSpot] ApiException during sampling: {exc}")
                raise ValueError(f"HubSpot API error during sampling: {exc.reason} - {exc.body}") from exc
            except Exception as exc:
                LOGGER.exception(f"[HubSpot] Unexpected error during sampling: {type(exc).__name__}: {str(exc)}")
                raise ValueError(f"Unexpected error during HubSpot sampling: {exc}") from exc
            
            results = page.results or []
            records_in_page = len(results)
            records_processed += records_in_page
            
            # Process records
            for record in results:
                properties = record.properties or {}
                for field in fields:
                    value = properties.get(field)
                    if value not in (None, ""):
                        non_null_counts[field] += 1
            
            if records_processed >= sample_size:
                print(f"[HubSpot] Reached sample size ({sample_size}). Stopping.", flush=True)
                break
            
            paging = getattr(page, "paging", None)
            next_link = getattr(paging, "next", None) if paging else None
            after = getattr(next_link, "after", None) if next_link else None
            if after is None:
                print(f"[HubSpot] No more pages available. Processed {records_processed} records.", flush=True)
                break
        
        print(f"[HubSpot] Sampling complete: processed {records_processed} records", flush=True)
        return non_null_counts
    
    def _iterate_records(
        self,
        client: HubSpot,
        object_type: str,
        fields: List[str],
        options,
    ) -> Tuple[int, Dict[str, int]]:

        print(f"[HubSpot] _iterate_records called for object_type: {object_type}, fields: {fields}", flush=True)
        LOGGER.info(f"[HubSpot] _iterate_records called for object_type: {object_type}, fields: {fields}")
        print("[HubSpot] Getting basic_api from client...", flush=True)
        basic_api = client.crm.objects.basic_api
        print("[HubSpot] Got basic_api", flush=True)
        limit = options.get("page_size", 100)
        print(f"[HubSpot] Page size: {limit}", flush=True)
        after: Optional[str] = None
        total_records = 0
        non_null_counts: Dict[str, int] = {field: 0 for field in fields}
        page_num = 0
        print(f"[HubSpot] Starting to iterate HubSpot {object_type} records (page_size={limit})...", flush=True)
        LOGGER.info(f"[HubSpot] Starting to iterate HubSpot {object_type} records (page_size={limit})...")
        while True:
            page_num += 1
            # Only print detailed logs every 100 pages to reduce noise
            should_log = page_num == 1 or page_num % 100 == 0
            try:
                page = basic_api.get_page(
                    object_type=object_type,
                    properties=fields,
                    limit=limit,
                    after=after,
                )
            except ApiException as exc:
                LOGGER.exception(f"[HubSpot] ApiException during pagination on page {page_num}: {exc}")
                raise ValueError(f"HubSpot API error during pagination: {exc.reason} - {exc.body}") from exc
            except Exception as exc:
                LOGGER.exception(f"[HubSpot] Unexpected error during pagination on page {page_num}: {type(exc).__name__}: {str(exc)}")
                raise ValueError(f"Unexpected error during HubSpot pagination: {exc}") from exc
            results = page.results or []
            records_in_page = len(results)
            total_records += records_in_page
            
            # Log progress every 100 pages (or first page)
            if should_log:
                print(f"[HubSpot] Page {page_num}: Retrieved {records_in_page} records (total so far: {total_records})", flush=True)
            LOGGER.info(f"[HubSpot] Page {page_num}: Retrieved {records_in_page} records (total so far: {total_records})")
            
            # Process records
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
                print(f"[HubSpot] Finished pagination. Total records processed: {total_records}", flush=True)
                LOGGER.info(f"[HubSpot] Finished pagination. Total records processed: {total_records}")
                break
        return total_records, non_null_counts
    
    def _print_complete_records(self, client: HubSpot, object_type: str, fields_to_profile: List[str]) -> None:
        """Print the first 3 complete records from HubSpot with all fields to verify data."""
        try:
            print(f"\n=== HubSpot Connection Info ===")
            print(f"Object Type: {object_type}")
            
            basic_api = client.crm.objects.basic_api
            
            # Query first 3 records with all fields we're profiling
            print(f"\n=== First 3 Complete {object_type} Records from HubSpot ===")
            print(f"Fields requested: {fields_to_profile}")
            
            try:
                page = basic_api.get_page(
                    object_type=object_type,
                    properties=fields_to_profile,
                    limit=3,
                )
                
                results = page.results or []
                
                if results:
                    for i, record in enumerate(results, 1):
                        print(f"\n  --- Record {i} ---")
                        properties = record.properties or {}
                        # Print ID if available
                        record_id = getattr(record, 'id', None)
                        if record_id:
                            print(f"    Id: {record_id}")
                        # Print all requested fields
                        for field in fields_to_profile:
                            value = properties.get(field)
                            print(f"    {field}: {value}")
                        # Show all properties for debugging
                        print(f"    All properties: {dict(properties)}")
                else:
                    print(f"  No records found in {object_type}")
            except ApiException as exc:
                print(f"\n--- Error fetching first 3 records (ApiException): {str(exc)} ---")
                LOGGER.warning(f"Error fetching first 3 records: {exc}")
            except Exception as e:
                print(f"\n--- Error fetching first 3 records: {str(e)} ---")
                LOGGER.warning(f"Error fetching first 3 records: {e}")
        except Exception as e:
            print(f"\n--- Error in _print_complete_records: {str(e)} ---")
            import traceback
            traceback.print_exc()
