class AIConfigurationError(Exception):
    """Raised when the selected AI provider is not configured."""


class AIProviderError(Exception):
    """Raised when the selected AI provider cannot return a response."""
