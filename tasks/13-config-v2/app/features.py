"""Feature flags."""


def enabled(settings, name):
    return name in [f.strip() for f in settings.features.split(",") if f.strip()]


def all_enabled(settings):
    return sorted({f.strip() for f in settings.features.split(",") if f.strip()})
