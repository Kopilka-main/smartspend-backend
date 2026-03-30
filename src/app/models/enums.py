import enum


class UserStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    PENDING_DELETION = "pending_deletion"


class Theme(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"


class SetSource(str, enum.Enum):
    SMARTSPEND = "smartspend"
    COMMUNITY = "community"
    OWN = "own"


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class InvType(str, enum.Enum):
    CONSUMABLE = "consumable"
    WEAR = "wear"


class ReactionTarget(str, enum.Enum):
    ARTICLE = "article"
    SET = "set"
    COMMENT = "comment"


class ReactionType(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class BlockType(str, enum.Enum):
    P = "p"
    H2 = "h2"
    H3 = "h3"
    UL = "ul"
    HIGHLIGHT = "highlight"
    NOTE = "note"
    KEY_POINTS = "key_points"


class NotifType(str, enum.Enum):
    SYSTEM = "system"
    ACTIVITY = "activity"
    RECOMMENDATION = "recommendation"
