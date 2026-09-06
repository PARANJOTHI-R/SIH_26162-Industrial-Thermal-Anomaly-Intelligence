import urllib.request
import json

base = 'http://127.0.0.1:18765'

def get(endpoint):
    req = urllib.request.Request(f"{base}{endpoint}")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

print("\n--- GOLDEN NEGATIVE TEST ---")
thoo_invs = get("/investigations?region=thoothukudi")['investigations']
unknowns = [i for i in thoo_invs if i.get('is_investigation_candidate') and i.get('source_class') == 'UNKNOWN']
# Pick the first one (e.g. 2026-04-11)
g_neg = unknowns[0] if unknowns else None
if g_neg:
    print("Facility:", g_neg.get('facility_name'))
    print("Date:", g_neg.get('acq_date'))
    print("Association:", g_neg.get('association_type'))
    print("Depth (active_days):", g_neg.get('active_days'))
    print("Baseline Available:", g_neg.get('baseline_available'))
    print("Evidence Strength:", g_neg.get('evidence_strength'))
    print("Persistence:", g_neg.get('persistence_state'))
    print("NEW Evidence Quality:", g_neg.get('evidence_quality'))
else:
    print("Could not find Thoothukudi UNKNOWN candidate.")

print("\n--- GOLDEN POSITIVE TEST ---")
jam_invs = get("/investigations?region=jamnagar")['investigations']
rel = next((i for i in jam_invs if i.get('facility_name') == 'Reliance Refinery' and i.get('acq_date') == '2026-06-09'), None)
if rel:
    print("Facility:", rel.get('facility_name'))
    print("Source Class:", rel.get('source_class'))
    print("Behaviour:", rel.get('behavior_state'))
    print("Score:", rel.get('behavior_score'))
    print("Priority:", rel.get('investigation_priority'))
    print("Historical P90:", rel.get('baseline_p90_frp'))
    print("FRP vs P90 Ratio:", rel.get('frp_vs_p90_ratio'))
    print("Persistence:", rel.get('persistence_state'))
    print("Baseline Available:", rel.get('baseline_available'))
    print("Association:", rel.get('association_type'))
    print("NEW Evidence Quality:", rel.get('evidence_quality'))
else:
    print("Reliance June 9 not found.")

print("\n--- RECHECK REGION COUNTS ---")
sum_jam = get("/summary?region=jamnagar")
sum_thoo = get("/summary?region=thoothukudi")

def fmt_sum(r, s):
    unks = get(f"/unknown-sources?region={r}")['sources'] if get(f"/unknown-sources?region={r}") else []
    unmatched_evts = sum(u.get('event_count', 0) for u in unks)
    persistent = sum(1 for u in unks if u.get('persistence_class') in ('PERSISTENT', 'RECURRING') and u.get('event_count', 0) >= 3)
    return f"{r.capitalize()} | {s.get('raw_observations')} | {s.get('thermal_events')} | {s.get('facility_days')} | {s.get('facilities')} | {s.get('investigation_candidates')} | {unmatched_evts} | {persistent}"

print("REGION | RAW OBS | EVENTS | FACILITY DAYS | FACILITIES | INVESTIGATION CANDIDATES | UNMATCHED EVENTS | PERSISTENT UNKNOWN SOURCES")
print(fmt_sum("jamnagar", sum_jam))
print(fmt_sum("thoothukudi", sum_thoo))

print("\n--- RECHECK EVIDENCE QUALITY DISTRIBUTION ---")
def count_eq(r):
    invs = get(f"/investigations?region={r}")['investigations']
    cands = [i for i in invs if i.get('is_investigation_candidate')]
    counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INSUFFICIENT': 0}
    for c in cands:
        eq = c.get('evidence_quality', 'UNKNOWN')
        if eq in counts:
            counts[eq] += 1
    return f"{r.capitalize()} | {counts['HIGH']} | {counts['MEDIUM']} | {counts['LOW']} | {counts['INSUFFICIENT']}"

print("REGION | HIGH | MEDIUM | LOW | INSUFFICIENT")
print(count_eq("jamnagar"))
print(count_eq("thoothukudi"))

print("\n--- RECHECK QUEUE ---")
for c in unknowns:
    print(f"{c.get('facility_name')} | {c.get('acq_date')} | {c.get('source_class')} | {c.get('behavior_state')} | Score: {c.get('behavior_score')} | Priority: {c.get('investigation_priority')} | Old EQ: HIGH -> New EQ: {c.get('evidence_quality')}")

