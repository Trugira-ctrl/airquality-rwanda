"""
Main ETL orchestrator for Air Quality data pipeline
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from db_utils import get_pgsql_cxn, upsert_df
from config import Config

# Import ETL modules
from extract_purpleair import extract_purpleair_data
from extract_rema import extract_rema_data
from transform import transform_purpleair_data, transform_rema_data

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Config.LOG_DIR / f'etl_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

print("Starting ETL main.py")  # Add this at the top


class AirQualityETL:
    """Main ETL orchestrator for air quality data"""
    
    def __init__(self):
        self.schema = Config.DB_SCHEMA
        self.stats = {
            'purpleair_extracted': 0,
            'purpleair_loaded': 0,
            'rema_extracted': 0,
            'rema_loaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def run_purpleair_etl(self):
        """Run ETL for PurpleAir data"""
        logger.info("Starting PurpleAir ETL...")
        
        try:
            # Extract
            api_data = extract_purpleair_data()
            
            # Transform
            df = transform_purpleair_data(api_data)
            self.stats['purpleair_extracted'] = len(df)
            
            if df.empty:
                logger.warning("No PurpleAir data to load")
                return
            
            # Load
            with get_pgsql_cxn(**Config.get_db_connection_params()) as cxn:
                upsert_df(
                    df=df,
                    schema=self.schema,
                    table_name='purpleair_readings',
                    cxn=cxn
                )
                self.stats['purpleair_loaded'] = len(df)
                
            logger.info(f"Loaded {len(df)} PurpleAir readings to {self.schema}.purpleair_readings")
            
        except Exception as e:
            logger.error(f"Error in PurpleAir ETL: {e}", exc_info=True)
            self.stats['errors'] += 1
            raise
    
    def run_rema_etl(self):
        """Run ETL for REMA data"""
        logger.info("REMA ETL skipped - VPN access required")
        # Will implement when VPN access is available
        pass
    
    def run_full_etl(self):
        """Run complete ETL for all data sources"""
        self.stats['start_time'] = datetime.now()
        logger.info("="*60)
        logger.info(f"Starting ETL run at {self.stats['start_time']}")
        logger.info(f"Target schema: {self.schema}")
        logger.info("="*60)
        
        # Run PurpleAir ETL
        try:
            if Config.PURPLEAIR_API_KEY:
                self.run_purpleair_etl()
            else:
                logger.warning("PurpleAir API key not configured, skipping")
        except Exception as e:
            logger.error(f"PurpleAir ETL failed: {e}")
        
        # Run REMA ETL (when available)
        if Config.REMA_API_URL:
            self.run_rema_etl()
        
        # Report results
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("="*60)
        logger.info("ETL Run Complete")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"PurpleAir: {self.stats['purpleair_extracted']} extracted, {self.stats['purpleair_loaded']} loaded")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*60)
        
        return self.stats
    
    def verify_data(self):
        """Verify data was loaded correctly"""
        logger.info("Verifying loaded data...")
        
        try:
            with get_pgsql_cxn(**Config.get_db_connection_params()) as cxn:
                # Check PurpleAir data
                query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT sensor_id) as unique_sensors,
                        MIN(time_stamp) as oldest_reading,
                        MAX(time_stamp) as newest_reading
                    FROM {self.schema}.purpleair_readings
                """
                
                df = pd.read_sql(query, cxn)
                stats = df.iloc[0]
                
                logger.info("Database verification:")
                logger.info(f"  Total records: {stats['total_records']}")
                logger.info(f"  Unique sensors: {stats['unique_sensors']}")
                logger.info(f"  Date range: {stats['oldest_reading']} to {stats['newest_reading']}")
                    
        except Exception as e:
            logger.error(f"Error verifying data: {e}")


def main():
    """Main entry point"""
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Create ETL instance and run
    etl = AirQualityETL()
    
    try:
        # Run full ETL
        stats = etl.run_full_etl()
        
        # Verify data if no errors
        if stats['errors'] == 0:
            etl.verify_data()
        
        # Exit with appropriate code
        sys.exit(0 if stats['errors'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Fatal error in ETL: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()