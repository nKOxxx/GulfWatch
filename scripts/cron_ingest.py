#!/usr/bin/env python3
"""
Cron script to run Twitter ingestion for Gulf Watch
Called every 5 minutes by cron
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from sqlalchemy.orm import Session
from models import get_db, init_database
from ingestion.twitter import TwitterIngestion

def main():
    """Run Twitter ingestion"""
    try:
        print("🔄 Starting Twitter ingestion...")
        
        # Initialize DB
        init_database()
        
        # Get DB session
        db = next(get_db())
        
        # Run ingestion
        ingestion = TwitterIngestion(db)
        new_reports = ingestion.run_ingestion()
        
        print(f"✅ Ingestion complete: {new_reports} new reports")
        
        # Auto-convert reports to incidents
        if new_reports > 0:
            from api_v2 import convert_pending_reports
            result = convert_pending_reports(db)
            print(f"✅ Converted reports: {result}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
