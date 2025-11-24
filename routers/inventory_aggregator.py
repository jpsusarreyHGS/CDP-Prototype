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
        options: Annotated[Dict[str, str], Body(..., embed=True)],
        adapters = Depends(get_adapters),
    ) -> Dict[str, Any]:
    """Execute the aggregation workflow and return normalized results."""
    try:
        results: Dict[str, EntityInventory] = {}
        for adapter in adapters:
            results[adapter.get_name()] = adapter.collect_inventory(user, options)
        payload = {name: inventory.to_dict() for name, inventory in results.items()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Unexpected error while aggregating inventory")
        raise HTTPException(status_code=500, detail="Failed to aggregate inventory.") from exc
    return payload

