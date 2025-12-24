"""FastAPI router that wraps the inventory aggregation workflow."""
from __future__ import annotations

import argparse
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cdp_inventory.adapters.adapter_factory import get_adapters
from cdp_inventory.adapters.base import EntityInventory
from cdp_inventory.types import User

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = "config/config.yaml"

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryRequest(BaseModel):
    """Request model for inventory aggregation."""
    user: User
    options: Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Customer data platform inventory tool")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the configuration file that defines adapters and credentials.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()

@router.post(
    "",
    summary="Run data inventory aggregation",
    response_description="Inventory details per platform",
)
def run_inventory(request: InventoryRequest) -> Dict[str, Any]:
    """Execute the aggregation workflow and return normalized results."""
    user = request.user
    options = request.options
    
    print("=" * 50)
    print("run_inventory CALLED - starting inventory aggregation")
    print("=" * 50)
    LOGGER.info("run_inventory called - starting inventory aggregation")
    
    # Debug: Log raw connection objects to see what we're receiving
    print(f"Raw user.connections: {user.connections}")
    print(f"Number of connections: {len(user.connections)}")
    
    LOGGER.info(f"User connections: {[conn.get('name') or conn.get('type') for conn in user.connections]}")
    LOGGER.info(f"Options: {options}")
    print(f"User connections: {[conn.get('name') or conn.get('type') for conn in user.connections]}")
    print(f"Options: {options}")
    
    # Debug: Log connection details for each connection
    for i, conn in enumerate(user.connections):
        conn_name = conn.get('name') or conn.get('type') or 'unknown'
        print(f"Connection {i+1} ({conn_name}):")
        print(f"  Raw connection object: {conn}")
        print(f"  Keys: {list(conn.keys())}")
        print(f"  Values: {[(k, type(v).__name__) for k, v in conn.items()]}")
        
        # Check for camelCase variations
        if 'accessToken' in conn:
            print(f"  WARNING: Found 'accessToken' (camelCase) instead of 'access_token' (snake_case)")
            # Try to fix it
            conn['access_token'] = conn.pop('accessToken')
            print(f"  Fixed: Moved accessToken -> access_token")
        
        if conn_name == 'salesforce':
            # Log Salesforce connection details (masked)
            username = conn.get('username', '')
            password = conn.get('password', '')
            token = conn.get('security_token', '')
            print(f"  Username: {username}")
            print(f"  Password: {'***' + str(len(password)) if password else 'MISSING'}")
            print(f"  Security Token: {token[:4] + '***' + str(len(token)) if token else 'MISSING'}")
            print(f"  Domain (from options): {options.get('domain', 'NOT SET')}")
        elif conn_name == 'unknown' or not conn.get('name'):
            # Try to detect HubSpot connection by access_token
            if 'access_token' in conn or 'accessToken' in conn:
                print(f"  Detected HubSpot connection (has access_token), adding name field")
                conn['name'] = 'hubspot'
                if 'accessToken' in conn and 'access_token' not in conn:
                    conn['access_token'] = conn.pop('accessToken')
    
    # Get adapters based on user connections
    adapters = get_adapters(user)
    results: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    
    print(f"Processing {len(adapters)} adapters")
    LOGGER.info(f"Processing {len(adapters)} adapters")
    for idx, adapter in enumerate(adapters, 1):
        print(f"[Adapter {idx}/{len(adapters)}] Starting adapter processing...", flush=True)
        print(f"[Adapter {idx}/{len(adapters)}] Getting adapter name...", flush=True)
        try:
            adapter_name = adapter.get_name()
            print(f"[Adapter {idx}/{len(adapters)}] Adapter name retrieved: {adapter_name}", flush=True)
        except Exception as e:
            print(f"[Adapter {idx}/{len(adapters)}] ERROR getting adapter name: {e}", flush=True)
            raise
        print(f"[Adapter {idx}/{len(adapters)}] Processing adapter: {adapter_name}", flush=True)
        LOGGER.info(f"[Adapter {idx}/{len(adapters)}] Processing adapter: {adapter_name}")
        
        # Special handling for Salesforce: support multiple objects (object_names)
        if adapter_name == "Salesforce" and "object_names" in options:
            object_names = options.get("object_names", [])
            print(f"[Adapter {idx}/{len(adapters)}] Salesforce: Processing {len(object_names)} objects: {object_names}", flush=True)
            LOGGER.info(f"Salesforce: Processing {len(object_names)} objects: {object_names}")
            
            for object_name in object_names:
                # Create a copy of options with the specific object_name
                object_options = options.copy()
                object_options["object_name"] = object_name
                # Keep default fields or use object-specific fields if provided
                if "fields" not in object_options or not object_options.get("fields"):
                    # Default fields based on object type
                    if object_name == "Case":
                        # Note: Description is a long text field that can't be filtered, but we'll handle it gracefully
                        object_options["fields"] = ["Subject", "Description", "Status", "Priority", "Origin", "Type"]
                    else:  # Contact or other
                        object_options["fields"] = ["Email", "Phone", "FirstName", "LastName"]
                
                result_key = f"{adapter_name}-{object_name}"
                print(f"[Adapter {idx}/{len(adapters)}] Salesforce: Processing object '{object_name}'...", flush=True)
                try:
                    inventory = adapter.collect_inventory(user, object_options)
                    print(f"[Adapter {idx}/{len(adapters)}] Salesforce: '{object_name}' completed successfully!", flush=True)
                    LOGGER.info(f"Salesforce: '{object_name}' completed successfully!")
                    results[result_key] = inventory.to_dict()
                except ValueError as exc:
                    errors[result_key] = str(exc)
                    LOGGER.warning("Validation error for %s: %s", result_key, exc)
                except Exception as exc:  # pylint: disable=broad-except
                    error_msg = f"Unexpected error: {str(exc)}"
                    errors[result_key] = error_msg
                    LOGGER.exception("Unexpected error while aggregating inventory for %s", result_key)
        # Special handling for HubSpot: support multiple object types (object_types)
        elif adapter_name == "HubSpot" and "object_types" in options:
            object_types = options.get("object_types", [])
            print(f"[Adapter {idx}/{len(adapters)}] HubSpot: Processing {len(object_types)} object types: {object_types}", flush=True)
            LOGGER.info(f"HubSpot: Processing {len(object_types)} object types: {object_types}")
            
            for object_type in object_types:
                # Create a copy of options with the specific object_type
                object_options = options.copy()
                object_options["object_type"] = object_type
                # Keep default fields or use object-specific fields if provided
                if "fields" not in object_options or not object_options.get("fields"):
                    # Default fields based on object type
                    if object_type == "deals":
                        object_options["fields"] = ["dealname", "amount", "dealstage", "closedate", "pipeline"]
                    elif object_type == "tickets":
                        object_options["fields"] = ["subject", "content", "hs_pipeline_stage", "hs_ticket_priority", "createdate"]
                    else:  # contacts or other
                        object_options["fields"] = ["email", "phone", "firstname", "lastname"]
                
                result_key = f"{adapter_name}-{object_type}"
                print(f"[Adapter {idx}/{len(adapters)}] HubSpot: Processing object type '{object_type}'...", flush=True)
                try:
                    inventory = adapter.collect_inventory(user, object_options)
                    print(f"[Adapter {idx}/{len(adapters)}] HubSpot: '{object_type}' completed successfully!", flush=True)
                    LOGGER.info(f"HubSpot: '{object_type}' completed successfully!")
                    results[result_key] = inventory.to_dict()
                except ValueError as exc:
                    errors[result_key] = str(exc)
                    LOGGER.warning("Validation error for %s: %s", result_key, exc)
                except Exception as exc:  # pylint: disable=broad-except
                    error_msg = f"Unexpected error: {str(exc)}"
                    errors[result_key] = error_msg
                    LOGGER.exception("Unexpected error while aggregating inventory for %s", result_key)
        # Special handling for Google Analytics: support multiple metric views (metric_views)
        elif adapter_name == "Google Analytics" and "metric_views" in options:
            metric_views = options.get("metric_views", [])
            print(f"[Adapter {idx}/{len(adapters)}] Google Analytics: Processing {len(metric_views)} metric views: {metric_views}", flush=True)
            LOGGER.info(f"Google Analytics: Processing {len(metric_views)} metric views: {metric_views}")
            
            for metric_view in metric_views:
                # Create a copy of options with the specific metric view
                view_options = options.copy()
                view_options["metrics"] = [metric_view.get("metric", "totalUsers")]
                view_options["completeness_metric"] = metric_view.get("metric", "totalUsers")
                # Store displayName in options so it can be used later
                if "displayName" in metric_view:
                    view_options["_display_name"] = metric_view.get("displayName")
                # Use name for the result key (simpler, without description)
                result_key_name = metric_view.get("name") or metric_view.get("metric", "totalUsers")
                view_name = metric_view.get("displayName") or result_key_name
                
                # Use view-specific fields if provided, otherwise use default
                if "fields" in metric_view and metric_view.get("fields"):
                    view_options["fields"] = metric_view.get("fields")
                elif "fields" not in view_options or not view_options.get("fields"):
                    # Default fields for Google Analytics
                    view_options["fields"] = ["userPseudoId", "sessionSource", "eventName"]
                
                result_key = f"{adapter_name}-{result_key_name}"
                print(f"[Adapter {idx}/{len(adapters)}] Google Analytics: Processing metric view '{view_name}'...", flush=True)
                try:
                    inventory = adapter.collect_inventory(user, view_options)
                    print(f"[Adapter {idx}/{len(adapters)}] Google Analytics: '{view_name}' completed successfully!", flush=True)
                    LOGGER.info(f"Google Analytics: '{view_name}' completed successfully!")
                    inventory_dict = inventory.to_dict()
                    # Add display name to the result for frontend use
                    if "_display_name" in view_options:
                        inventory_dict["_display_name"] = view_options["_display_name"]
                    results[result_key] = inventory_dict
                except ValueError as exc:
                    errors[result_key] = str(exc)
                    LOGGER.warning("Validation error for %s: %s", result_key, exc)
                except Exception as exc:  # pylint: disable=broad-except
                    error_msg = f"Unexpected error: {str(exc)}"
                    errors[result_key] = error_msg
                    LOGGER.exception("Unexpected error while aggregating inventory for %s", result_key)
        else:
            # Standard processing for other adapters
            print(f"[Adapter {idx}/{len(adapters)}] About to call adapter.collect_inventory()...", flush=True)
            LOGGER.info(f"[Adapter {idx}/{len(adapters)}] About to call adapter.collect_inventory()...")
            try:
                print(f"[Adapter {idx}/{len(adapters)}] Calling collect_inventory now...", flush=True)
                print(f"[Adapter {idx}/{len(adapters)}] This may take a while for HubSpot API calls...", flush=True)
                inventory = adapter.collect_inventory(user, options)
                print(f"[Adapter {idx}/{len(adapters)}] collect_inventory completed successfully!")
                LOGGER.info(f"[Adapter {idx}/{len(adapters)}] collect_inventory completed successfully!")
                results[adapter_name] = inventory.to_dict()
            except ValueError as exc:
                # Validation errors (e.g., missing property_id, permission denied)
                errors[adapter_name] = str(exc)
                LOGGER.warning("Validation error for %s: %s", adapter_name, exc)
            except Exception as exc:  # pylint: disable=broad-except
                # Unexpected errors
                error_msg = f"Unexpected error: {str(exc)}"
                errors[adapter_name] = error_msg
                LOGGER.exception("Unexpected error while aggregating inventory for %s", adapter_name)
    
    # If all adapters failed, return an error
    if not results and errors:
        # If there's a validation error, return 400; otherwise 500
        # Check error messages for validation-related keywords
        has_validation_error = any(
            "permission" in err.lower() or "required" in err.lower() or "invalid" in err.lower()
            for err in errors.values()
        )
        status_code = 400 if has_validation_error else 500
        error_detail = "; ".join([f"{name}: {err}" for name, err in errors.items()])
        raise HTTPException(status_code=status_code, detail=error_detail)
    
    # Include errors in response if some adapters succeeded
    payload: Dict[str, Any] = results
    if errors:
        payload["_errors"] = errors
    
    return payload


