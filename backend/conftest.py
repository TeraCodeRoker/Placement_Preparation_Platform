"""Pytest bootstrap.

Rate limiting off for the suite (its many requests would trip limits) — set
before Django settings load so it's read into config.
"""
import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
