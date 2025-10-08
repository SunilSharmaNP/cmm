# 8. bot/database/database.py - Enhanced database module

import datetime
import motor.motor_asyncio
from typing import Optional, List, Dict, Any
import asyncio
import logging

LOGGER = logging.getLogger(__name__)

class Database:
    """Enhanced Database class with improved functionality"""
    
    def __init__(self, uri: str, database_name: str):
        try:
            if not uri or uri == "":
                LOGGER.warning("Database URL not provided. Using in-memory storage.")
                self._client = None
                self.db = None
                self.users = None
                self.settings = None
                self.stats = None
                self.queue = None
                self._use_memory = True
                self._memory_users = {}
                return
                
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                uri, 
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            self.db = self._client[database_name]
            self.users = self.db.users
            self.settings = self.db.user_settings
            self.stats = self.db.bot_stats
            self.queue = self.db.compression_queue
            self._use_memory = False
            self._memory_users = {}
            LOGGER.info("Database connection established")
        except Exception as e:
            LOGGER.error(f"Database connection failed: {e}")
            LOGGER.warning("Falling back to in-memory storage")
            self._client = None
            self.db = None
            self.users = None
            self.settings = None
            self.stats = None
            self.queue = None
            self._use_memory = True
            self._memory_users = {}
    
    def new_user(self, id: int, username: str = None, first_name: str = None) -> Dict[str, Any]:
        """Create new user document with enhanced fields"""
        return {
            'id': id,
            'username': username,
            'first_name': first_name,
            'join_date': datetime.date.today().isoformat(),
            'last_active': datetime.datetime.utcnow().isoformat(),
            'total_compressions': 0,
            'total_size_compressed': 0,
            'ban_status': {
                'is_banned': False,
                'ban_duration': 0,
                'banned_on': datetime.date.max.isoformat(),
                'ban_reason': '',
                'banned_by': None
            },
            'settings': {
                'default_quality': 50,
                'output_format': 'mp4',
                'custom_thumbnail': None,
                'progress_updates': True,
                'notifications': True
            }
        }
    
    async def add_user(self, id: int, username: str = None, first_name: str = None) -> bool:
        """Add new user to database"""
        try:
            if self._use_memory:
                self._memory_users[id] = self.new_user(id, username, first_name)
                return True
                
            user = self.new_user(id, username, first_name)
            await self.users.insert_one(user)
            LOGGER.info(f"New user added: {id} ({username})")
            return True
        except Exception as e:
            LOGGER.error(f"Error adding user {id}: {e}")
            return False
    
    async def is_user_exist(self, id: int) -> bool:
        """Check if user exists in database"""
        try:
            if self._use_memory:
                return id in self._memory_users
                
            user = await self.users.find_one({'id': int(id)})
            return bool(user)
        except Exception as e:
            LOGGER.error(f"Error checking user existence {id}: {e}")
            return False
    
    async def get_user(self, id: int) -> Optional[Dict[str, Any]]:
        """Get user document by ID"""
        try:
            if self._use_memory:
                return self._memory_users.get(id)
                
            return await self.users.find_one({'id': int(id)})
        except Exception as e:
            LOGGER.error(f"Error getting user {id}: {e}")
            return None
    
    async def update_user_activity(self, id: int) -> bool:
        """Update user's last activity time"""
        try:
            if self._use_memory:
                if id in self._memory_users:
                    self._memory_users[id]['last_active'] = datetime.datetime.utcnow().isoformat()
                return True
                
            await self.users.update_one(
                {'id': id},
                {'$set': {'last_active': datetime.datetime.utcnow().isoformat()}}
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating user activity {id}: {e}")
            return False
    
    async def total_users_count(self) -> int:
        """Get total number of users"""
        try:
            if self._use_memory:
                return len(self._memory_users)
                
            return await self.users.count_documents({})
        except Exception as e:
            LOGGER.error(f"Error counting users: {e}")
            return 0
    
    async def active_users_count(self, days: int = 7) -> int:
        """Get count of active users in last N days"""
        try:
            if self._use_memory:
                # Simple count for memory storage
                return len(self._memory_users)
                
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            return await self.users.count_documents({
                'last_active': {'$gte': cutoff.isoformat()}
            })
        except Exception as e:
            LOGGER.error(f"Error counting active users: {e}")
            return 0
    
    # Ban/Unban functionality
    async def ban_user(self, user_id: int, ban_duration: int, ban_reason: str, banned_by: int) -> bool:
        """Ban a user with enhanced tracking"""
        try:
            ban_status = {
                'is_banned': True,
                'ban_duration': ban_duration,
                'banned_on': datetime.datetime.utcnow().isoformat(),
                'ban_reason': ban_reason,
                'banned_by': banned_by
            }
            
            if self._use_memory:
                if user_id in self._memory_users:
                    self._memory_users[user_id]['ban_status'] = ban_status
                return True
                
            await self.users.update_one(
                {'id': user_id},
                {'$set': {'ban_status': ban_status}}
            )
            LOGGER.info(f"User {user_id} banned by {banned_by}")
            return True
        except Exception as e:
            LOGGER.error(f"Error banning user {user_id}: {e}")
            return False
    
    async def remove_ban(self, id: int) -> bool:
        """Remove ban from user"""
        try:
            ban_status = {
                'is_banned': False,
                'ban_duration': 0,
                'banned_on': datetime.date.max.isoformat(),
                'ban_reason': '',
                'banned_by': None
            }
            
            if self._use_memory:
                if id in self._memory_users:
                    self._memory_users[id]['ban_status'] = ban_status
                return True
                
            await self.users.update_one(
                {'id': id},
                {'$set': {'ban_status': ban_status}}
            )
            LOGGER.info(f"User {id} unbanned")
            return True
        except Exception as e:
            LOGGER.error(f"Error unbanning user {id}: {e}")
            return False
    
    async def get_ban_status(self, id: int) -> Dict[str, Any]:
        """Get user's ban status"""
        try:
            if self._use_memory:
                user = self._memory_users.get(id)
                if user:
                    return user.get('ban_status', {'is_banned': False})
                return {'is_banned': False}
                
            user = await self.users.find_one({'id': int(id)})
            if user:
                return user.get('ban_status', {'is_banned': False})
            return {'is_banned': False}
        except Exception as e:
            LOGGER.error(f"Error getting ban status {id}: {e}")
            return {'is_banned': False}
    
    async def get_all_banned_users(self) -> List[Dict[str, Any]]:
        """Get all banned users"""
        try:
            if self._use_memory:
                return [
                    user for user in self._memory_users.values()
                    if user.get('ban_status', {}).get('is_banned', False)
                ]
                
            cursor = self.users.find({'ban_status.is_banned': True})
            return await cursor.to_list(length=None)
        except Exception as e:
            LOGGER.error(f"Error getting banned users: {e}")
            return []
    
    async def increment_user_compression(self, user_id: int, file_size: int = 0) -> bool:
        """Increment user's compression count and size"""
        try:
            if self._use_memory:
                if user_id in self._memory_users:
                    self._memory_users[user_id]['total_compressions'] += 1
                    self._memory_users[user_id]['total_size_compressed'] += file_size
                return True
                
            await self.users.update_one(
                {'id': user_id},
                {
                    '$inc': {
                        'total_compressions': 1,
                        'total_size_compressed': file_size
                    }
                }
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating compression stats {user_id}: {e}")
            return False
    
    async def get_all_users(self):
        """Get all users cursor"""
        try:
            if self._use_memory:
                # Return an async generator for memory storage
                async def memory_generator():
                    for user in self._memory_users.values():
                        yield user
                return memory_generator()
                
            return self.users.find({})
        except Exception as e:
            LOGGER.error(f"Error getting all users: {e}")
            return None
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user completely from database"""
        try:
            if self._use_memory:
                if user_id in self._memory_users:
                    del self._memory_users[user_id]
                return True
                
            await self.users.delete_many({'id': int(user_id)})
            return True
        except Exception as e:
            LOGGER.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def close_connection(self):
        """Close database connection"""
        try:
            if self._client:
                self._client.close()
                LOGGER.info("Database connection closed")
        except Exception as e:
            LOGGER.error(f"Error closing database connection: {e}")

print("Created database and commands modules")
