#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path

def debug_ace_structure():
    """Debug the ACE structure to understand the key generation issue"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    print("🔍 Debugging ACE Structure")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get the most recent permission change
        cursor.execute("""
            SELECT id, change_type, previous_state, current_state
            FROM permission_changes 
            ORDER BY detected_time DESC 
            LIMIT 1
        """)
        
        change = cursor.fetchone()
        if change:
            change_id, change_type, prev_state, curr_state = change
            print(f"📋 Recent Change (ID {change_id}):")
            print(f"   Type: {change_type}")
            
            try:
                if isinstance(prev_state, str):
                    prev_data = json.loads(prev_state)
                else:
                    prev_data = prev_state
                    
                if isinstance(curr_state, str):
                    curr_data = json.loads(curr_state)
                else:
                    curr_data = curr_state
                
                prev_aces = prev_data.get('aces', []) if prev_data else []
                curr_aces = curr_data.get('aces', []) if curr_data else []
                
                print(f"\n📊 ACE Analysis:")
                print(f"   Previous ACEs: {len(prev_aces)}")
                print(f"   Current ACEs: {len(curr_aces)}")
                
                # Show structure of a few ACEs
                print(f"\n🔍 Sample ACE Structure (Current):")
                for i, ace in enumerate(curr_aces[:3]):
                    print(f"   ACE {i+1}:")
                    print(f"     Full ACE: {json.dumps(ace, indent=2)}")
                    
                    # Show what the current key generation would produce
                    trustee = ace.get("trustee", {})
                    ace_key = f"{trustee.get('sid', '')}_{ace.get('type', '')}_{ace.get('is_inherited', False)}"
                    print(f"     Generated Key: '{ace_key}'")
                    print()
                
                # Try to manually identify what changed
                print(f"🔍 Manual Change Detection:")
                
                # Create simplified comparison
                def create_ace_signature(ace):
                    trustee = ace.get("trustee", {})
                    return {
                        'sid': trustee.get('sid', ''),
                        'name': trustee.get('full_name', ''),
                        'permissions': ace.get('permissions', {}),
                        'is_inherited': ace.get('is_inherited', False)
                    }
                
                prev_sigs = [create_ace_signature(ace) for ace in prev_aces]
                curr_sigs = [create_ace_signature(ace) for ace in curr_aces]
                
                # Find additions
                prev_names = {sig['name'] for sig in prev_sigs}
                curr_names = {sig['name'] for sig in curr_sigs}
                
                added_users = curr_names - prev_names
                removed_users = prev_names - curr_names
                
                print(f"   Added users: {list(added_users)}")
                print(f"   Removed users: {list(removed_users)}")
                
                if added_users:
                    print(f"\n✅ Found the issue: User(s) {list(added_users)} were added!")
                    print(f"   The change analysis should detect this but isn't working.")
                
            except Exception as e:
                print(f"   Error analyzing: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ No permission changes found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ace_structure()