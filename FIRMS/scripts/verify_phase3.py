import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.regions import REGIONS

def verify_region(region_id):
    print(f"==================================================")
    print(f"VERIFYING REGION: {region_id.upper()}")
    print(f"==================================================")
    
    config = REGIONS.get(region_id)
    if not config:
        print(f"ERROR: Region {region_id} not found in config.")
        return
        
    analysis_dir = config["analysis_dir"]
    
    # Check thermal events
    events_file = analysis_dir / "thermal_events.csv"
    if events_file.exists():
        df = pd.read_csv(events_file)
        print(f"Thermal events: {len(df)}")
    else:
        print(f"ERROR: {events_file} not found.")
        
    # Check behavior baseline
    baseline_file = analysis_dir / "facility_behavior_baseline.csv"
    if baseline_file.exists():
        df = pd.read_csv(baseline_file)
        print(f"Facility baselines: {len(df)}")
    else:
        print(f"ERROR: {baseline_file} not found.")
        
    # Check intelligence summary
    intelligence_file = analysis_dir / "thermal_source_behavior_intelligence.csv"
    if intelligence_file.exists():
        df = pd.read_csv(intelligence_file)
        print(f"Intelligence facility-days: {len(df)}")
    else:
        print(f"ERROR: {intelligence_file} not found.")

if __name__ == "__main__":
    verify_region("jamnagar")
    print("\n")
    verify_region("thoothukudi")
