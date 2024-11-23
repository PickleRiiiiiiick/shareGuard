from src.db.database import SessionLocal
from src.db.models.auth import ServiceAccount
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("permissions_update")

def update_service_account_permissions():
    db = SessionLocal()
    try:
        # Find the ShareGuardService account
        service_account = db.query(ServiceAccount).filter(
            ServiceAccount.username == "ShareGuardService",
            ServiceAccount.domain == "shareguard.com"
        ).first()

        if not service_account:
            logger.error("ShareGuardService account not found")
            return False

        # Update permissions to include all required permissions
        service_account.permissions = [
            "targets:read",
            "targets:create",
            "targets:update",
            "targets:delete",
            "scan:execute",
            "scan:read"
        ]

        db.commit()
        logger.info(f"Updated permissions for {service_account.username}")
        logger.info(f"New permissions: {service_account.permissions}")
        return True

    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Updating service account permissions...")
    success = update_service_account_permissions()
    if success:
        logger.info("Permissions updated successfully")
    else:
        logger.error("Failed to update permissions")