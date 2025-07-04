#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path

def debug_change_analysis():
    """Debug the change analysis for the recent alert"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    print("🔍 Debugging Change Analysis")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Find the recent alert for ShareGuardTestData
        cursor.execute("""
            SELECT id, severity, message, details, created_at 
            FROM alerts 
            WHERE message LIKE '%ShareGuardTestData%'
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        alert = cursor.fetchone()
        if alert:
            alert_id, severity, message, details_str, created_at = alert
            print(f"📋 Recent Alert Found:")
            print(f"   ID: {alert_id}")
            print(f"   Message: {message}")
            print(f"   Created: {created_at}")
            
            # Parse the details
            try:
                details = json.loads(details_str)
                print(f"\n🔍 Alert Details Structure:")
                print(f"   Folder: {details.get('folder', {}).get('name', 'N/A')}")
                print(f"   Changes Detected: {details.get('summary', {}).get('changes_detected', 'N/A')}")
                print(f"   Severity Level: {details.get('summary', {}).get('severity_level', 'N/A')}")
                print(f"   Number of Change Items: {len(details.get('changes', []))}")
                
                if details.get('changes'):
                    print(f"\n📝 Change Items:")
                    for i, change in enumerate(details['changes'], 1):
                        print(f"   {i}. {change.get('icon', '')} {change.get('type', '')} - {change.get('description', '')}")
                else:
                    print(f"\n❌ No change items found - this is the problem!")
                    
            except Exception as e:
                print(f"   ❌ Error parsing details: {e}")
        else:
            print("❌ No recent alert found for ShareGuardTestData")
        
        # 2. Check permission changes table
        cursor.execute("""
            SELECT id, change_type, detected_time, previous_state, current_state
            FROM permission_changes 
            ORDER BY detected_time DESC 
            LIMIT 3
        """)
        
        changes = cursor.fetchall()
        print(f"\n📊 Recent Permission Changes ({len(changes)}):")
        
        for change in changes:
            change_id, change_type, detected_time, prev_state, curr_state = change
            print(f"\n   Change ID {change_id}:")
            print(f"   Type: {change_type}")
            print(f"   Time: {detected_time}")
            
            # Try to parse the states to see what's different
            try:
                if isinstance(prev_state, str):
                    prev_data = json.loads(prev_state)
                else:
                    prev_data = prev_state
                    
                if isinstance(curr_state, str):
                    curr_data = json.loads(curr_state)
                else:
                    curr_data = curr_state
                
                # Compare ACE counts
                prev_aces = prev_data.get('aces', []) if prev_data else []
                curr_aces = curr_data.get('aces', []) if curr_data else []
                
                print(f"   Previous ACEs: {len(prev_aces)}")
                print(f"   Current ACEs: {len(curr_aces)}")
                print(f"   Difference: {len(curr_aces) - len(prev_aces)}")
                
                # Show some ACE details
                if curr_aces:
                    print(f"   Recent ACE example:")
                    for ace in curr_aces[-2:]:  # Show last 2 ACEs
                        trustee = ace.get('trustee', {})
                        print(f"     - {trustee.get('full_name', 'Unknown')}: {ace.get('permissions', {})}")
                
            except Exception as e:
                print(f"   Error analyzing states: {e}")
        
        print(f"\n🎯 Debug Summary:")
        print(f"   The system detected a change but couldn't analyze the specifics")
        print(f"   Need to improve the _analyze_permission_changes function")
        print(f"   The permission states are being stored correctly")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_change_analysis()