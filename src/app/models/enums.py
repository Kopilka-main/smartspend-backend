import enum


class UserStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    PENDING_DELETION = "pending_deletion"


class Theme(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"
