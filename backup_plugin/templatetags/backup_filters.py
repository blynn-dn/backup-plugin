import logging

from django import template
from datetime import datetime
from django.utils import timezone

register = template.Library()
logger = logging.getLogger(f"netbox.backup_plugin.{__name__}")


@register.filter
def utc_string_to_datetime(value, format_string="%Y-%m-%dT%H:%M:%SZ"):
    try:
        logger.info(f"value: {value}, {type(value)}")
        return datetime.fromisoformat(value).strftime(format_string)
    except (ValueError, TypeError):
        return None  # Handle invalid input gracefully
