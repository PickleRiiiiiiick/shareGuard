# test_user_access.py
from src.core.scanner import ShareGuardScanner
from typing import Dict, List

def normalize_name(name: str) -> str:
    """Normalize a name by stripping the domain prefix and converting to lowercase."""
    return name.split('\\')[-1].lower() if '\\' in name else name.lower()

def print_access_details(
    folder_path: str,
    permissions: Dict,
    aces: List[Dict],
    user_groups: List[Dict]
):
    """Print detailed access information including access paths."""
    print(f"\n📂 {folder_path}")
    print("  Access obtained through:")

    # Create a set of normalized user group names for comparison
    group_names = set(normalize_name(group['full_name']) for group in user_groups)
    access_found = False

    # Process each ACE
    for ace in aces:
        trustee = ace.get('trustee', {})
        trustee_name = trustee.get('full_name', 'Unknown')
        normalized_trustee_name = normalize_name(trustee_name)

        # Debugging output (optional)
        # print(f"Comparing trustee '{normalized_trustee_name}' with user groups {group_names}")

        # Check if this ACE corresponds to any of the user's groups
        if normalized_trustee_name in group_names:
            access_found = True
            perms = ace.get('permissions', {})

            # Determine access level
            if any('Full Control' in perms.get(cat, []) for cat in perms):
                access_level = "Full Control"
            elif 'Change Permissions' in perms.get('Advanced', []):
                access_level = "Administrative Access"
            elif 'Create Files' in perms.get('Directory', []):
                access_level = "Modify Access"
            elif 'Read Permissions' in perms.get('Advanced', []):
                access_level = "Read Access"
            else:
                access_level = "Custom Access"

            inheritance = "Inherited" if ace.get('inherited', False) else "Direct"

            # Print formatted access information
            print(f"  • Through group: {trustee_name}")
            print(f"    ├─ Access Level: {access_level}")
            print(f"    └─ Type: {inheritance}")

            # If there are nested groups, show them
            group_paths = ace.get('access_paths', {}).get('group_paths', [])
            if group_paths:
                print("    └─ Nested Groups:")
                for path in group_paths:
                    chain = []
                    if 'group' in path:
                        chain.append(path['group']['full_name'])
                        for member in path.get('member_groups', []):
                            chain.append(member['group']['full_name'])
                        if chain:
                            print(f"       └─ {' → '.join(chain)}")
        else:
            continue  # ACE does not match any user groups

    if not access_found:
        # Try to determine which groups should provide access
        suggested_groups = []
        for group in user_groups:
            group_name = normalize_name(group['full_name'])
            if any(word in folder_path.lower() for word in group_name.split('_')):
                suggested_groups.append(group['full_name'])

        if suggested_groups:
            print("  • Expected access through:")
            for group in suggested_groups:
                print(f"    └─ {group}")
        else:
            print("  • No matching group access found")

    # Show effective permissions
    print("\n  Effective Permissions:")
    for category in ['Basic', 'Advanced', 'Directory']:
        perms_in_category = permissions.get(category, [])
        if perms_in_category:
            print(f"  {category}:")
            for perm in sorted(perms_in_category):
                print(f"    • {perm}")

    # Add a summary of effective access
    print("\n  Access Summary:")
    all_perms = []
    for perms_list in permissions.values():
        all_perms.extend(perms_list)
    if 'Full Control' in all_perms:
        print("    ► Full Control Access")
    elif 'Change Permissions' in all_perms:
        print("    ► Administrative Access")
    elif 'Create Files' in all_perms or 'Write Data' in all_perms:
        print("    ► Modify Access")
    elif 'List Folder' in all_perms or 'Read Data' in all_perms:
        print("    ► Read Access")
    else:
        print("    ► Limited/Custom Access")

    # Add note about inheritance if relevant
    inherited = any(ace.get('inherited', False) for ace in aces)
    if inherited:
        print("    ► Some permissions are inherited from parent")

    print("  " + "─" * 30)

def organize_folders_by_department(
    folders: List[Dict],
    base_path: str
) -> Dict[str, List[Dict]]:
    """Organize folders by department."""
    departments = {
        "IT": [],
        "Finance": [],
        "HR": [],
        "Common": [],
        "Other": []
    }

    for folder in folders:
        path = folder.get('path', '')
        if not path:
            continue

        # Get relative path
        rel_path = path.replace(base_path + "\\", "").replace(base_path, "")
        if not rel_path:
            rel_path = "(Root)"

        # Determine department
        dept = "Other"
        for d in ["IT", "Finance", "HR", "Common"]:
            if (
                f"\\{d}\\" in path
                or path.endswith(f"\\{d}")
                or normalize_name(rel_path) == normalize_name(d)
            ):
                dept = d
                break

        departments[dept].append({
            'path': rel_path,
            'full_path': path,
            'permissions': folder.get('effective_permissions', {}),
            'aces': folder.get('aces', [])
        })

    return {k: v for k, v in departments.items() if v}

def print_user_access_results(result: Dict):
    """Print user access results with detailed access path information."""
    if not result.get('success', False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return

    # Print user info
    user_info = result.get('user_info', {})
    print(f"\nUser: {user_info.get('full_name', 'Unknown')}")

    # Print group memberships
    user_groups = result.get('group_memberships', [])
    print("\nGroup Memberships:")
    for group in sorted(user_groups, key=lambda x: x.get('full_name', '')):
        print(f"• {group.get('full_name', 'Unknown')}")

    # Organize and print accessible folders
    base_path = "C:\\ShareGuardTest"
    departments = organize_folders_by_department(
        result.get('accessible_folders', []),
        base_path
    )

    print("\nAccessible Resources by Department:")
    for dept, folders in departments.items():
        print(f"\n{dept} Department Access:")
        print("=" * 50)

        for folder in sorted(folders, key=lambda x: x['path']):
            print_access_details(
                folder['path'],
                folder['permissions'],
                folder.get('aces', []),
                user_groups
            )

    # Print statistics
    stats = result.get('statistics', {})
    if stats:
        print("\nAccess Statistics:")
        print(f"Total Folders in System: {stats.get('folders_checked', 0)}")
        print(f"Accessible Folders: {stats.get('accessible_folders', 0)}")

        # Calculate direct vs inherited access
        direct_access = 0
        inherited_access = 0
        for folder in result.get('accessible_folders', []):
            for ace in folder.get('aces', []):
                if ace.get('inherited', False):
                    inherited_access += 1
                else:
                    direct_access += 1

        if direct_access or inherited_access:
            print(f"Direct Access Entries: {direct_access}")
            print(f"Inherited Access Entries: {inherited_access}")

        if stats.get('error_count', 0) > 0:
            print(f"Errors Encountered: {stats.get('error_count', 0)}")

def test_user_access():
    scanner = ShareGuardScanner()

    # Test with multiple users
    test_cases = [
        {
            "user": ("john.smith", "SHAREGUARD"),
            "description": "IT Staff + Folder Admin",
            "expected_access": [
                "IT Department (Full Access through IT_Staff)",
                "HR Department (Admin Access through Folder_Admins)",
                "Common (Read Access through Domain Users)"
            ]
        },
        {
            "user": ("jane.doe", "SHAREGUARD"),
            "description": "Finance Staff + Report Viewer",
            "expected_access": [
                "Finance Department (Modify Access through Finance_Staff)",
                "Finance Reports (Read Access through Report_Viewers)",
                "Common (Read Access through Domain Users)"
            ]
        },
        {
            "user": ("bob.wilson", "SHAREGUARD"),
            "description": "HR Staff",
            "expected_access": [
                "HR Department (Modify Access through HR_Staff)",
                "Common (Read Access through Domain Users)"
            ]
        }
    ]

    for case in test_cases:
        username, domain = case["user"]
        print("\n" + "=" * 60)
        print(f"Testing User: {domain}\\{username}")
        print(f"Role: {case['description']}")
        print("\nExpected Access Patterns:")
        for access in case['expected_access']:
            print(f"• {access}")

        result = scanner.get_user_access(username, domain, r"C:\ShareGuardTest")
        print_user_access_results(result)

if __name__ == "__main__":
    print("\nShareGuard User Access Analysis")
    print("=" * 60)
    test_user_access()
    print("\nAnalysis completed!")
