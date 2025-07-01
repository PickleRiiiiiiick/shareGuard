# src/services/notification_service.py

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models.alerts import Alert, AlertConfiguration
from src.db.models.changes import PermissionChange
from src.utils.logger import setup_logger

logger = setup_logger('notification_service')

class NotificationType(Enum):
    PERMISSION_CHANGE = "permission_change"
    GROUP_MEMBERSHIP_CHANGE = "group_membership_change"
    NEW_ACCESS_GRANTED = "new_access_granted"
    ACCESS_REMOVED = "access_removed"
    ALERT_TRIGGERED = "alert_triggered"
    SYSTEM_STATUS = "system_status"

@dataclass
class Notification:
    """Structured notification message."""
    id: str
    type: NotificationType
    title: str
    message: str
    severity: str
    timestamp: str
    data: Dict[str, Any]
    read: bool = False

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.connection_filters: Dict[str, Dict] = {}  # connection_id -> filters
        
    async def connect(self, websocket: WebSocket, connection_id: str, 
                     user_id: str = None, filters: Dict = None) -> None:
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            if filters:
                self.connection_filters[connection_id] = filters
            
            logger.info(f"WebSocket connection established: {connection_id} (user: {user_id})")
            
            # Send connection confirmation
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error establishing connection {connection_id}: {str(e)}")
            raise

    async def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        try:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            if connection_id in self.connection_filters:
                del self.connection_filters[connection_id]
            
            # Remove from user connections
            for user_id, conn_ids in self.user_connections.items():
                if connection_id in conn_ids:
                    conn_ids.remove(connection_id)
                    if not conn_ids:  # Remove empty sets
                        del self.user_connections[user_id]
                    break
            
            logger.info(f"WebSocket connection closed: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting {connection_id}: {str(e)}")

    async def send_to_connection(self, connection_id: str, message: Dict) -> bool:
        """Send message to a specific connection."""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
                return True
            return False
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {str(e)}")
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: str, message: Dict) -> int:
        """Send message to all connections for a specific user."""
        sent_count = 0
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count

    async def broadcast(self, message: Dict, filters: Dict = None) -> int:
        """Broadcast message to all or filtered connections."""
        sent_count = 0
        for connection_id in list(self.active_connections.keys()):
            # Apply filters if specified
            if filters and not self._message_matches_filters(message, connection_id, filters):
                continue
                
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        return sent_count

    def _message_matches_filters(self, message: Dict, connection_id: str, 
                               message_filters: Dict) -> bool:
        """Check if message matches connection filters."""
        try:
            connection_filters = self.connection_filters.get(connection_id, {})
            
            # Check notification type filter
            if 'types' in connection_filters:
                msg_type = message.get('type')
                if msg_type not in connection_filters['types']:
                    return False
            
            # Check severity filter
            if 'min_severity' in connection_filters:
                msg_severity = message.get('severity', 'low')
                severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                min_level = severity_levels.get(connection_filters['min_severity'], 1)
                msg_level = severity_levels.get(msg_severity, 1)
                if msg_level < min_level:
                    return False
            
            # Check path filter
            if 'paths' in connection_filters:
                msg_data = message.get('data', {})
                msg_path = msg_data.get('path', '')
                if not any(path in msg_path for path in connection_filters['paths']):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error applying filters: {str(e)}")
            return True  # Default to allowing message

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)

    def get_user_count(self) -> int:
        """Get number of unique users connected."""
        return len(self.user_connections)

class NotificationService:
    """Service for managing real-time notifications and alerts."""
    
    def __init__(self, db_session_factory=get_db):
        self.db_session_factory = db_session_factory
        self.connection_manager = ConnectionManager()
        self.notification_handlers: Dict[NotificationType, List[Callable]] = {}
        
        # Notification queue for persistence
        self._notification_queue = asyncio.Queue()
        self._queue_processor_task = None
        
        # Statistics
        self.stats = {
            'notifications_sent': 0,
            'notifications_queued': 0,
            'connections_established': 0,
            'connections_closed': 0
        }
        
        logger.info("Notification service initialized")

    async def start_service(self) -> None:
        """Start the notification service."""
        try:
            # Start notification queue processor
            self._queue_processor_task = asyncio.create_task(
                self._process_notification_queue()
            )
            
            logger.info("Notification service started")
            
        except Exception as e:
            logger.error(f"Failed to start notification service: {str(e)}")
            raise

    async def stop_service(self) -> None:
        """Stop the notification service."""
        try:
            if self._queue_processor_task:
                self._queue_processor_task.cancel()
                try:
                    await self._queue_processor_task
                except asyncio.CancelledError:
                    pass
            
            # Close all connections
            for connection_id in list(self.connection_manager.active_connections.keys()):
                await self.connection_manager.disconnect(connection_id)
            
            logger.info("Notification service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping notification service: {str(e)}")

    async def handle_websocket_connection(self, websocket: WebSocket, 
                                        user_id: str = None, 
                                        filters: Dict = None) -> str:
        """Handle a new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        
        try:
            await self.connection_manager.connect(websocket, connection_id, user_id, filters)
            self.stats['connections_established'] += 1
            
            # Keep connection alive and handle messages
            try:
                while True:
                    # Wait for messages from client (like ping/pong or filter updates)
                    message = await websocket.receive_text()
                    await self._handle_client_message(connection_id, json.loads(message))
                    
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {connection_id}")
            except Exception as e:
                logger.error(f"WebSocket error for {connection_id}: {str(e)}")
            finally:
                await self.connection_manager.disconnect(connection_id)
                self.stats['connections_closed'] += 1
                
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {str(e)}")
            await self.connection_manager.disconnect(connection_id)
            
        return connection_id

    async def _handle_client_message(self, connection_id: str, message: Dict) -> None:
        """Handle messages received from WebSocket clients."""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'ping':
                await self.connection_manager.send_to_connection(connection_id, {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            elif msg_type == 'update_filters':
                filters = message.get('filters', {})
                self.connection_manager.connection_filters[connection_id] = filters
                await self.connection_manager.send_to_connection(connection_id, {
                    'type': 'filters_updated',
                    'filters': filters,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            elif msg_type == 'acknowledge_notification':
                notification_id = message.get('notification_id')
                await self._acknowledge_notification(notification_id, connection_id)
            
        except Exception as e:
            logger.error(f"Error handling client message: {str(e)}")

    async def send_notification(self, notification: Notification, 
                              target_user: str = None,
                              broadcast: bool = False) -> None:
        """Send a notification to specific user or broadcast."""
        try:
            # Add to queue for persistence
            await self._notification_queue.put({
                'notification': notification,
                'target_user': target_user,
                'broadcast': broadcast,
                'timestamp': datetime.utcnow()
            })
            
            self.stats['notifications_queued'] += 1
            
        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")

    async def send_permission_change_notification(self, change: PermissionChange) -> None:
        """Send notification for permission changes."""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                type=NotificationType.PERMISSION_CHANGE,
                title="Permission Change Detected",
                message=self._format_permission_change_message(change),
                severity=self._determine_change_severity(change),
                timestamp=datetime.utcnow().isoformat(),
                data={
                    'change_id': change.id,
                    'change_type': change.change_type,
                    'scan_job_id': change.scan_job_id,
                    'previous_state': change.previous_state,
                    'current_state': change.current_state,
                    'detected_time': change.detected_time.isoformat()
                }
            )
            
            await self.send_notification(notification, broadcast=True)
            
        except Exception as e:
            logger.error(f"Error sending permission change notification: {str(e)}")

    async def send_group_change_notification(self, change: PermissionChange) -> None:
        """Send notification for group membership changes."""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                type=NotificationType.GROUP_MEMBERSHIP_CHANGE,
                title="Group Membership Change",
                message=self._format_group_change_message(change),
                severity=self._determine_change_severity(change),
                timestamp=datetime.utcnow().isoformat(),
                data={
                    'change_id': change.id,
                    'change_type': change.change_type,
                    'group_info': change.current_state or change.previous_state,
                    'detected_time': change.detected_time.isoformat()
                }
            )
            
            await self.send_notification(notification, broadcast=True)
            
        except Exception as e:
            logger.error(f"Error sending group change notification: {str(e)}")

    async def send_alert_notification(self, alert: Alert) -> None:
        """Send notification for triggered alerts."""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                type=NotificationType.ALERT_TRIGGERED,
                title=f"Alert: {alert.severity.upper()}",
                message=alert.message,
                severity=alert.severity,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    'alert_id': alert.id,
                    'config_id': alert.config_id,
                    'severity': alert.severity,
                    'details': alert.details,
                    'scan_job_id': alert.scan_job_id,
                    'permission_change_id': alert.permission_change_id
                }
            )
            
            await self.send_notification(notification, broadcast=True)
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")

    def _format_permission_change_message(self, change: PermissionChange) -> str:
        """Format a human-readable message for permission changes."""
        try:
            change_type = change.change_type
            current_state = change.current_state or {}
            previous_state = change.previous_state or {}
            
            if change_type == "permission_added":
                trustee = current_state.get('trustee', 'Unknown user')
                path = current_state.get('path', 'Unknown location')
                return f"New access granted to {trustee} on {path}"
            
            elif change_type == "permission_removed":
                trustee = previous_state.get('trustee', 'Unknown user')
                path = previous_state.get('path', 'Unknown location')
                return f"Access removed for {trustee} on {path}"
            
            elif change_type == "permission_modified":
                trustee = current_state.get('trustee', 'Unknown user')
                path = current_state.get('path', 'Unknown location')
                return f"Access permissions changed for {trustee} on {path}"
            
            else:
                return f"Permission change detected: {change_type}"
                
        except Exception as e:
            logger.warning(f"Error formatting permission change message: {str(e)}")
            return f"Permission change: {change.change_type}"

    def _format_group_change_message(self, change: PermissionChange) -> str:
        """Format a human-readable message for group membership changes."""
        try:
            change_type = change.change_type
            current_state = change.current_state or {}
            previous_state = change.previous_state or {}
            
            if change_type == "group_member_added":
                group = current_state.get('group', 'Unknown group')
                member_info = current_state.get('member_info', {})
                member_name = member_info.get('full_name', 'Unknown user')
                return f"User {member_name} added to group {group}"
            
            elif change_type == "group_member_removed":
                group = previous_state.get('group', 'Unknown group')
                member_info = previous_state.get('member_info', {})
                member_name = member_info.get('full_name', 'Unknown user')
                return f"User {member_name} removed from group {group}"
            
            elif change_type == "group_nested_group_added":
                parent_group = current_state.get('parent_group', 'Unknown group')
                nested_group = current_state.get('nested_group', 'Unknown nested group')
                return f"Group {nested_group} added to {parent_group}"
            
            elif change_type == "group_nested_group_removed":
                parent_group = previous_state.get('parent_group', 'Unknown group')
                nested_group = previous_state.get('nested_group', 'Unknown nested group')
                return f"Group {nested_group} removed from {parent_group}"
            
            else:
                return f"Group membership change: {change_type}"
                
        except Exception as e:
            logger.warning(f"Error formatting group change message: {str(e)}")
            return f"Group change: {change.change_type}"

    def _determine_change_severity(self, change: PermissionChange) -> str:
        """Determine severity level for a change."""
        try:
            change_type = change.change_type
            current_state = change.current_state or {}
            
            # High severity changes
            if change_type in ["permission_added", "group_member_added"]:
                # Check if this involves admin-level permissions
                permissions = current_state.get('permissions', {})
                if isinstance(permissions, dict):
                    if any(perm in str(permissions).lower() 
                          for perm in ['full_control', 'modify', 'write']):
                        return 'high'
                return 'medium'
            
            elif change_type in ["permission_removed", "group_member_removed"]:
                return 'medium'
            
            elif change_type == "permission_modified":
                return 'medium'
            
            else:
                return 'low'
                
        except Exception as e:
            logger.warning(f"Error determining change severity: {str(e)}")
            return 'medium'

    async def _process_notification_queue(self) -> None:
        """Process queued notifications."""
        try:
            logger.info("Notification queue processor started")
            
            while True:
                try:
                    # Get notification from queue
                    queue_item = await self._notification_queue.get()
                    notification = queue_item['notification']
                    target_user = queue_item['target_user']
                    broadcast = queue_item['broadcast']
                    
                    # Convert notification to message format
                    message = {
                        'id': notification.id,
                        'type': notification.type.value,
                        'title': notification.title,
                        'message': notification.message,
                        'severity': notification.severity,
                        'timestamp': notification.timestamp,
                        'data': notification.data,
                        'read': notification.read
                    }
                    
                    # Send notification
                    sent_count = 0
                    if broadcast:
                        sent_count = await self.connection_manager.broadcast(message)
                    elif target_user:
                        sent_count = await self.connection_manager.send_to_user(target_user, message)
                    
                    self.stats['notifications_sent'] += sent_count
                    
                    # Persist notification to database
                    await self._persist_notification(notification)
                    
                    logger.debug(f"Processed notification {notification.id} - sent to {sent_count} connections")
                    
                except Exception as queue_error:
                    logger.error(f"Error processing notification from queue: {str(queue_error)}")
                    
        except asyncio.CancelledError:
            logger.info("Notification queue processor cancelled")
        except Exception as e:
            logger.error(f"Notification queue processor error: {str(e)}")

    async def _persist_notification(self, notification: Notification) -> None:
        """Persist notification to database for audit trail."""
        try:
            # This could be implemented to store notifications in a database table
            # for audit purposes and to show notification history
            pass
        except Exception as e:
            logger.warning(f"Error persisting notification: {str(e)}")

    async def _acknowledge_notification(self, notification_id: str, 
                                     connection_id: str) -> None:
        """Handle notification acknowledgment from client."""
        try:
            # Send acknowledgment confirmation
            await self.connection_manager.send_to_connection(connection_id, {
                'type': 'notification_acknowledged',
                'notification_id': notification_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error acknowledging notification: {str(e)}")

    async def get_service_stats(self) -> Dict:
        """Get notification service statistics."""
        try:
            return {
                'active_connections': self.connection_manager.get_connection_count(),
                'unique_users': self.connection_manager.get_user_count(),
                'notifications_sent': self.stats['notifications_sent'],
                'notifications_queued': self.stats['notifications_queued'],
                'connections_established': self.stats['connections_established'],
                'connections_closed': self.stats['connections_closed'],
                'queue_size': self._notification_queue.qsize()
            }
        except Exception as e:
            logger.error(f"Error getting service stats: {str(e)}")
            return {'error': str(e)}

# Global notification service instance
notification_service = NotificationService()