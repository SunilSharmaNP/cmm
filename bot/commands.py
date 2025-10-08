# 6. bot/commands.py - Enhanced commands

from bot.get_cfg import get_config

class Command:
    """Enhanced command configuration with aliases"""
    
    # Basic Commands
    START = get_config("COMMAND_START", "start")
    COMPRESS = get_config("COMMAND_COMPRESS", "compress")
    CANCEL = get_config("COMMAND_CANCEL", "cancel")
    HELP = get_config("COMMAND_HELP", "help")
    
    # Admin Commands  
    STATUS = get_config("COMMAND_STATUS", "status")
    EXEC = get_config("COMMAND_EXEC", "exec")
    LOGS = get_config("COMMAND_LOGS", "logs")
    BROADCAST = get_config("COMMAND_BROADCAST", "broadcast")
    BAN = get_config("COMMAND_BAN", "ban")
    UNBAN = get_config("COMMAND_UNBAN", "unban")
    
    # Enhanced Commands
    QUEUE = get_config("COMMAND_QUEUE", "queue")
    SETTINGS = get_config("COMMAND_SETTINGS", "settings")
    STATS = get_config("COMMAND_STATS", "stats")
    BACKUP = get_config("COMMAND_BACKUP", "backup")
    
    # Command aliases for better user experience
    ALIASES = {
        START: ["begin", "init"],
        COMPRESS: ["comp", "c", "encode"],
        CANCEL: ["stop", "abort", "x"],
        HELP: ["h", "info", "?"],
        STATUS: ["stat", "s"],
        QUEUE: ["q", "list"],
        SETTINGS: ["config", "cfg", "set"]
    }
    
    @classmethod
    def get_all_commands(cls) -> list:
        """Get all available commands"""
        return [
            cls.START, cls.COMPRESS, cls.CANCEL, cls.HELP,
            cls.STATUS, cls.EXEC, cls.LOGS, cls.BROADCAST,
            cls.BAN, cls.UNBAN, cls.QUEUE, cls.SETTINGS,
            cls.STATS, cls.BACKUP
        ]
    
    @classmethod
    def get_public_commands(cls) -> list:
        """Get public commands available to all users"""
        return [cls.START, cls.COMPRESS, cls.HELP, cls.QUEUE, cls.SETTINGS]
    
    @classmethod
    def get_admin_commands(cls) -> list:
        """Get admin-only commands"""
        return [
            cls.STATUS, cls.EXEC, cls.LOGS, cls.BROADCAST,
            cls.BAN, cls.UNBAN, cls.STATS, cls.BACKUP, cls.CANCEL
        ]
