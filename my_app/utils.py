"""Shared formatting helpers used across views, models, and templates."""


def format_minutes(total_minutes):
    """Split a total-minutes integer into whole hours + leftover minutes.

    e.g. 624 -> {'hours': 10, 'minutes': 24}
    """
    total_minutes = max(int(total_minutes or 0), 0)
    return {
        'hours': total_minutes // 60,
        'minutes': total_minutes % 60,
    }


def format_duration(total_minutes):
    """Render a minutes total as an unambiguous 'Xh Ym' string.

    Use this (not '{{ hours }}.{{ minutes }} hrs') anywhere a duration is
    displayed - decimal-looking hour.minute strings (e.g. "10.40 hrs") are
    misread as true decimal hours (10h24m) when they're actually H:M
    digits mashed together (10h40m). 'Xh Ym' has no such ambiguity.

    e.g. 624 -> '10h 24m'
    """
    parts = format_minutes(total_minutes)
    return f"{parts['hours']}h {parts['minutes']}m"
