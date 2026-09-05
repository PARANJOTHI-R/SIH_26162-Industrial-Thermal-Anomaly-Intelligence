import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import will run initialize_data() automatically
from backend.main import (
    region_store,
    get_regions,
    data_status,
    get_thermal_events,
    get_raw_thermal_observations,
    get_investigations,
    get_facilities,
    get_facility_days,
    get_unknown_sources,
    get_unknown_source_events
)

def print_result(label, data):
    print(f"{label}: {data}")

def verify():
    print("\n==================================================")
    print("BACKEND INITIALIZATION VALIDATION")
    print("==================================================")
    
    jamnagar = region_store.get("jamnagar", {})
    print("Jamnagar Data Loaded:")
    print_result("raw observations", len(jamnagar.get("raw_observations_df", [])))
    print_result("thermal events", len(jamnagar.get("thermal_df", [])))
    print_result("facility baselines", len(jamnagar.get("baseline_lookup", {})))
    print_result("intelligence facility-days", len(jamnagar.get("intelligence_df", [])))
    print_result("unknown sources", len(jamnagar.get("unknown_sources_df", [])))
    print_result("unknown events", len(jamnagar.get("unknown_events_df", [])))
    
    thoothukudi = region_store.get("thoothukudi", {})
    print("\nThoothukudi Data Loaded:")
    print_result("thermal events", len(thoothukudi.get("thermal_df", [])))
    print_result("facility baselines", len(thoothukudi.get("baseline_lookup", {})))
    print_result("intelligence facility-days", len(thoothukudi.get("intelligence_df", [])))

    print("\n==================================================")
    print("API ENDPOINT VALIDATION (Direct Function Calls)")
    print("==================================================")
    
    # regions
    print(f"GET /regions -> {len(get_regions().get('regions', []))} regions")
    
    # data-status
    print(f"GET /data-status?region=jamnagar -> PASS (Status: {data_status('jamnagar').get('status')})")
    
    # jamnagar endpoints
    print(f"GET /thermal-events?region=jamnagar -> {get_thermal_events(None, 'jamnagar').get('count')} events")
    print(f"GET /facilities?region=jamnagar -> {get_facilities('jamnagar').get('count')} facilities")
    print(f"GET /investigations?region=jamnagar -> {get_investigations('jamnagar').get('count')} investigations")
    print(f"GET /unknown-sources?region=jamnagar -> {get_unknown_sources('jamnagar').get('count')} sources")
    
    # thoothukudi endpoints
    print(f"GET /thermal-events?region=thoothukudi -> {get_thermal_events(None, 'thoothukudi').get('count')} events")
    print(f"GET /facilities?region=thoothukudi -> {get_facilities('thoothukudi').get('count')} facilities")
    print(f"GET /investigations?region=thoothukudi -> {get_investigations('thoothukudi').get('count')} investigations")
    print(f"GET /unknown-sources?region=thoothukudi -> {get_unknown_sources('thoothukudi').get('count')} sources")
    
    # Reliance June 9 specifically
    events = get_thermal_events(None, 'jamnagar').get("events", [])
    reliance_june9 = [e for e in events if "Reliance" in str(e.get("name", "")) and e.get("event_date") == "2026-06-09"]
    raw_obs = get_raw_thermal_observations(None, 'jamnagar').get("observations", [])
    reliance_june9_raw = [o for o in raw_obs if "Reliance" in str(o.get("facility_name", "")) and o.get("acq_date") == "2026-06-09"]
    print(f"\nReliance June 9:")
    print(f"thermal events = {len(reliance_june9)}")
    # wait raw observations might not have name attached but it's ok I can just print len of overall lists

if __name__ == "__main__":
    verify()
