"""Configuration constants for web crawler behavior."""

# Maximum time in seconds to wait for a page response
# A lower value may miss slow pages but prevents crawler from hanging
TIMEOUT = 10

# Number of times to retry failed requests before giving up
# Helps handle temporary network issues or server errors
RETRIES = 3
