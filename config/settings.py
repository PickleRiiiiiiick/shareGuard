# config/settings.py
import os
from typing import Dict, Any

# Scanner settings
SCANNER_CONFIG = {
    "max_depth": 5,            
    "batch_size": 1000,        
    "cache_timeout": 300,      
    "excluded_paths": [        
        "C:\\Windows\\",
        "C:\\Program Files\\",
        "C:\\Program Files (x86)\\"
    ],
    "require_approved_targets": False
}

# API settings
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": False,
    "workers": 4,
    "timeout": 60,
    "cors_origins": [
        "http://localhost:5173",    # Development server
        "http://localhost:8000",    # Production/Static serving
        "http://127.0.0.1:5173",    # Alternative development URL
        "http://127.0.0.1:8000"     # Alternative production URL
    ],
    "allowed_hosts": [
        "localhost",
        "127.0.0.1"
    ]
}

# Enhanced Database settings
DB_CONFIG = {
    # Connection settings
    "driver": os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
    "server": os.getenv('DB_SERVER', 'localhost'),
    "database": os.getenv('DB_NAME', 'ShareGuard'),
    "username": os.getenv('DB_USER', 'shareguard_user'),
    "password": os.getenv('DB_PASSWORD', 'YourStrongPassword123!'),
    "trusted_connection": os.getenv('DB_USE_WINDOWS_AUTH', 'true').lower() == 'true',
    
    # Pool settings
    "pool_size": int(os.getenv('DB_POOL_SIZE', '5')),
    "max_overflow": int(os.getenv('DB_MAX_OVERFLOW', '10')),
    "timeout": int(os.getenv('DB_TIMEOUT', '30')),
    
    # Additional SQL Server specific settings
    "pool_recycle": int(os.getenv('DB_POOL_RECYCLE', '1800')),
    "command_timeout": int(os.getenv('DB_COMMAND_TIMEOUT', '60')),
    "fast_executemany": True,
    "use_mars": True
}

# Construct database URL
def get_db_url() -> str:
    """Generate database connection URL based on configuration."""
    # Use SQLite for development if SQL Server isn't available
    use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    
    if use_sqlite:
        db_path = os.getenv('SQLITE_PATH', 'shareguard.db')
        return f'sqlite:///{db_path}'
    
    if DB_CONFIG['trusted_connection']:
        params = [
            f"Driver={{{DB_CONFIG['driver']}}}",
            f"Server={DB_CONFIG['server']}",
            f"Database={DB_CONFIG['database']}",
            "Trusted_Connection=yes"
        ]
    else:
        params = [
            f"Driver={{{DB_CONFIG['driver']}}}",
            f"Server={DB_CONFIG['server']}",
            f"Database={DB_CONFIG['database']}",
            f"UID={DB_CONFIG['username']}",
            f"PWD={DB_CONFIG['password']}"
        ]
    
    if DB_CONFIG['use_mars']:
        params.append("MARS_Connection=yes")
    
    return 'mssql+pyodbc:///?odbc_connect=' + ';'.join(params)

# Update DB_CONFIG with the connection URL
DB_CONFIG['url'] = get_db_url()

# Logging settings
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "shareguard.log",
    "max_size": 10485760,  # 10MB
    "backup_count": 5
}

# Security settings
SECURITY_CONFIG = {
    "secret_key": os.getenv('SECRET_KEY', 'your-secret-key-here'),
    "token_expire_minutes": 1440,  # 24 hours
    "algorithm": "HS256",
    # Added security headers
    "security_headers": {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
}