"""Shared formatting utilities for ddmcp."""


def format_duration(nanoseconds: int) -> str:
    """Format a duration from nanoseconds to a human-readable string.

    Args:
        nanoseconds: Duration in nanoseconds

    Returns:
        Formatted duration string (e.g., "1.23s", "456ms", "78.9µs")

    Examples:
        >>> format_duration(1234567890)
        '1.23s'
        >>> format_duration(456789000)
        '457ms'
        >>> format_duration(78900)
        '78.9µs'
        >>> format_duration(123)
        '123ns'
    """
    if nanoseconds >= 1_000_000_000:
        # Seconds
        return f"{nanoseconds / 1_000_000_000:.2f}s"
    elif nanoseconds >= 1_000_000:
        # Milliseconds
        return f"{nanoseconds / 1_000_000:.0f}ms"
    elif nanoseconds >= 1_000:
        # Microseconds
        return f"{nanoseconds / 1_000:.1f}µs"
    else:
        # Nanoseconds
        return f"{nanoseconds}ns"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length with a suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append if truncated (default: "...")

    Returns:
        Truncated text with suffix if needed, original text if short enough

    Examples:
        >>> truncate_text("short", 10)
        'short'
        >>> truncate_text("a very long string that needs truncation", 20)
        'a very long strin...'
    """
    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]

    return text[:truncate_at] + suffix


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal value as a percentage.

    Args:
        value: Decimal value (0.0 to 1.0)
        decimals: Number of decimal places (default: 1)

    Returns:
        Formatted percentage string (e.g., "12.5%")

    Examples:
        >>> format_percentage(0.125)
        '12.5%'
        >>> format_percentage(0.9999, decimals=2)
        '99.99%'
    """
    return f"{value * 100:.{decimals}f}%"


def format_number(value: int | float) -> str:
    """Format a number with thousands separators.

    Args:
        value: Number to format

    Returns:
        Formatted number string with commas

    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.56)
        '1,234.56'
    """
    if isinstance(value, int):
        return f"{value:,}"
    else:
        return f"{value:,.2f}"
