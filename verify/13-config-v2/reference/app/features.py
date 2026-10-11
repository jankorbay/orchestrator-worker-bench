"""Feature flags."""


def enabled(settings, name):
    return name in settings.features


def all_enabled(settings):
    return sorted(set(settings.features))
