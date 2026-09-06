import "./SummaryCards.css";

function SummaryCards({ summary }) {
  if (!summary) {
    return (
      <div className="summary-loading">Loading intelligence...</div>
    );
  }

  return (
    <div className="summary-grid">

      {/* Raw FIRMS observations */}
      <div className="summary-card">
        <div className="summary-label">RAW FIRMS OBS</div>
        <div className="summary-value">
          {summary.raw_observations ?? summary.thermal_observations ?? 0}
        </div>
        <div className="summary-sub">satellite detections</div>
      </div>

      {/* Thermal events (clustered/deduped) */}
      <div className="summary-card">
        <div className="summary-label">THERMAL EVENTS</div>
        <div className="summary-value">
          {summary.thermal_events ?? 0}
        </div>
        <div className="summary-sub">after clustering</div>
      </div>

      {/* Facility-days */}
      <div className="summary-card">
        <div className="summary-label">FACILITY DAYS</div>
        <div className="summary-value">
          {summary.facility_days ?? 0}
        </div>
        <div className="summary-sub">facility × date records</div>
      </div>

      {/* Facilities */}
      <div className="summary-card">
        <div className="summary-label">FACILITIES</div>
        <div className="summary-value">
          {summary.facilities ?? 0}
        </div>
        <div className="summary-sub">with baselines</div>
      </div>

      {/* Investigation candidates */}
      <div className="summary-card priority-card">
        <div className="summary-label">INVESTIGATION CANDIDATES</div>
        <div className="summary-value">
          {summary.investigation_candidates ?? 0}
        </div>
        <div className="summary-sub">for human review</div>
      </div>

      {/* Unmatched sources */}
      {(summary.unmatched_sources ?? 0) > 0 && (
        <div className="summary-card">
          <div className="summary-label">UNMATCHED SOURCES</div>
          <div className="summary-value">
            {summary.unmatched_sources}
          </div>
          <div className="summary-sub">no facility association</div>
        </div>
      )}

    </div>
  );
}

export default SummaryCards;