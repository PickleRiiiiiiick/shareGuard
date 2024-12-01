import requests
import json
from datetime import datetime
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_test")

class TestDataManager:
    @staticmethod
    def get_test_target_data(name=None):
        """Generate test target data"""
        if name is None:
            name = "Test-Target-" + datetime.now().strftime("%Y%m%d%H%M%S")
            
        return {
            "name": name,
            "path": f"C:\\ShareGuardTest\\TestTarget\\{name}",
            "description": "Test target created by API test",
            "department": "IT",
            "owner": "Test Owner",
            "sensitivity_level": "medium",
            "scan_frequency": "daily",
            "target_metadata": {"purpose": "testing"},
            "is_sensitive": False,
            "max_depth": 3,
            "exclude_patterns": {"folders": ["temp"]}
        }

    @staticmethod
    def create_test_directory(path):
        """Create test directory if it doesn't exist"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured test directory exists at {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create test directory: {str(e)}")
            return False

class ShareGuardApiTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
        
    def login(self):
        """Authenticate and get token"""
        login_data = {
            "username": "ShareGuardService",
            "domain": "shareguard.com",
            "password": "P(5$\\#SX07sj"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                self.token = response.json()['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                logger.info("Login successful")
                return True
            else:
                logger.error(f"Login failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def verify_permissions(self):
        """Verify that the service account has all required permissions"""
        required_permissions = {
            "targets:read",
            "targets:create",
            "targets:update",
            "targets:delete",
            "scan:execute",
            "scan:read"
        }
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auth/verify")
            if response.status_code != 200:
                logger.error(f"Failed to verify permissions: {response.text}")
                return False
                
            account_info = response.json()
            current_permissions = set(account_info.get('account', {}).get('permissions', []))
            
            missing_permissions = required_permissions - current_permissions
            if missing_permissions:
                logger.error(f"Missing required permissions: {missing_permissions}")
                return False
                
            logger.info("All required permissions are present")
            return True
        except Exception as e:
            logger.error(f"Permission verification error: {str(e)}")
            return False
            
    def test_create_target(self):
        """Test target creation"""
        target_data = TestDataManager.get_test_target_data()
        
        # Ensure test directory exists
        if not TestDataManager.create_test_directory(target_data["path"]):
            return None
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/targets/",
                json=target_data
            )
            
            if response.status_code == 201:
                logger.info(f"Target created successfully: {response.json()['name']}")
                return response.json()['id']
            else:
                logger.error(f"Target creation failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Create target error: {str(e)}")
            return None
            
    def test_list_targets(self, sort_by="name", sort_desc=False):
        """Test target listing with different sorting options"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/targets/",
                params={
                    "sort_by": sort_by,
                    "sort_desc": sort_desc,
                    "limit": 10,
                    "skip": 0
                }
            )
            
            if response.status_code == 200:
                targets = response.json()
                logger.info(f"Retrieved {len(targets)} targets")
                for target in targets:
                    logger.info(f"- {target['name']} ({target['path']})")
                return targets
            else:
                logger.error(f"Failed to list targets: {response.text}")
                return None
        except Exception as e:
            logger.error(f"List targets error: {str(e)}")
            return None
            
    def test_get_target(self, target_id):
        """Test retrieving a specific target"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/targets/{target_id}"
            )
            
            if response.status_code == 200:
                target = response.json()
                logger.info(f"Retrieved target: {target['name']}")
                return target
            else:
                logger.error(f"Failed to get target {target_id}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Get target error: {str(e)}")
            return None
            
    def test_update_target(self, target_id):
        """Test updating a target"""
        # First get the current target data
        current_target = self.test_get_target(target_id)
        if not current_target:
            return False

        try:
            # Update with existing data plus changes
            update_data = {
                "name": current_target["name"],
                "path": current_target["path"],
                "description": f"Updated description at {datetime.now()}",
                "department": current_target.get("department"),
                "owner": current_target.get("owner"),
                "sensitivity_level": current_target.get("sensitivity_level"),
                "scan_frequency": "weekly",
                "target_metadata": current_target.get("target_metadata"),
                "is_sensitive": current_target.get("is_sensitive", False),
                "max_depth": current_target.get("max_depth", 5),
                "exclude_patterns": current_target.get("exclude_patterns")
            }
            
            response = self.session.put(
                f"{self.base_url}/api/v1/targets/{target_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"Target updated successfully: {response.json()['name']}")
                # Verify the update
                updated_target = self.test_get_target(target_id)
                if updated_target and updated_target["scan_frequency"] == "weekly":
                    logger.info("Update verified successfully")
                    return True
                else:
                    logger.error("Update verification failed")
                    return False
            else:
                logger.error(f"Failed to update target {target_id}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Update target error: {str(e)}")
            return False
            
    def test_target_operations(self, target_id):
        """Test enable/disable operations"""
        try:
            # Test disable
            response = self.session.post(
                f"{self.base_url}/api/v1/targets/{target_id}/disable"
            )
            if response.status_code == 200:
                logger.info("Target disabled successfully")
            else:
                logger.error(f"Failed to disable target: {response.text}")
                
            # Test enable
            response = self.session.post(
                f"{self.base_url}/api/v1/targets/{target_id}/enable",
                params={"scan_frequency": "daily"}
            )
            if response.status_code == 200:
                logger.info("Target enabled successfully")
            else:
                logger.error(f"Failed to enable target: {response.text}")
        except Exception as e:
            logger.error(f"Target operations error: {str(e)}")
            
    def cleanup_test_target(self, target_id):
        """Clean up test target"""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/targets/{target_id}"
            )
            
            if response.status_code == 204:
                logger.info(f"Test target {target_id} cleaned up successfully")
                return True
            else:
                logger.error(f"Failed to clean up target {target_id}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return False

def run_test_suite():
    """Run complete test suite"""
    tester = ShareGuardApiTester()
    
    # Step 1: Login
    if not tester.login():
        return
        
    # Step 2: Verify permissions
    if not tester.verify_permissions():
        logger.error("Permission verification failed. Please update service account permissions.")
        return
        
    # Step 3: Create test target
    target_id = tester.test_create_target()
    if not target_id:
        return
        
    try:
        # Step 4: List targets
        logger.info("\nTesting target listing...")
        tester.test_list_targets(sort_by="name", sort_desc=False)
        
        # Step 5: Get specific target
        logger.info("\nTesting target retrieval...")
        tester.test_get_target(target_id)
        
        # Step 6: Update target
        logger.info("\nTesting target update...")
        tester.test_update_target(target_id)
        
        # Step 7: Test operations
        logger.info("\nTesting target operations...")
        tester.test_target_operations(target_id)
        
    finally:
        # Cleanup
        logger.info("\nCleaning up test data...")
        tester.cleanup_test_target(target_id)

if __name__ == "__main__":
    logger.info("Starting API test suite...")
    try:
        run_test_suite()
    except KeyboardInterrupt:
        logger.info("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in test suite: {str(e)}")
        sys.exit(1)