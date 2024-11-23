import requests
import json
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_test")

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
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            self.token = response.json().get('access_token')
            if not self.token:
                logger.error("Login failed: No access token received")
                return False
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            logger.info("Login successful")
            return True
        else:
            logger.error(f"Login failed: {response.text}")
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
        
        # Get account info from verify endpoint
        verify_url = f"{self.base_url}/api/v1/auth/verify"
        try:
            response = self.session.get(verify_url)
        except requests.RequestException as e:
            logger.error(f"Error connecting to verify endpoint: {e}")
            return False
        
        if response.status_code != 200:
            logger.error(f"Failed to verify permissions: {response.text}")
            return False
            
        try:
            account_info = response.json()
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from verify endpoint")
            return False
        
        current_permissions = set(account_info.get('account', {}).get('permissions', []))
        
        missing_permissions = required_permissions - current_permissions
        if missing_permissions:
            logger.error(f"Missing required permissions: {', '.join(missing_permissions)}")
            return False
            
        logger.info("All required permissions are present")
        return True

    def test_create_target(self):
        """Test target creation"""
        target_data = {
            "name": "Test-Target-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "path": "C:\\ShareGuardTest\\TestTarget",
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
        
        # Ensure test directory exists
        try:
            Path(target_data["path"]).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured test directory exists at {target_data['path']}")
        except Exception as e:
            logger.error(f"Failed to create test directory: {e}")
            return None
        
        response = self.session.post(
            f"{self.base_url}/api/v1/targets/",
            json=target_data
        )
        
        if response.status_code == 201:
            target = response.json()
            logger.info(f"Target created successfully: {target.get('name')}")
            return target.get('id')
        else:
            logger.error(f"Target creation failed: {response.text}")
            return None
            
    def test_list_targets(self, sort_by="name", sort_desc=False):
        """Test target listing with different sorting options"""
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
            try:
                targets = response.json()
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from target listing")
                return None
            logger.info(f"Retrieved {len(targets)} targets")
            for target in targets:
                logger.info(f"- {target.get('name')} ({target.get('path')})")
            return targets
        else:
            logger.error(f"Failed to list targets: {response.text}")
            return None
            
    def test_get_target(self, target_id):
        """Test retrieving a specific target"""
        response = self.session.get(
            f"{self.base_url}/api/v1/targets/{target_id}"
        )
        
        if response.status_code == 200:
            try:
                target = response.json()
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from get target")
                return None
            logger.info(f"Retrieved target: {target.get('name')}")
            return target
        else:
            logger.error(f"Failed to get target {target_id}: {response.text}")
            return None
            
    def test_update_target(self, target_id):
        """Test updating a target"""
        update_data = {
            "description": f"Updated description at {datetime.now()}",
            "scan_frequency": "weekly"
        }
        
        response = self.session.put(
            f"{self.base_url}/api/v1/targets/{target_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            try:
                updated_target = response.json()
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from update target")
                return False
            logger.info(f"Target updated successfully: {updated_target.get('name')}")
            return True
        else:
            logger.error(f"Failed to update target {target_id}: {response.text}")
            return False
            
    def test_target_operations(self, target_id):
        """Test enable/disable operations"""
        # Test disable
        disable_url = f"{self.base_url}/api/v1/targets/{target_id}/disable"
        response = self.session.post(disable_url)
        if response.status_code == 200:
            logger.info("Target disabled successfully")
        else:
            logger.error(f"Failed to disable target: {response.text}")
            
        # Test enable
        enable_url = f"{self.base_url}/api/v1/targets/{target_id}/enable"
        response = self.session.post(
            enable_url,
            params={"scan_frequency": "daily"}
        )
        if response.status_code == 200:
            logger.info("Target enabled successfully")
        else:
            logger.error(f"Failed to enable target: {response.text}")
            
    def cleanup_test_target(self, target_id):
        """Clean up test target"""
        response = self.session.delete(
            f"{self.base_url}/api/v1/targets/{target_id}"
        )
        
        if response.status_code == 204:
            logger.info(f"Test target {target_id} cleaned up successfully")
            return True
        else:
            logger.error(f"Failed to clean up target {target_id}: {response.text}")
            return False

def run_test_suite():
    """Run complete test suite"""
    tester = ShareGuardApiTester()
    
    # Step 1: Login
    if not tester.login():
        logger.error("Exiting test suite due to login failure.")
        return
        
    # Step 2: Verify permissions
    if not tester.verify_permissions():
        logger.error("Permission verification failed. Please update service account permissions.")
        return
        
    # Step 3: Create test target
    target_id = tester.test_create_target()
    if not target_id:
        logger.error("Exiting test suite due to target creation failure.")
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
    run_test_suite()
