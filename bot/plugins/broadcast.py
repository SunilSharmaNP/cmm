# 14. bot/plugins/broadcast.py - Enhanced broadcast

import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message

try:
    from bot.database import Database
    from bot import DATABASE_URL, SESSION_NAME
    db = Database(DATABASE_URL, SESSION_NAME) if DATABASE_URL else None
except:
    db = None

LOGGER = logging.getLogger(__name__)

async def broadcast_(bot: Client, update: Message):
    """Enhanced broadcast function with better error handling and progress"""
    try:
        if not db:
            await update.reply_text("❌ Database not available for broadcast")
            return
            
        if not update.reply_to_message:
            await update.reply_text(
                "❌ **Please reply to a message to broadcast it**\\n\\n"
                "💡 **Tip:** Reply to any message (text, photo, video, etc.) with `/broadcast`"
            )
            return
            
        # Get all users
        all_users_cursor = await db.get_all_users()
        if not all_users_cursor:
            await update.reply_text("❌ No users found in database")
            return
            
        users_count = await db.total_users_count()
        
        if users_count == 0:
            await update.reply_text("❌ No users in database to broadcast to")
            return
        
        broadcast_msg = update.reply_to_message
        
        # Send initial progress message
        progress_msg = await update.reply_text(
            f"📢 **Starting Broadcast...**\\n\\n"
            f"👥 **Total Users:** {users_count:,}\\n"
            f"📊 **Progress:** 0/{users_count} (0.0%)\\n"
            f"✅ **Success:** 0\\n"
            f"❌ **Failed:** 0\\n"
            f"⏱️ **ETA:** Calculating..."
        )
        
        success_count = 0
        failed_count = 0
        blocked_count = 0
        deleted_accounts = 0
        
        start_time = asyncio.get_event_loop().time()
        
        # Convert cursor to list for memory-based storage compatibility
        if hasattr(all_users_cursor, '__aiter__'):
            users_list = []
            async for user in all_users_cursor:
                users_list.append(user)
        else:
            # For memory storage, it returns an async generator function
            users_list = []
            async for user in all_users_cursor():
                users_list.append(user)
        
        for i, user in enumerate(users_list):
            try:
                await broadcast_msg.copy(chat_id=user['id'])
                success_count += 1
            
            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "user is deactivated" in error_str:
                    blocked_count += 1
                elif "peer_id_invalid" in error_str or "user not found" in error_str:
                    deleted_accounts += 1
                else:
                    failed_count += 1
                    LOGGER.warning(f"Failed to send broadcast to {user['id']}: {e}")
            
            # Update progress every 25 users or at the end
            if (i + 1) % 25 == 0 or (i + 1) == len(users_list):
                try:
                    processed = i + 1
                    percentage = (processed / len(users_list)) * 100
                    
                    # Calculate ETA
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    if processed > 0:
                        time_per_user = elapsed_time / processed
                        remaining_users = len(users_list) - processed
                        eta_seconds = remaining_users * time_per_user
                        
                        if eta_seconds > 3600:
                            eta_str = f"{eta_seconds // 3600:.0f}h {(eta_seconds % 3600) // 60:.0f}m"
                        elif eta_seconds > 60:
                            eta_str = f"{eta_seconds // 60:.0f}m {eta_seconds % 60:.0f}s"
                        else:
                            eta_str = f"{eta_seconds:.0f}s"
                    else:
                        eta_str = "Calculating..."
                    
                    progress_text = (
                        f"📢 **Broadcasting in Progress...**\\n\\n"
                        f"👥 **Total Users:** {len(users_list):,}\\n"
                        f"📊 **Progress:** {processed}/{len(users_list)} ({percentage:.1f}%)\\n"
                        f"✅ **Success:** {success_count:,}\\n"
                        f"❌ **Failed:** {failed_count:,}\\n"
                        f"🚫 **Blocked/Deactivated:** {blocked_count:,}\\n"
                        f"👻 **Deleted Accounts:** {deleted_accounts:,}\\n"
                        f"⏱️ **ETA:** {eta_str}\\n"
                        f"⚡ **Speed:** {processed/elapsed_time:.1f} users/sec"
                    )
                    
                    await progress_msg.edit_text(progress_text)
                    
                except Exception as e:
                    LOGGER.error(f"Error updating progress: {e}")
                    pass
                    
            # Rate limiting - small delay between messages
            await asyncio.sleep(0.05)
        
        # Calculate final statistics
        total_processed = success_count + failed_count + blocked_count + deleted_accounts
        success_rate = (success_count / total_processed) * 100 if total_processed > 0 else 0
        total_time = asyncio.get_event_loop().time() - start_time
        
        # Final result message
        final_text = (
            f"✅ **Broadcast Completed!**\\n\\n"
            f"📊 **Final Statistics:**\\n"
            f"👥 **Total Users:** {len(users_list):,}\\n"
            f"✅ **Successfully Sent:** {success_count:,}\\n"
            f"❌ **Failed:** {failed_count:,}\\n"
            f"🚫 **Blocked/Deactivated:** {blocked_count:,}\\n"
            f"👻 **Deleted Accounts:** {deleted_accounts:,}\\n\\n"
            f"📈 **Success Rate:** {success_rate:.1f}%\\n"
            f"⏰ **Total Time:** {total_time/60:.1f} minutes\\n"
            f"⚡ **Average Speed:** {total_processed/total_time:.1f} users/sec\\n\\n"
            f"💡 **Tip:** Clean up deleted/blocked users regularly for better performance"
        )
        
        await progress_msg.edit_text(final_text)
        
        # Log broadcast completion
        LOGGER.info(
            f"Broadcast completed: {success_count} success, "
            f"{failed_count} failed, {blocked_count} blocked, "
            f"{deleted_accounts} deleted out of {len(users_list)} total users"
        )
        
    except Exception as e:
        LOGGER.error(f"Broadcast error: {e}")
        await update.reply_text("❌ Error during broadcast. Check logs for details.")

async def broadcast_stats(bot: Client, update: Message):
    """Get broadcast statistics"""
    try:
        if not db:
            await update.reply_text("❌ Database not available")
            return
            
        total_users = await db.total_users_count()
        active_users = await db.active_users_count(days=7)
        active_30d = await db.active_users_count(days=30)
        
        stats_text = (
            f"📊 **Broadcast Statistics**\\n\\n"
            f"👥 **Total Users:** {total_users:,}\\n"
            f"🟢 **Active (7 days):** {active_users:,} ({(active_users/total_users)*100:.1f}%)\\n"
            f"🟡 **Active (30 days):** {active_30d:,} ({(active_30d/total_users)*100:.1f}%)\\n\\n"
            f"**📈 Estimated Reach:**\\n"
            f"• Immediate: ~{int(active_users * 0.9):,} users\\n"
            f"• Within 24h: ~{int(active_30d * 0.7):,} users\\n"
            f"• Total potential: ~{int(total_users * 0.6):,} users\\n\\n"
            f"💡 **Note:** Estimates based on typical engagement rates"
        )
        
        await update.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"Broadcast stats error: {e}")
        await update.reply_text("❌ Error getting broadcast statistics")
