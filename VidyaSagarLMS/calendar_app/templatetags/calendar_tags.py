from django import template
from datetime import date, timedelta

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split string by delimiter"""
    return value.split(delimiter)

@register.filter
def filter_upcoming(events, days=7):
    """Filter events for next X days"""
    today = date.today()
    end_date = today + timedelta(days=days)
    return [event for event in events if today <= event.start_date <= end_date]

@register.filter
def month_name(month_number):
    """Convert month number to month name"""
    from datetime import date
    try:
        return date(1900, int(month_number), 1).strftime('%B')
    except (ValueError, TypeError):
        return month_number

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key)