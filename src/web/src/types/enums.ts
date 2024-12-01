export enum ScanScheduleType {
    ONCE = "once",
    DAILY = "daily",
    WEEKLY = "weekly",
    MONTHLY = "monthly"
}

export enum AlertType {
    PERMISSION_CHANGE = "permission_change",
    NEW_ACCESS = "new_access",
    INHERITANCE_CHANGE = "inheritance_change",
    GROUP_MEMBERSHIP_CHANGE = "group_membership_change",
    SENSITIVE_ACCESS = "sensitive_access"
}

export enum AlertSeverity {
    LOW = "low",
    MEDIUM = "medium",
    HIGH = "high",
    CRITICAL = "critical"
}