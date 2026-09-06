import urllib.request
import json
import traceback

base = 'http://127.0.0.1:18765'

def get(endpoint):
    req = urllib.request.Request(f"{base}{endpoint}")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

print("==================================================")
print("11. ENDPOINT SMOKE TESTS")
print("==================================================")
endpoints = [
    "/health",
    "/regions",
    "/summary?region=jamnagar",
    "/summary?region=thoothukudi",
    "/facility-days?region=jamnagar",
    "/facility-days?region=thoothukudi",
    "/investigations?region=jamnagar",
    "/investigations?region=thoothukudi",
    "/unknown-sources?region=jamnagar",
    "/unknown-sources?region=thoothukudi"
]

for ep in endpoints:
    try:
        req = urllib.request.Request(f"{base}{ep}")
        with urllib.request.urlopen(req) as response:
            print(f"{ep}: {response.getcode()} OK")
    except Exception as e:
        print(f"{ep}: FAIL - {e}")

print("\n==================================================")
print("2. EXACT REGION VALIDATION")
print("==================================================")

sum_jam = get("/summary?region=jamnagar")
sum_thoo = get("/summary?region=thoothukudi")

print("REGION | RAW OBS | EVENTS | FACILITY DAYS | FACILITIES | INVESTIGATION CANDIDATES | UNMATCHED EVENTS | PERSISTENT UNKNOWN SOURCES")

def fmt_sum(r, s):
    # unmatched events is not directly in summary, let's pull from unknown sources
    unks = get(f"/unknown-sources?region={r}")['sources'] if get(f"/unknown-sources?region={r}") else []
    unmatched_evts = sum(u.get('event_count', 0) for u in unks)
    persistent = sum(1 for u in unks if u.get('persistence_class') in ('PERSISTENT', 'RECURRING') and u.get('event_count', 0) >= 3)
    return f"{r.capitalize()} | {s.get('raw_observations')} | {s.get('thermal_events')} | {s.get('facility_days')} | {s.get('facilities')} | {s.get('investigation_candidates')} | {unmatched_evts} | {persistent}"

print(fmt_sum("jamnagar", sum_jam))
print(fmt_sum("thoothukudi", sum_thoo))

print("\nREGION | HIGH | MEDIUM | LOW | INSUFFICIENT")
def count_eq(r):
    invs = get(f"/investigations?region={r}")['investigations']
    counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INSUFFICIENT': 0}
    for i in invs:
        eq = i.get('evidence_quality', 'UNKNOWN')
        if eq in counts:
            counts[eq] += 1
    return f"{r.capitalize()} | {counts['HIGH']} | {counts['MEDIUM']} | {counts['LOW']} | {counts['INSUFFICIENT']}"

print(count_eq("jamnagar"))
print(count_eq("thoothukudi"))


print("\n==================================================")
print("3. INVESTIGATION QUEUE FORENSIC CHECK")
print("==================================================")

def dump_queue(r):
    print(f"\n--- {r.upper()} QUEUE ---")
    invs = get(f"/investigations?region={r}")['investigations']
    cands = [i for i in invs if i.get('is_investigation_candidate')]
    
    # Sort same as frontend queue
    priorityOrder = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    cands.sort(key=lambda x: (priorityOrder.get(x.get('investigation_priority'), 9), -float(x.get('behavior_score') or 0)))
    
    for c in cands:
        fid = c.get('facility_name') or c.get('name') or 'Unmatched source'
        print(f"Candidate: {fid} | Date: {c.get('acq_date')}")
        print(f"  Source Class: {c.get('source_class')}")
        print(f"  Behaviour: {c.get('behavior_state')} (Score: {c.get('behavior_score')})")
        print(f"  Priority: {c.get('investigation_priority')}")
        print(f"  Evidence Quality: {c.get('evidence_quality')}")
        print(f"  Persistence: {c.get('persistence_state')}")
        print(f"  Baseline: active_days={c.get('baseline_active_days')}, prev_active_days={c.get('previous_active_days')}")
        print(f"  Assoc: {c.get('association_type')} / {c.get('evidence_strength')}")
        print("-" * 20)

dump_queue("jamnagar")
dump_queue("thoothukudi")


print("\n==================================================")
print("4. UNKNOWN ACTIVITY FORENSICS")
print("==================================================")
for r in ["jamnagar", "thoothukudi"]:
    unks = get(f"/unknown-sources?region={r}")
    if unks and unks.get('sources'):
        sources = unks['sources']
        print(f"\n--- {r.upper()} UNMATCHED ---")
        persistent = [s for s in sources if s.get('persistence_class') in ('PERSISTENT', 'RECURRING') and s.get('event_count', 0) >= 3]
        transient = [s for s in sources if s not in persistent]
        
        print(f"Unmatched thermal events: {sum(s.get('event_count',0) for s in sources)}")
        print(f"Transient unmatched sources: {len(transient)}")
        print(f"Persistent unmatched sources: {len(persistent)}")
        
        ind_cands = [s for s in sources if s.get('source_class') == 'INDUSTRIAL_ASSOCIATED' and s.get('is_investigation_candidate')]
        print(f"Candidate industrial-associated unmatched sources: {len(ind_cands)}")
        
        for s in persistent:
            print(f"\nSource ID: {s.get('source_id')}")
            print(f"  Events: {s.get('event_count')} (Active days: {s.get('active_days')})")
            print(f"  Dates: {s.get('first_observed_date')} to {s.get('last_observed_date')}")
            print(f"  Diameter: {s.get('diameter_km')} km")
            print(f"  Nearest Known: {s.get('nearest_known_facility')} ({s.get('nearest_known_facility_distance_km')} km)")
            print(f"  Class: {s.get('source_class')} | Behaviour: {s.get('behavior_state')}")
            print(f"  Eq: {s.get('evidence_quality')} | Prio: {s.get('investigation_priority')}")

print("\n==================================================")
print("5. RELIANCE JUNE 9 GOLDEN CASE")
print("==================================================")
jam_invs = get("/investigations?region=jamnagar")['investigations']
rel = next((i for i in jam_invs if i.get('facility_name') == 'Reliance Refinery' and i.get('acq_date') == '2026-06-09'), None)
if rel:
    print(json.dumps({
        'facility': rel.get('facility_name'),
        'date': rel.get('acq_date'),
        'raw_observations': rel.get('observation_count'),
        'max_frp': rel.get('max_frp_mw'),
        'historical_p90': rel.get('baseline_p90_frp'),
        'historical_active_days': rel.get('baseline_active_days'),
        'prior_active_days': rel.get('previous_active_days'),
        'total_active_days': rel.get('active_days'),
        'behaviour': rel.get('behavior_state'),
        'behaviour_score': rel.get('behavior_score'),
        'priority': rel.get('investigation_priority'),
        'evidence_quality': rel.get('evidence_quality'),
        'persistence': rel.get('persistence_state'),
        'spatial_behaviour': rel.get('spatial_behavior_state'),
        'hist_radius': rel.get('historical_spatial_radius_km'),
        'curr_radius': rel.get('current_spatial_radius_km'),
        'classification_confidence': rel.get('classification_confidence'),
        'source_class': rel.get('source_class'),
        'osm_assoc': rel.get('association_type'),
        'worldcover': rel.get('worldcover_context'),
        'evidence_strength': rel.get('evidence_strength')
    }, indent=2))
else:
    print("Reliance June 9 not found!")

