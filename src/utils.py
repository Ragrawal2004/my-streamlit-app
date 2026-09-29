"""Formatting helpers shared by tools, agent and UI."""
import math


def fmt_inr(value: float) -> str:
    """Format a rupee amount in Indian digit grouping, e.g. 2000000 -> '₹20,00,000'."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    neg = value < 0
    n = str(int(round(abs(value))))
    if len(n) > 3:
        head, tail = n[:-3], n[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        n = ",".join(parts) + "," + tail
    return ("-₹" if neg else "₹") + n


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def fmt_months(months) -> str:
    if months is None:
        return "not reachable (no contribution)"
    years, rem = divmod(int(months), 12)
    if years == 0:
        return f"{int(months)} months"
    return f"{int(months)} months ({years} yr {rem} mo)" if rem else f"{int(months)} months ({years} yr)"
