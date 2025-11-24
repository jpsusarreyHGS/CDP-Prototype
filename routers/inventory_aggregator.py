"""FastAPI router that wraps the inventory aggregation workflow."""
from __future__ import annotations

import argparse
import logging
from typing import Any, Dict, Annotated

from fastapi import APIRouter, HTTPException, Depends, Body

from cdp_inventory.adapters.adapter_factory import get_adapters
from cdp_inventory.adapters.base import EntityInventory
from cdp_inventory.types import User

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = "config/config.yaml"

router = APIRouter(prefix="/inventory", tags=["inventory"])

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
def run_inventory(
        user: User,
        options: Annotated[Dict[str, Any], Body(..., embed=True)],
        adapters = Depends(get_adapters),
    ) -> Dict[str, Any]:
    """Execute the aggregation workflow and return normalized results."""
    results: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    
    for adapter in adapters:
        adapter_name = adapter.get_name()
        try:
            inventory = adapter.collect_inventory(user, options)
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


