# Adapted from https://dflund.se/~triad/krad/recode/petscii.html
# Authors: Linus Walleij <triad@df.lth.se>
# General notes: Licensed under the GNU GPL, version 2

upper_chars = (
    """             \r\x0e     \x7f            !"#$%&'()*+,-./0123456789"""
    """:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\xa3]\u2191\u2190\u2500\u2660  """
    """     \u256e\u2570\u256f \u2572\u2571  \u25cf \u2665 \u256d\u2573"""
    """\u25cb\u2663 \u2666\u253c \u2502\u03c0\u25e5             \n\x0f """
    """   \x0c            \xa0\u258c\u2584\u2594\u2581\u258f\u2592\u2595"""
    """ \u25e4 \u251c\u2597\u2514\u2510\u2582\u250c\u2534\u252c\u2524"""
    """\u258e\u258d   \u2583 \u2596\u259d\u2518\u2598\u259a\u2500\u2660"""
    """       \u256e\u2570\u256f \u2572\u2571  \u25cf \u2665 \u256d\u2573"""
    """\u25cb\u2663 \u2666\u253c \u2502\u03c0\u25e5\xa0\u258c\u2584\u2594"""
    """\u2581\u258f\u2592\u2595 \u25e4 \u251c\u2597\u2514\u2510\u2582"""
    """\u250c\u2534\u252c\u2524\u258e\u258d   \u2583 \u2596\u259d\u2518"""
    """\u2598\u03c0"""
)

lower_chars = (
    """             \r\x0e     \x7f            !"#$%&'()*+,-./0123456789"""
    """:;<=>?@abcdefghijklmnopqrstuvwxyz[\xa3]\u2191\u2190\u2500ABCDEFGH"""
    """IJKLMNOPQRSTUVWXYZ\u253c \u2502\u2592              \n\x0f    \x0c"""
    """            \xa0\u258c\u2584\u2594\u2581\u258f\u2592\u2595   \u251c"""
    """\u2597\u2514\u2510\u2582\u250c\u2534\u252c\u2524\u258e\u258d   """
    """\u2583\u2713\u2596\u259d\u2518\u2598\u259a\u2500ABCDEFGHIJKLMNOPQ"""
    """RSTUVWXYZ\u253c \u2502\u2592 \xa0\u258c\u2584\u2594\u2581\u258f"""
    """\u2592\u2595   \u251c\u2597\u2514\u2510\u2582\u250c\u2534\u252c"""
    """\u2524\u258e\u258d   \u2583\u2713\u2596\u259d\u2518\u2598\u2592"""
)


def from_screencode(c):
    if c < 0x20:
        return c + 0x40
    elif c < 0x40:
        return c
    elif c < 0x60:
        return c + 0x80
    elif c < 0x80:
        return c + 0x40
    elif c < 0xA0:
        return c - 0x80
    elif c < 0xE0:
        return c - 0x40
    else:
        return c


def to_unicode(bytes, lower=True, screencode=False):
    unicode = ""
    for b in bytes:
        if screencode:
            b = from_screencode(b)
        if lower:
            unicode += lower_chars[b]
        else:
            unicode += upper_chars[b]
    return unicode