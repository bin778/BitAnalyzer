from datetime import timedelta, timezone

COLOR_BG = (0.05, 0.05, 0.08, 1)
COLOR_GRID = (0.3, 0.3, 0.35, 0.5)
COLOR_TEXT = (0.85, 0.85, 0.85, 1)
COLOR_UP = (0.1, 0.85, 0.5, 1)
COLOR_DOWN = (1.0, 0.3, 0.35, 1)
COLOR_SPREAD_DEFAULT = (0.4, 0.5, 0.6, 0.5)

COLOR_ASK_LINE = (1.0, 0.3, 0.35, 0.8)
COLOR_BID_LINE = (0.1, 0.85, 0.5, 0.8)

DEFAULT_COLOR = (0.5, 0.5, 0.5, 1)

EXCHANGE_COLORS = {
    'Binance': (0.95, 0.75, 0.06, 1),
    'Upbit': (0.05, 0.36, 0.65, 1),
    'Bybit': (1, 0.6, 0.2, 1),
    'Bitfinex': (0.2, 0.8, 0.2, 1),
    'Kucoin': (0.6, 0.4, 0.8, 1)
}

KST = timezone(timedelta(hours=9))

TIME_SPAN_MAP = {
    '1H': 3600,
    '1D': 86400,
    '1M': 2592000,
    '3M': 7776000,
    '1Y': 31536000
}