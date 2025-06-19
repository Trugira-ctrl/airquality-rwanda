"""
Configuration module for Air Quality ETL
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for ETL pipeline"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    LOG_DIR = PROJECT_ROOT / 'logs'
    DATA_DIR = PROJECT_ROOT / 'data'
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'
    
    # Create directories if they don't exist
    for dir_path in [LOG_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'airspectrum_dev')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'thierry_sandbox')
    
    # PurpleAir API Configuration
    PURPLEAIR_API_KEY = os.getenv('PURPLEAIR_API_KEY', '')
    PURPLEAIR_BASE_URL = 'https://api.purpleair.com/v1/sensors'
    
    # Private sensors configuration
    # Format: "sensor_id:read_key,sensor_id:read_key"
    # Example: "12345:ABC123DEF,67890:GHI456JKL"
    PURPLEAIR_PRIVATE_SENSORS = os.getenv('PURPLEAIR_PRIVATE_SENSORS', '')
    
    # PurpleAir fields to request
    PURPLEAIR_FIELDS = [
        'sensor_index',
        'name',
        'latitude',
        'longitude',
        'last_seen',
        'humidity',
        'temperature',
        'pressure',
        'pm1.0',
        'pm1.0_cf_1',
        'pm2.5',
        'pm2.5_cf_1',
        'pm10.0',
        'pm10.0_cf_1'
    ]
    
    # REMA API Configuration (for future use)
    REMA_API_URL = os.getenv('REMA_API_URL', '')
    REMA_API_KEY = os.getenv('REMA_API_KEY', '')
    REMA_USERNAME = os.getenv('REMA_USERNAME', '')
    REMA_PASSWORD = os.getenv('REMA_PASSWORD', '')
    
    # ETL Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    SAVE_RAW_DATA = os.getenv('SAVE_RAW_DATA', 'true').lower() == 'true'
    
    # Timezone
    TIMEZONE = 'Africa/Kigali'
    
    # Run environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def get_db_connection_params(cls) -> Dict[str, any]:
        """Get database connection parameters for db_utils"""
        return {
            'host': cls.DB_HOST,
            'dbname': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'port': cls.DB_PORT
        }
    
    @classmethod
    def get_private_sensors(cls) -> Dict[str, str]:
        """
        Get private sensor configuration
        Can load from either environment variable or sensors.json file
        
        Returns:
            Dictionary mapping sensor_id to read_key
        """
        sensors = {}
        
        # First, try to load from PA_sensors.json if it exists
        sensors_file = cls.PROJECT_ROOT / 'PA_sensors.json'
        if sensors_file.exists():
            try:
                with open(sensors_file, 'r') as f:
                    data = json.load(f)
                    for sensor in data.get('sensors', []):
                        sensors[sensor['id']] = sensor['read_key']
                return sensors
            except Exception as e:
                print(f"Warning: Could not load PA_sensors.json: {e}")
        
        # Fall back to environment variable
        if cls.PURPLEAIR_PRIVATE_SENSORS:
            # Parse format: "sensor_id:read_key,sensor_id:read_key"
            for sensor_config in cls.PURPLEAIR_PRIVATE_SENSORS.split(','):
                if ':' in sensor_config:
                    sensor_id, read_key = sensor_config.strip().split(':', 1)
                    sensors[sensor_id] = read_key
        return sensors
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD not set")
        
        if not cls.PURPLEAIR_API_KEY:
            errors.append("PURPLEAIR_API_KEY not set")
        
        # Check for sensors in either format
        if not cls.get_private_sensors():
            errors.append("No sensors configured - set PURPLEAIR_PRIVATE_SENSORS in .env or create PA_sensors.json")
        
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive values)"""
        print("Current Configuration:")
        print(f"  Environment: {cls.ENVIRONMENT}")
        print(f"  Database: {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        print(f"  Schema: {cls.DB_SCHEMA}")
        print(f"  PurpleAir API: {'Configured' if cls.PURPLEAIR_API_KEY else 'Not configured'}")
        print(f"  Private Sensors: {len(cls.get_private_sensors())} configured")
        print(f"  REMA API: {'Configured' if cls.REMA_API_URL else 'Not configured'}")
        print(f"  Save Raw Data: {cls.SAVE_RAW_DATA}")
        print(f"  Timezone: {cls.TIMEZONE}")
    
    @classmethod
    def check_write_permissions(cls):
        """Check write permissions for configured directories"""
        # Check write permissions for LOG_DIR and RAW_DATA_DIR
        for dir_path in [cls.LOG_DIR, cls.RAW_DATA_DIR]:
            try:
                test_file = dir_path / "write_test.tmp"
                with open(test_file, "w") as f:
                    f.write("test")
                test_file.unlink()  # Remove the test file
            except Exception as e:
                print(f"ERROR: Cannot write to {dir_path}: {e}")


if __name__ == "__main__":
    Config.print_config()
    if Config.validate():
        print("\n✓ Configuration is valid")
    else:
        print("\n✗ Configuration has errors")