"""OAuth provider configuration using Authlib.

Supports Google and GitHub OAuth 2.0 for social login.
To add more providers, register them here with their OAuth endpoints.
"""

import os

from authlib.integrations.starlette_client import OAuth

# Initialize OAuth registry
oauth = OAuth()

# Google OAuth Configuration
# Get credentials from: https://console.cloud.google.com/apis/credentials
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# GitHub OAuth Configuration
# Get credentials from: https://github.com/settings/developers
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=None,  # Will be set dynamically in the endpoint
    client_kwargs={"scope": "user:email"},
)

# Add more providers here:
# oauth.register(
#     name='microsoft',
#     client_id=os.getenv('MICROSOFT_CLIENT_ID'),
#     ...
# )


def get_oauth_provider(provider_name: str):
    """Get OAuth client for a provider.

    Args:
        provider_name: Name of the provider ('google', 'github', etc.)

    Returns:
        OAuth client instance or None if provider not found
    """
    try:
        return getattr(oauth, provider_name)
    except AttributeError:
        return None


# List of supported OAuth providers
SUPPORTED_PROVIDERS = ["google", "github"]


def is_provider_supported(provider_name: str) -> bool:
    """Check if an OAuth provider is supported."""
    return provider_name.lower() in SUPPORTED_PROVIDERS
