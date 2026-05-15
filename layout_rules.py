from storage import load_config


BREAK_SHORT_FORMS = {
    "lunch": "LUNCH BR.",
    "fruit break": "FRUIT BR.",
    "fruit": "FRUIT BR.",
    "short break": "SHORT BR.",
    "break": "BREAK",
}


def get_break_periods():
    """
    Fetch break periods from config dynamically.

    Example output:
    {
        7: "LUNCH BR.",
        3: "FRUIT BR."
    }
    """

    config = load_config()

    raw_breaks = getattr(config, "break_periods", {})

    normalized = {}

    for period, label in raw_breaks.items():

        try:
            period_num = int(period)
        except (ValueError, TypeError):
            continue

        if not isinstance(label, str):
            continue

        clean = label.strip()

        short_name = normalize_break_name(clean)

        normalized[period_num] = short_name

    return normalized


def normalize_break_name(name: str) -> str:
    """
    Convert config names into PDF-friendly labels.

    Examples:
    Lunch -> LUNCH BR.
    Fruit Break -> FRUIT BR.
    """

    cleaned = name.strip().lower()

    if cleaned in BREAK_SHORT_FORMS:
        return BREAK_SHORT_FORMS[cleaned]

    # fallback generic formatter
    return cleaned.upper()


def is_break_period(period_number: int) -> bool:
    """
    Check whether a period is configured as break.
    """

    breaks = get_break_periods()

    return period_number in breaks


def get_break_label(period_number: int):
    """
    Returns formatted break label.

    Example:
    7 -> LUNCH BR.
    """

    breaks = get_break_periods()

    return breaks.get(period_number)


def get_break_name(config, period_number: int):
    """
    Return the normalized break name for a given period from a provided config.

    Accepts either string or int keys in config.break_periods.
    """

    raw_breaks = getattr(config, "break_periods", {})

    # try both str and int keys
    label = raw_breaks.get(period_number) if period_number in raw_breaks else raw_breaks.get(str(period_number))

    if not label or not isinstance(label, str):
        return None

    return normalize_break_name(label)