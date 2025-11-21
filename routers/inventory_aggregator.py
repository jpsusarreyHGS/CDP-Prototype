"""FastAPI router that wraps the inventory aggregation workflow."""
from __future__ import annotations

import argparse
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from cdp_inventory.aggregator.inventory_runner import InventoryAggregator

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = "config/config.yaml"

router = APIRouter(prefix="/inventory", tags=["inventory"])

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Customer data platform inventory tool")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the configuration file that defines connectors and credentials.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()

@router.get(
    "",
    summary="Run data inventory aggregation",
    response_description="Inventory details per platform",
)
def run_inventory() -> Dict[str, Any]:
    """Execute the aggregation workflow and return normalized results."""
    try:
        args = parse_args()
        aggregator = InventoryAggregator(config_path=args.config)
        results = aggregator.run()
        payload = {name: inventory.to_dict() for name, inventory in results.items()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Unexpected error while aggregating inventory")
        raise HTTPException(status_code=500, detail="Failed to aggregate inventory.") from exc
    return payload


