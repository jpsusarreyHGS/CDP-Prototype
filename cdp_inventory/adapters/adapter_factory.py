from cdp_inventory.adapters.google_analytics import GoogleAnalyticsAdapter
from cdp_inventory.adapters.hubspot import HubSpotAdapter
from cdp_inventory.adapters.salesforce import SalesforceAdapter
from cdp_inventory.types import User


ADAPTER_REGISTRY = {
    "salesforce": SalesforceAdapter,
    "hubspot": HubSpotAdapter,
    "google_analytics": GoogleAnalyticsAdapter,
}


def get_adapters(user: User):
    """Returns list of adapters based on connections in the request body"""
    adapters = []
    connections = user.connections
    for connection in connections:
        adapter_cls = ADAPTER_REGISTRY.get(connection.get("name"))
        if adapter_cls:
            adapters.append(adapter_cls())
    return adapters