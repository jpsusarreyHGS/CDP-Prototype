"""CLI entry point for running the data inventory aggregation."""
from __future__ import annotations

import argparse
import logging
import sys

from cdp_inventory.aggregator.inventory_runner import InventoryAggregator


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


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    aggregator = InventoryAggregator(config_path=args.config)
    results = aggregator.run()
    print(aggregator.to_json(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
