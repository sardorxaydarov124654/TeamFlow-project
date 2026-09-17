from django import template

register = template.Library()

# Palette pulled from the app's own teal/amber theme so generated avatars
# always feel native to the product rather than random web colors.
AVATAR_PALETTE = [
    "#1F4B43",  # primary teal
    "#2E6B5F",  # lighter teal
    "#E2A63B",  # amber accent
    "#4A78C4",  # blue (matches .status-review)
    "#8A5A00",  # deep amber (matches .pill)
    "#7A2E85",  # plum (matches platform_admin pill)
    "#2F7D4F",  # success green
    "#C1443C",  # danger red, used sparingly
]


@register.filter
def user_initials(user):
    """Return up to 2 uppercase initials for a user, falling back to the email."""
    if not user or not getattr(user, "is_authenticated", False):
        return "?"
    first = (getattr(user, "first_name", "") or "").strip()
    last = (getattr(user, "last_name", "") or "").strip()
    if first or last:
        initials = f"{first[:1]}{last[:1]}"
        if initials:
            return initials.upper()
    email = getattr(user, "email", "") or ""
    return (email[:2] or "?").upper()


@register.filter
def avatar_color(user):
    """Deterministic palette color keyed off the user's pk (or email as fallback)."""
    if not user:
        return AVATAR_PALETTE[0]
    key = getattr(user, "pk", None) or getattr(user, "email", "") or "x"
    index = hash(str(key)) % len(AVATAR_PALETTE)
    return AVATAR_PALETTE[index]
