"""Logging configuration."""
import logging


def level(settings):
    return getattr(logging, settings.log_level.upper())
