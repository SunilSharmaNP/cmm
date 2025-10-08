# 17. bot/plugins/status_message_fn.py - Enhanced status and exec

import os
import subprocess
import logging
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from bot import AUTH_USERS, LOG_FILE_ZZGEVC
from bot.helper_funcs.display_progress import humanbytes

LOGGER = logging.getLogger(__name__)

async def exec_message_f(bot: Client, update: Message):
    """Enhanced exec command with safety checks"""
    try:
        if update.from_user.id not in AUTH_USERS:
            await update.reply_text("❌ Unauthorized access denied")
            return
            
        if len(update.command) < 2:
            await update.reply_text(
                "**Usage:** `/exec <command>`\\n\\n"
                "**Examples:**\\n"
                "• `/exec ls -la`\\n"
                "• `/exec df -h`\\n"
                "• `/exec ps aux | grep python`\\n\\n"
                "⚠️ **Warning:** Use with caution!"
            )
            return
            
        command = " ".join(update.command[1:])
        
        # Basic safety checks
        dangerous_commands = ['rm -rf', 'dd if=', 'mkfs', 'format', ':(){ :|:& };:', 'shutdown', 'reboot']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            await update.reply_text(
                "🚫 **Dangerous command detected!**\\n\\n"
                "This command could harm the system and has been blocked.\\n"
                "Please use safe commands only."
            )
            return
        
        # Send "executing" message
        exec_msg = await update.reply_text(
            f"⚙️ **Executing command...**\\n\\n"
            f"```bash\\n{command}\\n```\\n\\n"
            f"⏳ Please wait..."
        )
        
        try:
            # Execute command with timeout
            result = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=30
            )
            
            stdout, stderr = await result.communicate()
            
            output = ""
            if stdout:
                output += f"**📤 STDOUT:**\\n```\\n{stdout.decode()[:2000]}\\n```\\n\\n"
            
            if stderr:
                output += f"**📥 STDERR:**\\n```\\n{stderr.decode()[:2000]}\\n```\\n\\n"
            
            if not output:
                output = "✅ **Command executed successfully (no output)**"
            
            output += f"**🔢 Exit Code:** {result.returncode}"
            
            # If output is too long, send as file
            if len(output) > 4000:
                with open("command_output.txt", "w") as f:
                    f.write(f"Command: {command}\\n\\n")
                    f.write(f"STDOUT:\\n{stdout.decode()}\\n\\n")
                    f.write(f"STDERR:\\n{stderr.decode()}\\n\\n")
                    f.write(f"Exit Code: {result.returncode}")
                
                await bot.send_document(
                    chat_id=update.chat.id,
                    document="command_output.txt",
                    caption=f"📄 **Command Output**\\n\\n```bash\\n{command}\\n```"
                )
                
                os.remove("command_output.txt")
                await exec_msg.delete()
            else:
                await exec_msg.edit_text(output)
            
        except asyncio.TimeoutError:
            await exec_msg.edit_text(
                f"⏰ **Command Timeout**\\n\\n"
                f"```bash\\n{command}\\n```\\n\\n"
                f"❌ Command took too long to execute (>30 seconds)"
            )
        except Exception as e:
            await exec_msg.edit_text(
                f"❌ **Execution Error**\\n\\n"
                f"```bash\\n{command}\\n```\\n\\n"
                f"🔍 **Error:** {str(e)}"
            )
            
    except Exception as e:
        LOGGER.error(f"Exec command error: {e}")
        await update.reply_text("❌ Fatal error in exec command")

async def upload_log_file(bot: Client, update: Message):
    """Enhanced log file upload with options"""
    try:
        if update.from_user.id not in AUTH_USERS:
            await update.reply_text("❌ Unauthorized access denied")
            return
        
        if not os.path.exists(LOG_FILE_ZZGEVC):
            await update.reply_text(
                "❌ **Log file not found**\\n\\n"
                f"Expected location: `{LOG_FILE_ZZGEVC}`\\n"
                "The log file may not have been created yet."
            )
            return
        
        # Get file info
        file_size = os.path.getsize(LOG_FILE_ZZGEVC)
        file_size_mb = file_size / (1024 * 1024)
        
        # Check if user wants specific log type
        log_type = "full"
        if len(update.command) > 1:
            log_type = update.command[1].lower()
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            await update.reply_text(
                f"⚠️ **Log file is very large**\\n\\n"
                f"📏 **Size:** {humanbytes(file_size)}\\n\\n"
                f"**Options:**\\n"
                f"• Use `/log tail` for recent logs only\\n"
                f"• Use `/log errors` for error logs only\\n"
                f"• Use `/log clean` to clean old logs first"
            )
            return
        
        if log_type == "tail":
            # Send last 500 lines
            try:
                result = await asyncio.create_subprocess_exec(
                    'tail', '-n', '500', LOG_FILE_ZZGEVC,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    temp_log = LOG_FILE_ZZGEVC + '.tail'
                    with open(temp_log, 'w') as f:
                        f.write(stdout.decode())
                    
                    await bot.send_document(
                        chat_id=update.chat.id,
                        document=temp_log,
                        caption="📋 **Recent Bot Logs** (Last 500 lines)",
                        reply_to_message_id=update.id
                    )
                    
                    os.remove(temp_log)
                else:
                    raise Exception("tail command failed")
                    
            except:
                # Fallback method
                with open(LOG_FILE_ZZGEVC, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-500:] if len(lines) > 500 else lines
                
                temp_log = LOG_FILE_ZZGEVC + '.tail'
                with open(temp_log, 'w') as f:
                    f.writelines(recent_lines)
                
                await bot.send_document(
                    chat_id=update.chat.id,
                    document=temp_log,
                    caption="📋 **Recent Bot Logs**",
                    reply_to_message_id=update.id
                )
                
                os.remove(temp_log)
                
        elif log_type == "errors":
            # Extract error logs
            try:
                result = await asyncio.create_subprocess_exec(
                    'grep', '-i', 'error\\|exception\\|traceback\\|failed', LOG_FILE_ZZGEVC,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0 and stdout:
                    temp_log = LOG_FILE_ZZGEVC + '.errors'
                    with open(temp_log, 'w') as f:
                        f.write(stdout.decode())
                    
                    await bot.send_document(
                        chat_id=update.chat.id,
                        document=temp_log,
                        caption="🔍 **Error Logs Only**",
                        reply_to_message_id=update.id
                    )
                    
                    os.remove(temp_log)
                else:
                    await update.reply_text("✅ No errors found in logs!")
                    
            except Exception as e:
                await update.reply_text(f"❌ Error extracting error logs: {e}")
                
        elif log_type == "clean":
            # Clean old logs and show info
            try:
                # Backup current log
                backup_name = LOG_FILE_ZZGEVC + '.backup'
                with open(LOG_FILE_ZZGEVC, 'r') as src, open(backup_name, 'w') as dst:
                    dst.write(src.read())
                
                # Clear current log
                with open(LOG_FILE_ZZGEVC, 'w') as f:
                    f.write(f"# Log cleaned at {datetime.now()}\\n")
                
                await update.reply_text(
                    f"🧹 **Logs Cleaned Successfully**\\n\\n"
                    f"📋 Old log backed up as: `{backup_name}`\\n"
                    f"📏 Freed space: {humanbytes(file_size)}\\n\\n"
                    f"✨ Fresh log file created"
                )
                
            except Exception as e:
                await update.reply_text(f"❌ Error cleaning logs: {e}")
                
        else:
            # Send full log file
            await bot.send_document(
                chat_id=update.chat.id,
                document=LOG_FILE_ZZGEVC,
                caption=(
                    f"📋 **Complete Bot Logs**\\n\\n"
                    f"📏 **Size:** {humanbytes(file_size)}\\n"
                    f"📅 **Generated:** Just now\\n\\n"
                    f"💡 **Tip:** Use `/log tail` for recent logs only"
                ),
                reply_to_message_id=update.id
            )
        
    except Exception as e:
        LOGGER.error(f"Upload log error: {e}")
        await update.reply_text("❌ Error uploading logs")

async def server_stats(bot: Client, update: Message):
    """Get detailed server statistics"""
    try:
        if update.from_user.id not in AUTH_USERS:
            await update.reply_text("❌ Unauthorized access")
            return
        
        from bot.helper_funcs.utils import SystemUtils
        system_info = SystemUtils.get_system_info()
        
        # Get additional system info
        try:
            # Disk usage for different paths
            download_size = 0
            log_size = 0
            
            from bot import DOWNLOAD_LOCATION
            from bot.helper_funcs.utils import CleanupManager
            download_size = await CleanupManager.get_directory_size(DOWNLOAD_LOCATION)
            
            if os.path.exists(LOG_FILE_ZZGEVC):
                log_size = os.path.getsize(LOG_FILE_ZZGEVC)
            
        except:
            download_size = 0
            log_size = 0
        
        stats_text = (
            f"🖥️ **Detailed Server Statistics**\\n\\n"
            f"**💻 System Resources:**\\n"
            f"• CPU Cores: {system_info.get('cpu_count', 'N/A')}\\n"
            f"• CPU Usage: {system_info.get('cpu_percent', 0):.1f}%\\n"
            f"• Memory Total: {humanbytes(system_info.get('memory_total', 0))}\\n"
            f"• Memory Used: {system_info.get('memory_percent', 0):.1f}%\\n"
            f"• Memory Available: {humanbytes(system_info.get('memory_available', 0))}\\n"
            f"• Disk Total: {humanbytes(system_info.get('disk_total', 0))}\\n"
            f"• Disk Used: {system_info.get('disk_percent', 0):.1f}%\\n"
            f"• Disk Free: {humanbytes(system_info.get('disk_free', 0))}\\n\\n"
            f"**📁 Bot Storage Usage:**\\n"
            f"• Downloads: {humanbytes(download_size)}\\n"
            f"• Log File: {humanbytes(log_size)}\\n\\n"
            f"**🔧 Process Information:**\\n"
            f"• PID: {os.getpid()}\\n"
            f"• Python: {sys.version.split()[0]}\\n"
        )
        
        # Add network info if available
        try:
            import socket
            hostname = socket.gethostname()
            stats_text += f"• Hostname: {hostname}\\n"
        except:
            pass
        
        await update.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"Server stats error: {e}")
        await update.reply_text("❌ Error getting server statistics")

print("Created help and status modules")
