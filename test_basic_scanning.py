# test_basic_scanning.py
from src.core.scanner import ShareGuardScanner
from datetime import datetime

def test_basic_scan():
    scanner = ShareGuardScanner()
    
    # Test paths
    test_paths = [
        r"C:\ShareGuardTest\IT",         # IT Staff should have access
        r"C:\ShareGuardTest\Finance",    # Finance Staff access
        r"C:\ShareGuardTest\HR",         # HR Staff access
        r"C:\ShareGuardTest\Common"      # Everyone should have read access
    ]
    
    for path in test_paths:
        print(f"\nScanning: {path}")
        print("=" * 50)
        result = scanner.scan_path(path)
        print_scan_results(result)

def print_scan_results(result):
    """Print scan results with better error handling."""
    if not result.get('success', False):
        print(f"Error scanning folder: {result.get('error', 'Unknown error')}")
        return

    # Print folder info
    folder_info = result.get('folder_info', {})
    print(f"Folder: {folder_info.get('name', 'Unknown')}")
    print(f"Path: {folder_info.get('path', 'Unknown')}")
    
    # Print permissions
    permissions = result.get('permissions', {})
    if not permissions.get('success', False):
        print(f"Error getting permissions: {permissions.get('error', 'Unknown error')}")
        return

    # Print owner
    owner = permissions.get('owner', {})
    if owner:
        print(f"\nOwner: {owner.get('full_name', 'Unknown')}")

    # Print ACEs
    print("\nPermissions:")
    for ace in permissions.get('aces', []):
        print(f"\n{'-' * 40}")
        trustee = ace.get('trustee', {})
        print(f"Account: {trustee.get('full_name', 'Unknown')}")
        print(f"Type: {ace.get('type', 'Unknown')}")
        print(f"Inherited: {ace.get('inherited', False)}")
        
        # Print permissions by category
        for category, perms in ace.get('permissions', {}).items():
            if perms:
                print(f"\n{category}:")
                for perm in sorted(perms):
                    print(f"  • {perm}")
        
        # Print group access paths if available
        access_paths = ace.get('access_paths', {})
        if access_paths and access_paths.get('group_paths'):
            print("\nAccess through groups:")
            for path in access_paths['group_paths']:
                group = path.get('group', {})
                print(f"  • {group.get('full_name', 'Unknown')}")
                for member_group in path.get('member_groups', []):
                    sub_group = member_group.get('group', {})
                    print(f"    └─ {sub_group.get('full_name', 'Unknown')}")

    # Print statistics
    stats = result.get('statistics', {})
    if stats:
        print(f"\nStatistics:")
        print(f"Total folders: {stats.get('total_folders', 0)}")
        print(f"Processed folders: {stats.get('processed_folders', 0)}")
        print(f"Errors: {stats.get('error_count', 0)}")

def format_datetime(dt_str):
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

if __name__ == "__main__":
    print("\nShareGuard Permission Scanner Test")
    print("=" * 50)
    test_basic_scan()
    print("\nScan completed!")