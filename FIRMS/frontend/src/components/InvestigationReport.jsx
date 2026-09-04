import "./InvestigationReport.css";

function safeNumber(val, decimals = 2) {
  if (val === null || val === undefined || val === "") return "—";
  const num = Number(val);
  return Number.isFinite(num) ? num.toFixed(decimals) : "—";
}

function InvestigationReport({ observation, onClose }) {
  if (!observation) return null;

  const facilityName = observation.facility_name ?? observation.name ?? "Unknown source";
  const date = observation.acq_date ?? observation.date ?? "—";
  const priority = observation.investigation_priority ?? "LOW";
  const behaviorState = observation.behavior_state ?? "—";

  const rawInterpretation = observation.decision_interpretation ?? 
    `${facilityName}: ${observation.source_class?.toLowerCase()?.replace(/_/g, ' ') || 'unknown'} thermal activity shows ${behaviorState?.toLowerCase()} behaviour relative to its historical baseline. Suitable for human investigation.`;
  const interpretation = rawInterpretation.replace(/not evidence of an unregistered industry/gi, "Candidate industrial association");

  const frp = Number(observation.max_frp_mw ?? observation.frp ?? 0);
  const baselineP90 = Number(observation.baseline_p90_frp ?? 0);
  const baselineP95 = Number(observation.baseline_p95_frp ?? 0);
  const frpRatio = baselineP90 > 0 ? (frp / baselineP90) : 0;
  
  const detectionCount = Number(observation.observation_count ?? 1);
  const baselineDetectionP90 = Number(observation.baseline_detection_p90 ?? 0);
  const detectionRatio = baselineDetectionP90 > 0 ? (detectionCount / baselineDetectionP90) : 0;

  const reasons = [];
  if (frpRatio >= 2) reasons.push("Peak FRP is at least 2× the historical P90.");
  else if (frpRatio >= 1.5) reasons.push("Peak FRP is elevated above the historical P90.");
  
  if (detectionRatio >= 2) reasons.push("Daily detection count is substantially above the historical range.");
  else if (detectionRatio >= 1.5) reasons.push("Daily detection count is elevated above the historical range.");
  
  if (observation.association_type === "OSM_FEATURE_INTERSECTION") reasons.push("Thermal observations intersect mapped industrial infrastructure.");
  if (observation.persistence_state === "RECURRING" || observation.persistence_state === "PERSISTENT") reasons.push("Thermal activity has been observed repeatedly at this facility.");
  
  if (observation.spatial_behavior_state === "NORMAL") reasons.push("Spatial behaviour is within the historical spatial pattern.");
  else if (observation.spatial_behavior_state === "UNUSUAL") reasons.push("Current thermal activity is spatially displaced or spatially expanded relative to the facility's historical thermal footprint.");

  return (
    <div className="investigation-report-overlay">
      <div className="investigation-report-modal">
        
        <div className="report-actions no-print">
          <button onClick={() => window.print()} className="print-button">PRINT / SAVE REPORT</button>
          <button onClick={onClose} className="close-report-button">CLOSE</button>
        </div>

        <div className="report-content">
          <h1>EVIDENCE-BACKED INVESTIGATION REPORT</h1>

          <section className="report-section">
            <h2>1. CASE HEADER</h2>
            <div className="report-grid">
              <div><strong>Facility/Source:</strong> {facilityName}</div>
              <div><strong>Date:</strong> {date}</div>
              <div><strong>Priority:</strong> {priority}</div>
              <div><strong>Behaviour State:</strong> {behaviorState}</div>
              <div><strong>Recommendation:</strong> {priority === "HIGH" ? "HUMAN INVESTIGATION RECOMMENDED" : "REVIEW"}</div>
            </div>
          </section>

          <section className="report-section">
            <h2>2. THERMAL OBSERVATION EVIDENCE</h2>
            <div className="report-grid">
              <div><strong>Representative Location:</strong> {safeNumber(observation.latitude, 5)}, {safeNumber(observation.longitude, 5)}</div>
              <div><strong>Acquisition Date/Time:</strong> {date} {observation.acq_time ?? ""}</div>
              <div><strong>Satellite:</strong> {observation.satellite ?? "—"}</div>
              <div><strong>Peak FRP:</strong> {safeNumber(frp)} MW</div>
              <div><strong>Observations (Day):</strong> {detectionCount}</div>
              <div><strong>Daily Observed FRP Sum:</strong> {safeNumber(observation.total_frp_mw)} MW</div>
            </div>
          </section>

          <section className="report-section">
            <h2>3. SOURCE CLASSIFICATION</h2>
            <div className="report-grid">
              <div><strong>Source Class:</strong> {observation.source_class ?? "—"}</div>
              <div><strong>Classification Confidence:</strong> {observation.classification_confidence ?? "—"}</div>
              <div><strong>Evidence Strength:</strong> {observation.evidence_strength ?? "—"}</div>
              <div><strong>Association Type:</strong> {observation.association_type ?? "—"}</div>
              <div><strong>Industrial Context:</strong> {observation.osm_industrial ?? observation.osm_landuse ?? "—"}</div>
              <div><strong>Mapped Facility Name:</strong> {observation.osm_feature_name ?? "—"}</div>
            </div>
          </section>

          <section className="report-section">
            <h2>4. HISTORICAL THERMAL FINGERPRINT</h2>
            <div className="report-grid">
              <div><strong>Historical Median FRP:</strong> {safeNumber(observation.baseline_median_frp ?? observation.baseline_median)} MW</div>
              <div><strong>Historical Mean FRP:</strong> {safeNumber(observation.baseline_mean_frp ?? observation.baseline_mean)} MW</div>
              <div><strong>P90 FRP:</strong> {safeNumber(baselineP90)} MW</div>
              <div><strong>P95 FRP:</strong> {safeNumber(baselineP95)} MW</div>
              <div><strong>Activity Rate:</strong> {observation.activity_rate ? (observation.activity_rate * 100).toFixed(1) + "%" : "—"}</div>
              <div><strong>Historical Active Days:</strong> {observation.baseline_active_days ?? observation.previous_active_days ?? "—"}</div>
              <div><strong>Historical Period:</strong> {observation.baseline_period_days ?? "—"} days</div>
              <div><strong>Persistence State:</strong> {observation.persistence_state ?? "—"}</div>
            </div>
          </section>

          <section className="report-section">
            <h2>5. DEVIATION ANALYSIS</h2>
            
            <div className="deviation-sub">
              <h3>FRP Intensity</h3>
              <div className="report-grid">
                <div><strong>Observed FRP:</strong> {safeNumber(frp)} MW</div>
                <div><strong>Historical P90:</strong> {safeNumber(baselineP90)} MW</div>
                <div><strong>FRP/P90 Ratio:</strong> {safeNumber(frpRatio)}x</div>
                <div><strong>Above P90:</strong> {frp > baselineP90 ? "Yes" : "No"}</div>
                <div><strong>Above P95:</strong> {frp > baselineP95 ? "Yes" : "No"}</div>
              </div>
            </div>

            <div className="deviation-sub">
              <h3>Detection Count</h3>
              <div className="report-grid">
                <div><strong>Observed Count:</strong> {detectionCount}</div>
                <div><strong>Historical P90:</strong> {safeNumber(baselineDetectionP90)}</div>
                <div><strong>Count/P90 Ratio:</strong> {safeNumber(detectionRatio)}x</div>
                <div><strong>Unusually High:</strong> {detectionCount > baselineDetectionP90 && detectionRatio > 1.5 ? "Yes" : "No"}</div>
              </div>
            </div>

            <div className="deviation-sub">
              <h3>Recent Frequency</h3>
              <div className="report-grid">
                <div><strong>Prior Active Days:</strong> {observation.previous_active_days ?? "—"}</div>
              </div>
            </div>
          </section>

          <section className="report-section">
            <h2>6. SPATIAL BEHAVIOUR</h2>
            <div className="report-grid">
              <div><strong>Spatial State:</strong> {observation.spatial_behavior_state ?? "—"}</div>
              <div><strong>Spatial Score:</strong> {safeNumber(observation.spatial_behavior_score, 1)}</div>
              <div><strong>Historical Centroid:</strong> {safeNumber(observation.historical_centroid_lat, 5)}, {safeNumber(observation.historical_centroid_lon, 5)}</div>
              <div><strong>Current Centroid:</strong> {safeNumber(observation.current_centroid_lat, 5)}, {safeNumber(observation.current_centroid_lon, 5)}</div>
              <div><strong>Spatial Displacement (Shift):</strong> {safeNumber(observation.centroid_shift_km)} km</div>
              <div><strong>Historical Activity Radius:</strong> {safeNumber(observation.historical_spatial_radius_km)} km</div>
              <div><strong>Current Activity Radius:</strong> {safeNumber(observation.current_spatial_radius_km)} km</div>
              <div><strong>Spatial Expansion Ratio:</strong> {safeNumber(observation.spatial_expansion_ratio)}x</div>
              <div><strong>Historical Observation Count:</strong> {observation.historical_spatial_observation_count ?? "—"}</div>
            </div>
          </section>

          <section className="report-section">
            <h2>7. EVIDENCE REASONS</h2>
            <ul className="reasons-list">
              {reasons.length > 0 ? reasons.map((r, i) => <li key={i}>{r}</li>) : <li>Insufficient evidence triggers recorded.</li>}
            </ul>
          </section>

          <section className="report-section">
            <h2>8. SYSTEM INTERPRETATION</h2>
            <p className="interpretation-text">{interpretation}</p>
          </section>

          <section className="report-section">
            <h2>9. LIMITATIONS / CAVEATS</h2>
            <ul className="limitations-list">
              <li>FIRMS observations are satellite thermal anomalies, not direct incident confirmation.</li>
              <li>Spatial analysis describes the distribution of FIRMS observations and not an exact fire boundary.</li>
              <li>OSM/infrastructure association is contextual evidence.</li>
              <li>Land-cover context is secondary evidence.</li>
              <li>The system produces investigation candidates for human review; it does not automatically declare an incident.</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

export default InvestigationReport;
