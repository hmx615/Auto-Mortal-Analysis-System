#!/usr/bin/env python3
"""Compatibility entry point for the browser-based crawler."""

# Direct calls to Amae-Koromo's player_records API are intentionally disabled.
# The endpoint now requires a CAP token and rejects unattended API crawling.
# Keep the historical command name, but run only the normal browser UI flow.

from crawl_frontend import main


if __name__ == "__main__":
    main()
