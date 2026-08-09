"""Constants for the Bpost Tracker integration."""
from __future__ import annotations

import logging
from datetime import timedelta

DOMAIN = "bpost_tracker"
LOGGER = logging.getLogger(__package__)

CONF_TRACKING_NUMBER = "tracking_number"
CONF_POSTAL_CODE = "postal_code"
CONF_REMOVE_AFTER_DAYS = "remove_after_days"

UPDATE_INTERVAL_ACTIVE = timedelta(minutes=15)
UPDATE_INTERVAL_DELIVERED = timedelta(hours=6)

DEFAULT_REMOVE_AFTER_DAYS = 10

SUPPORTED_LANGUAGES = ("NL", "FR", "EN")
DEFAULT_LANGUAGE = "EN"
