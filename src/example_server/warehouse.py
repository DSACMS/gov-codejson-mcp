"""Shared Databricks SQL connection setup."""

import os

from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal


def app_credentials_provider():
    """Provide OAuth credentials for the deployed App."""
    config = Config(
        host="https://" + os.environ["DATABRICKS_SERVER_HOSTNAME"],
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
    return oauth_service_principal(config)


def connect():
    """Open a SQL connection using the configured authentication mode."""
    auth_mode = os.environ.get("DATABRICKS_READER_AUTH_MODE", "local")

    if auth_mode == "local":
        auth_options = {"auth_type": "databricks-oauth"}
    elif auth_mode == "app":
        auth_options = {
            "credentials_provider": app_credentials_provider,
        }
    else:
        raise ValueError("DATABRICKS_READER_AUTH_MODE must be local or app")

    return sql.connect(
        server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        **auth_options,
    )
