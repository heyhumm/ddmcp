"""Configuration management for ddmcp."""

import os
from dataclasses import dataclass


# Mapping of short site codes to full Datadog API URLs
DD_SITE_URLS = {
    "us1": "https://api.datadoghq.com",
    "us3": "https://api.us3.datadoghq.com",
    "us5": "https://api.us5.datadoghq.com",
    "eu": "https://api.datadoghq.eu",
    "ap1": "https://api.ap1.datadoghq.com",
    "gov": "https://api.ddog-gov.com",
}


@dataclass
class DDMCPConfig:
    """Configuration for ddmcp loaded from environment variables."""

    api_key: str
    app_key: str
    site: str
    max_results: int = 50

    @classmethod
    def from_env(cls) -> "DDMCPConfig":
        """Load configuration from environment variables.

        Returns:
            DDMCPConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("DD_API_KEY")
        app_key = os.getenv("DD_APP_KEY")

        if not api_key:
            raise ValueError(
                "DD_API_KEY environment variable is required. "
                "Get your API key from https://app.datadoghq.com/organization-settings/api-keys"
            )

        if not app_key:
            raise ValueError(
                "DD_APP_KEY environment variable is required. "
                "Get your application key from https://app.datadoghq.com/organization-settings/application-keys"
            )

        # Get DD_SITE with default fallback to us1
        site_input = os.getenv("DD_SITE", "us1")

        # If it's a short code, map it to the full URL
        if site_input in DD_SITE_URLS:
            site = DD_SITE_URLS[site_input]
        elif site_input.startswith("http"):
            # Already a full URL
            site = site_input
        elif site_input.endswith(".datadoghq.com") or site_input.endswith(".datadoghq.eu") or site_input.endswith(".ddog-gov.com"):
            # Handle partial domain like "us5.datadoghq.com" -> "https://api.us5.datadoghq.com"
            site = f"https://api.{site_input}"
        else:
            # Unknown short code - fail with helpful message
            raise ValueError(
                f"Invalid DD_SITE value: {site_input}. "
                f"Use a short code ({', '.join(DD_SITE_URLS.keys())}) "
                f"or a full URL (https://api.datadoghq.com)"
            )

        # Get max results cap
        max_results_str = os.getenv("DDMCP_MAX_RESULTS", "50")
        try:
            max_results = int(max_results_str)
        except ValueError:
            raise ValueError(
                f"DDMCP_MAX_RESULTS must be an integer, got: {max_results_str}"
            )

        return cls(
            api_key=api_key,
            app_key=app_key,
            site=site,
            max_results=max_results,
        )
