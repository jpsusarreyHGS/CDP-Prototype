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
        import logging
        logger = logging.getLogger(__name__)
        
        connection = [dict for dict in user.connections if "salesforce" == dict.get("name")]
        if not connection:
            raise ValueError("No Salesforce connection found in user connections.")
        
        credentials = connection[0]
        # Trim whitespace from credentials to avoid authentication issues
        username = credentials.get("username", "").strip() if credentials.get("username") else ""
        password = credentials.get("password", "").strip() if credentials.get("password") else ""
        security_token = credentials.get("security_token", "").strip() if credentials.get("security_token") else ""
        domain = options.get("domain", "login")
        
        logger.info(f"Salesforce authentication attempt - Username: {username}, Domain: {domain}")
        logger.debug(f"Security token present: {bool(security_token)}, Password present: {bool(password)}")
        
        if not all([username, password, security_token]):
            missing = [k for k, v in {"username": username, "password": password, "security_token": security_token}.items() if not v]
            raise ValueError(f"Salesforce credentials are incomplete. Missing: {', '.join(missing)}")
        
        try:
            return Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Salesforce authentication failed: {error_msg}")
            # Provide more helpful error message
            if "INVALID_LOGIN" in error_msg:
                raise ValueError(
                    "Salesforce authentication failed. Please verify:\n"
                    "1. Username is correct\n"
                    "2. Password is correct\n"
                    "3. Security token is correct (reset it if needed)\n"
                    "4. Account is not locked out\n"
                    f"Error: {error_msg}"
                ) from e
            raise

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
        
        # Print first 3 complete records with all fields to verify data
        self._print_complete_records(client, object_name, fields_to_profile)
        
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
        """Fetch non-null count for a field. Handles fields that cannot be filtered in WHERE clauses."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Try the standard approach: COUNT with WHERE clause
            query = f"SELECT COUNT() FROM {object_name} WHERE {field_name} != null"
            result = client.query(query)
            records = result.get("records", [])
            if records:
                key = next(iter(records[0]))
                return int(records[0][key])
            return int(result.get("totalSize", 0))
        except Exception as e:
            # Check if this is a "field cannot be filtered" error
            error_msg = str(e)
            if "can not be filtered" in error_msg or "INVALID_FIELD" in error_msg:
                logger.warning(f"Field '{field_name}' cannot be filtered in WHERE clause. Attempting alternative count method...")
                # For fields that can't be filtered (like long text areas), count non-nulls by fetching records
                # We'll sample records to avoid performance issues with large datasets
                try:
                    # Fetch records with this field and count non-nulls in memory
                    # Use a reasonable limit to avoid performance issues
                    batch_size = 2000
                    query = f"SELECT {field_name} FROM {object_name} LIMIT {batch_size}"
                    result = client.query(query)
                    records = result.get("records", [])
                    non_null_count = sum(1 for record in records if record.get(field_name) is not None)
                    
                    # If we got fewer records than the limit, we've counted all records
                    total_size = result.get("totalSize", 0)
                    if len(records) < batch_size or len(records) >= total_size:
                        logger.info(f"Field '{field_name}': Counted {non_null_count} non-nulls from {len(records)} records (complete count)")
                        return non_null_count
                    else:
                        # We only sampled, so estimate based on sample
                        # This is an approximation - for exact counts, would need to fetch all records
                        logger.warning(f"Field '{field_name}': Sampled {non_null_count} non-nulls from {len(records)} records (approximation, total records: {total_size})")
                        # Return the sampled count as an approximation
                        # Note: This is not exact, but gives a reasonable estimate
                        return non_null_count
                except Exception as e2:
                    logger.error(f"Failed to count non-nulls for field '{field_name}' using alternative method: {e2}")
                    # If alternative method also fails, return 0
                    return 0
            else:
                # Re-raise if it's a different error
                raise
    
    def _print_complete_records(self, client, object_name: str, fields_to_profile: List[str]) -> None:
        """Print the first 3 complete records from Salesforce with all fields to verify data."""
        try:
            # Show which Salesforce org we're connected to
            print(f"\n=== Salesforce Connection Info ===")
            print(f"Salesforce Base URL: {client.base_url}")
            print(f"API Version: {client.sf_version}")
            
            # Query first 3 records with all fields we're profiling
            fields_str = ", ".join(["Id"] + fields_to_profile)
            query = f"SELECT {fields_str} FROM {object_name} LIMIT 3"
            
            print(f"\n=== First 3 Complete {object_name} Records from Salesforce ===")
            print(f"Query: {query}")
            
            result = client.query(query)
            records = result.get("records", [])
            
            if records:
                for i, record in enumerate(records, 1):
                    print(f"\n  --- Record {i} ---")
                    print(f"    Id: {record.get('Id')}")
                    for field in fields_to_profile:
                        value = record.get(field)
                        print(f"    {field}: {value}")
                    # Show the raw record dict
                    print(f"    Raw record dict: {dict(record)}")
            else:
                print(f"  No records found in {object_name}")
        except Exception as e:
            print(f"\n--- Error fetching complete records: {str(e)} ---")
            import traceback
            traceback.print_exc()