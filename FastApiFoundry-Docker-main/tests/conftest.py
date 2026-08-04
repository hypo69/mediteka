# -*- coding: utf-8 -*-
# =============================================================================
# conftest.py — Pytest configuration and shared fixtures
# =============================================================================

from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("ci")
