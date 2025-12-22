import json
from typing import Optional
from cdp_inventory.adapters.google_analytics import GoogleAnalyticsAdapter
from cdp_inventory.adapters.hubspot import HubSpotAdapter
from cdp_inventory.adapters.salesforce import SalesforceAdapter
from cdp_inventory.types import User


ADAPTER_REGISTRY = {
    "salesforce": SalesforceAdapter,
    "hubspot": HubSpotAdapter,
    "google_analytics": GoogleAnalyticsAdapter,
}


def _detect_adapter_name(connection: dict) -> Optional[str]:
    """Detect adapter name from connection object.
    
    Checks for 'name' field first (preserves existing behavior for Salesforce/HubSpot),
    then falls back to detecting by connection type or service account fields for Google Analytics.
    """
    # First check for explicit name - this preserves existing behavior
    # Salesforce and HubSpot connections with name="salesforce" or name="hubspot" will work as before
    name = connection.get("name")
    if name and name in ADAPTER_REGISTRY:
        return name
    
    # Fallback detection (only runs if 'name' is not present):
    # Check for Google Analytics service account by type and specific fields
    conn_type = connection.get("type")
    if conn_type == "service_account":
        # Check if it's a Google service account by looking for Google-specific fields
        if "client_email" in connection and "iam.gserviceaccount.com" in connection.get("client_email", ""):
            return "google_analytics"
    
    # Note: We don't do fallback detection for Salesforce/HubSpot because:
    # 1. They require explicit 'name' field in their adapters
    # 2. Their credential fields could overlap with other platforms
    # 3. Existing connections always have 'name' field, so this won't affect them
    
    return None


def get_adapters(user: User):
    """Returns list of adapters based on connections in the request body"""
    adapters = []
    connections = user.connections
    for connection in connections:
        adapter_name = _detect_adapter_name(connection)
        if adapter_name:
            adapter_cls = ADAPTER_REGISTRY.get(adapter_name)
            if adapter_cls:
                # For Google Analytics, normalize the connection format if needed
                if adapter_name == "google_analytics" and not connection.get("service_account_info") and not connection.get("service_account_file"):
                    # Convert direct service account fields to service_account_info format
                    if "private_key" in connection and "client_email" in connection:
                        # Get and normalize the private key
                        private_key = connection.get("private_key", "")
                        
                        # Ensure the private key has proper newlines
                        # Handle different escape scenarios:
                        # - JSON with \\n becomes literal \n (backslash+n) in Python
                        # - JSON with \\\\n becomes literal \\n (double backslash+n) in Python  
                        # - We need to convert any literal backslash+n sequences to actual newlines
                        
                        import re
                        # Replace any sequence of backslashes followed by 'n' with actual newline
                        # This handles: \n, \\n, \\\\n, etc. - converts all to actual newlines
                        private_key = re.sub(r'\\+n', '\n', private_key)
                        
                        # Validate private key format
                        if not private_key.startswith("-----BEGIN"):
                            raise ValueError(
                                "Private key format is invalid. It should start with '-----BEGIN PRIVATE KEY-----'. "
                                "Ensure the private key in your JSON request uses \\n for newlines."
                            )
                        if not private_key.endswith("-----END PRIVATE KEY-----\n") and not private_key.endswith("-----END PRIVATE KEY-----"):
                            raise ValueError(
                                "Private key format is invalid. It should end with '-----END PRIVATE KEY-----'. "
                                "Ensure the private key in your JSON request uses \\n for newlines."
                            )
                        
                        service_account_dict = {
                            "type": connection.get("type", "service_account"),
                            "project_id": connection.get("project_id"),
                            "private_key_id": connection.get("private_key_id"),
                            "private_key": private_key,  # Now has actual newlines
                            "client_email": connection.get("client_email"),
                            "client_id": connection.get("client_id"),
                            "auth_uri": connection.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                            "token_uri": connection.get("token_uri", "https://oauth2.googleapis.com/token"),
                            "auth_provider_x509_cert_url": connection.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                            "client_x509_cert_url": connection.get("client_x509_cert_url"),
                            "universe_domain": connection.get("universe_domain", "googleapis.com"),
                        }
                        # json.dumps will properly escape the newlines when serializing
                        connection["service_account_info"] = json.dumps(service_account_dict)
                        connection["name"] = "google_analytics"
                adapters.append(adapter_cls())
    return adapters