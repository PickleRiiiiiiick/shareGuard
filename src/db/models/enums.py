import enum

class ScanScheduleType(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class AlertType(enum.Enum):
    PERMISSION_CHANGE = "permission_change"
    NEW_ACCESS = "new_access"
    INHERITANCE_CHANGE = "inheritance_change"
    GROUP_MEMBERSHIP_CHANGE = "group_membership_change"
    SENSITIVE_ACCESS = "sensitive_access"

class AlertSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
