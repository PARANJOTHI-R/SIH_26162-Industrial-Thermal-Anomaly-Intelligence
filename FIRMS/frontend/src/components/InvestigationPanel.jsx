import { useEffect, useMemo, useState } from "react";
import InvestigationReport from "./InvestigationReport";
import "./InvestigationPanel.css";

const API_BASE = "http://localhost:8000";

function toNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function firstNumber(...values) {
  for (const value of values) {
    const number = toNumber(value);
    if (number !== null) return number;
  }

  return null;
}

function InvestigationPanel({
  observation,
  region,
  onClose,
}) {
  const [facilityHistory, setFacilityHistory] =
    useState([]);
  const [historyLoading, setHistoryLoading] =
    useState(false);
  const [showReport, setShowReport] = useState(false);

  // --------------------------------------------------------
  // Fetch facility-day history
  // --------------------------------------------------------

  useEffect(() => {
    if (!observation) {
      setFacilityHistory([]);
      return;
    }

    const facility =
      observation.facility_name ??
      observation.name ??
      "";

    if (
      !facility ||
      String(facility).trim() === "" ||
      String(facility).toLowerCase() ===
        "unknown source"
    ) {
      setFacilityHistory([]);
      return;
    }

    let cancelled = false;

    async function loadHistory() {
      try {
        setHistoryLoading(true);

    const response = await fetch(
          `${API_BASE}/facility-days?region=${encodeURIComponent(region || "jamnagar")}`
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }

        const data = await response.json();

        if (cancelled) return;

        const rows = Array.isArray(data)
          ? data
          : data.data ??
            data.facility_days ??
            [];

        const selectedName =
          String(facility)
            .trim()
            .toLowerCase();

        const filtered = rows
          .filter((row) => {
            const rowName = String(
              row.facility_name ??
                row.name ??
                row.facility ??
                ""
            )
              .trim()
              .toLowerCase();

            return rowName === selectedName;
          })
          .sort((a, b) =>
            String(
              a.acq_date ??
                a.date ??
                ""
            ).localeCompare(
              String(
                b.acq_date ??
                  b.date ??
                  ""
              )
            )
          );

        setFacilityHistory(filtered);
      } catch (error) {
        console.error(
          "Failed to load facility history:",
          error
        );

        if (!cancelled) {
          setFacilityHistory([]);
        }
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [observation]);

  // --------------------------------------------------------
  // Normalize facility history
  // --------------------------------------------------------

  const history = useMemo(() => {
    return facilityHistory
      .map((row) => {
        const date =
          row.acq_date ??
          row.date ??
          row.observation_date ??
          null;

        const frp = firstNumber(
          row.max_frp_mw,
          row.max_frp,
          row.frp
        );

        const count = firstNumber(
          row.observation_count,
          row.detection_count,
          row.count
        );

        return {
          ...row,
          date,
          frp: frp ?? 0,
          count: count ?? 0,
        };
      })
      .filter((row) => row.date);
  }, [facilityHistory]);

  // --------------------------------------------------------
  // Case values
  // --------------------------------------------------------

  const currentFrp = firstNumber(
    observation?.frp,
    observation?.max_frp_mw
  );

  const caseMaxFrp = firstNumber(
    observation?.max_frp_mw,
    observation?.frp
  );

  const observationCount = firstNumber(
    observation?.observation_count
  );

  const previousActiveDays = firstNumber(
    observation?.previous_active_days
  );

  const totalFrp = firstNumber(
    observation?.total_frp_mw
  );

  const behaviorScore = firstNumber(
    observation?.behavior_score
  );

  const priority =
    observation?.investigation_priority ??
    "LOW";

  const behavior =
    observation?.behavior_state ??
    "—";

  const persistence =
    observation?.persistence_state ??
    "—";

  // --------------------------------------------------------
  // IMPORTANT:
  // Baseline can exist on either the selected
  // raw observation OR the investigation case.
  //
  // Never convert missing values to zero.
  // --------------------------------------------------------

  const baselineMean = firstNumber(
    observation?.baseline_mean_frp,
    observation?.baseline_mean,
    observation?.historical_mean_frp
  );

  const baselineP90 = firstNumber(
    observation?.baseline_p90_frp,
    observation?.baseline_p90,
    observation?.historical_p90_frp
  );

  const baselineMedian = firstNumber(
    observation?.baseline_median_frp,
    observation?.baseline_median,
    observation?.historical_median_frp
  );

  const baselineP95 = firstNumber(
    observation?.baseline_p95_frp,
    observation?.baseline_p95,
    observation?.historical_p95_frp
  );

  const baselineStd = firstNumber(
    observation?.baseline_std_frp,
    observation?.baseline_std,
    observation?.historical_std_frp
  );

  const activityFrequency = firstNumber(
    observation?.activity_rate,
    observation?.activity_frequency
  );

  const activeDays = firstNumber(
    observation?.active_days
  );

  const evidenceQuality =
    observation?.evidence_quality ??
    "—";

  // --------------------------------------------------------
  // Classification
  // --------------------------------------------------------

  const sourceClass =
    observation?.source_class_v2 ??
    observation?.source_class ??
    "UNKNOWN";

  const classificationConfidence =
    observation?.classification_confidence_v2 ??
    observation?.classification_confidence ??
    "—";

  const evidenceStrength =
    observation?.evidence_strength ??
    "—";

  // --------------------------------------------------------
  // Spatial behaviour
  // --------------------------------------------------------

  const spatialState = observation?.spatial_behavior_state ?? "—";
  const spatialScore = firstNumber(observation?.spatial_behavior_score);
  
  const currentCentroidLat = firstNumber(observation?.current_centroid_lat);
  const currentCentroidLon = firstNumber(observation?.current_centroid_lon);
  
  const histCentroidLat = firstNumber(observation?.historical_centroid_lat);
  const histCentroidLon = firstNumber(observation?.historical_centroid_lon);
  
  const centroidShift = firstNumber(observation?.centroid_shift_km);
  
  const histRadius = firstNumber(observation?.historical_spatial_radius_km);
  const currentRadius = firstNumber(observation?.current_spatial_radius_km);
  
  const spatialExpansion = firstNumber(observation?.spatial_expansion_ratio);

  // --------------------------------------------------------
  // Deviation analysis
  // --------------------------------------------------------

  const frpDeviationRatio =
    currentFrp !== null &&
    baselineP90 !== null &&
    baselineP90 > 0
      ? currentFrp / baselineP90
      : null;

  const detectionBaseline = useMemo(() => {
    const counts = history
      .filter(
        (row) =>
          row.date !==
          observation?.acq_date
      )
      .map((row) => row.count)
      .filter(
        (count) =>
          Number.isFinite(count) &&
          count > 0
      );

    if (!counts.length) return null;

    const sorted = [...counts].sort(
      (a, b) => a - b
    );

    const mean =
      counts.reduce(
        (sum, value) =>
          sum + value,
        0
      ) / counts.length;

    const index =
      Math.min(
        sorted.length - 1,
        Math.floor(
          sorted.length * 0.9
        )
      );

    return {
      mean,
      p90: sorted[index],
    };
  }, [history, observation]);

  const detectionDeviation =
    observationCount !== null &&
    detectionBaseline &&
    detectionBaseline.p90 > 0
      ? observationCount /
        detectionBaseline.p90
      : null;

  // --------------------------------------------------------
  // Deviation labels
  // --------------------------------------------------------

  const frpDeviationLabel =
    frpDeviationRatio === null
      ? "INSUFFICIENT DATA"
      : frpDeviationRatio >= 2
      ? "HIGH"
      : frpDeviationRatio > 1
      ? "ELEVATED"
      : "NORMAL";

  const detectionDeviationLabel =
    detectionDeviation === null
      ? "INSUFFICIENT DATA"
      : detectionDeviation >= 2
      ? "HIGH"
      : detectionDeviation > 1
      ? "ELEVATED"
      : "NORMAL";

  // --------------------------------------------------------
  // Evidence / reason codes
  // --------------------------------------------------------

  const reasonCodes = [];

  if (
    frpDeviationRatio !== null &&
    frpDeviationRatio >= 2
  ) {
    reasonCodes.push({
      type: "deviation",
      label: "FRP SPIKE",
      detail:
        "Peak thermal intensity is at least 2× the historical P90.",
    });
  } else if (
    frpDeviationRatio !== null &&
    frpDeviationRatio > 1
  ) {
    reasonCodes.push({
      type: "deviation",
      label: "FRP ABOVE BASELINE",
      detail:
        "Peak thermal intensity exceeds the historical P90.",
    });
  }

  if (
    detectionDeviation !== null &&
    detectionDeviation >= 2
  ) {
    reasonCodes.push({
      type: "deviation",
      label: "DETECTION COUNT SPIKE",
      detail:
        "Daily detection count is substantially above the historical range.",
    });
  } else if (
    detectionDeviation !== null &&
    detectionDeviation > 1
  ) {
    reasonCodes.push({
      type: "deviation",
      label: "DETECTION COUNT ELEVATED",
      detail:
        "Daily detection count exceeds the historical range.",
    });
  }

  if (
    observation?.association_type ===
    "OSM_FEATURE_INTERSECTION"
  ) {
    reasonCodes.push({
      type: "context",
      label: "FACILITY ASSOCIATION",
      detail:
        "Thermal point intersects mapped industrial infrastructure.",
    });
  } else if (
    observation?.association_type ===
    "NEARBY_OSM_INDUSTRIAL_FEATURE"
  ) {
    reasonCodes.push({
      type: "context",
      label: "NEARBY INDUSTRIAL CONTEXT",
      detail:
        "Thermal point is near mapped industrial infrastructure.",
    });
  }

  if (persistence === "RECURRING") {
    reasonCodes.push({
      type: "context",
      label: "RECURRING SOURCE",
      detail:
        "Thermal activity has been observed repeatedly at this source.",
    });
  }

  // --------------------------------------------------------
  // Generic evidence text
  // --------------------------------------------------------

  const evidence = [];

  if (
    observation?.association_type &&
    observation.association_type !== "—"
  ) {
    evidence.push(
      observation.association_type
    );
  }

  if (
    observation?.classification_reason &&
    observation.classification_reason !==
      "—"
  ) {
    evidence.push(
      observation.classification_reason
    );
  }

  if (
    observation?.evidence_summary &&
    observation.evidence_summary !== "—"
  ) {
    evidence.push(
      observation.evidence_summary
    );
  }

  // --------------------------------------------------------
  // Chart
  // --------------------------------------------------------

  const chartMax = useMemo(() => {
    const values = history
      .map((item) => item.frp)
      .filter((value) =>
        Number.isFinite(value)
      );

    if (caseMaxFrp !== null) {
      values.push(caseMaxFrp);
    }

    if (baselineP90 !== null) {
      values.push(baselineP90);
    }

    return Math.max(
      ...values,
      1
    );
  }, [
    history,
    caseMaxFrp,
    baselineP90,
  ]);

  const chartData = useMemo(() => {
    return history.map(
      (item, index) => ({
        ...item,

        height: Math.max(
          4,
          (item.frp / chartMax) *
            100
        ),

        isSelected:
          item.date ===
          (observation?.acq_date ?? observation?.date),

        key: `${item.date}-${index}`,
      })
    );
  }, [
    history,
    chartMax,
    observation,
  ]);

  // --------------------------------------------------------
  // No selection
  // --------------------------------------------------------

  if (!observation) {
    return null;
  }

  // --------------------------------------------------------
  // Render
  // --------------------------------------------------------

  return (
    <aside className="investigation-panel">

      {/* HEADER */}
      <div className="investigation-panel-header">
        <div>
          <div className="investigation-eyebrow">
            {(priority === "HIGH" || observation?.is_investigation_candidate)
              ? "INVESTIGATION CANDIDATE"
              : "THERMAL OBSERVATION"}
          </div>

          <h3>
            {observation.facility_name ??
              observation.name ??
              "Unknown source"}
          </h3>
        </div>

        <button
          className="investigation-close"
          onClick={onClose}
          aria-label="Close investigation panel"
        >
          ×
        </button>
      </div>

      {/* PRIORITY */}
      <div
        className={`investigation-priority priority-${String(
          priority
        ).toLowerCase()}`}
      >
        {priority}
        {priority === "HIGH"
          ? " — INVESTIGATE"
          : priority === "MEDIUM"
          ? " — REVIEW"
          : ""}
      </div>

      {/* REPORT BUTTON */}
      <div className="investigation-action" style={{ padding: "16px 20px 0" }}>
        <button 
          onClick={() => setShowReport(true)}
          style={{ width: "100%", padding: "12px", background: "#f04e23", color: "white", border: "none", borderRadius: "4px", fontWeight: "bold", cursor: "pointer" }}
        >
          VIEW INVESTIGATION REPORT
        </button>
      </div>

      {/* CURRENT EVENT */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          CURRENT EVENT
        </div>

        <div className="investigation-grid">

          <Metric
            label="FRP"
            value={
              currentFrp !== null
                ? `${currentFrp.toFixed(
                    2
                  )} MW`
                : "—"
            }
            highlight={
              frpDeviationLabel ===
              "HIGH"
            }
          />

          <Metric
            label="DATE"
            value={
              observation.acq_date ??
              "—"
            }
          />

          <Metric
            label="TIME"
            value={
              observation.acq_time ??
              "—"
            }
          />

          <Metric
            label="SATELLITE"
            value={
              observation.satellite ??
              "Not available at event level"
            }
          />

          <Metric
            label="OBSERVATIONS"
            value={
              observationCount !== null
                ? observationCount
                : "—"
            }
          />

          <Metric
            label="SUM OF OBSERVED FRP VALUES"
            value={
              totalFrp !== null
                ? `${totalFrp.toFixed(
                    2
                  )} MW`
                : "—"
            }
          />

        </div>
      </div>

      {/* SOURCE CLASSIFICATION */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          SOURCE CLASSIFICATION
        </div>

        <div className="classification-main">
          {sourceClass === "INDUSTRIAL_ASSOCIATED" ? "Industrial-associated" 
           : sourceClass === "AGRICULTURAL" ? "Agricultural / Biomass"
           : sourceClass === "FOREST_NATURAL" ? "Forest / Natural"
           : sourceClass === "OTHER" ? "Other"
           : "Unknown / Unmatched"}
        </div>
        
        {sourceClass === "INDUSTRIAL_ASSOCIATED" && (
          <div style={{ fontSize: '9px', color: '#94a3b8', marginBottom: '8px', fontStyle: 'italic' }}>
            * Industrial-associated based on contextual evidence, not a confirmed industrial fire.
          </div>
        )}

        <div className="classification-meta">
          Confidence:{" "}
          {classificationConfidence}
        </div>

        <div className="classification-meta">
          Contextual Evidence Strength:{" "}
          {evidenceStrength}
        </div>

        {observation.worldcover_context && (
          <div className="classification-meta">
            Land-cover context:{" "}
            {observation.worldcover_context} (Secondary evidence; OSM industrial association takes precedence)
          </div>
        )}
      </div>

      {/* EVIDENCE QUALITY */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          EVIDENCE QUALITY
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "8px",
          }}
        >
          <div
            style={{
              fontWeight: "bold",
              fontSize: "14px",
              color:
                evidenceQuality === "HIGH"
                  ? "#4ade80"
                  : evidenceQuality === "MEDIUM"
                  ? "#fbbf24"
                  : evidenceQuality === "LOW"
                  ? "#f87171"
                  : "#64748b",
            }}
          >
            {evidenceQuality}
          </div>
          <div style={{ fontSize: "10px", color: "#94a3b8" }}>
            {evidenceQuality === "HIGH"
              ? "Multiple strong evidence sources support this assessment."
              : evidenceQuality === "MEDIUM"
              ? "Moderate evidence available. Assessment is reasonably reliable."
              : evidenceQuality === "LOW"
              ? "Limited evidence. Assessment may be incomplete."
              : "Insufficient evidence for a reliable assessment."}
          </div>
        </div>

        <div
          style={{
            fontSize: "9px",
            color: "#475569",
            fontStyle: "italic",
          }}
        >
          Evidence quality is separate from behaviour score and investigation priority.
          It reflects the volume and quality of supporting data, not the severity of the event.
        </div>
      </div>

      {/* FACILITY THERMAL FINGERPRINT */}
      <div className="investigation-section fingerprint-section">
        <div className="investigation-section-title">
          FACILITY THERMAL FINGERPRINT
        </div>

        <div className="fingerprint-grid">

          <FingerprintMetric
            label="TYPICAL FRP"
            value={
              baselineMedian !== null
                ? `${baselineMedian.toFixed(
                    2
                  )} MW`
                : baselineMean !== null
                ? `${baselineMean.toFixed(
                    2
                  )} MW`
                : "—"
            }
            detail="Historical median"
          />

          <FingerprintMetric
            label="BASELINE MEAN"
            value={
              baselineMean !== null
                ? `${baselineMean.toFixed(
                    2
                  )} MW`
                : "—"
            }
            detail="Historical mean"
          />

          <FingerprintMetric
            label="P90 FRP"
            value={
              baselineP90 !== null
                ? `${baselineP90.toFixed(
                    2
                  )} MW`
                : "—"
            }
            detail="90th percentile"
          />

          <FingerprintMetric
            label="P95 FRP"
            value={
              baselineP95 !== null
                ? `${baselineP95.toFixed(
                    2
                  )} MW`
                : "—"
            }
            detail="95th percentile"
          />

          <FingerprintMetric
            label="ACTIVITY RATE"
            value={
              activityFrequency !== null
                ? `${(
                    activityFrequency *
                    100
                  ).toFixed(1)}%`
                : "Not available"
            }
            detail={
              activeDays !== null
                ? `${activeDays} active days`
                : "Historical activity"
            }
          />

          <FingerprintMetric
            label="PERSISTENCE"
            value={persistence}
            detail="Historical pattern"
          />

        </div>

        <div className="fingerprint-confidence">
          <span>BASELINE CONFIDENCE — </span>
          <strong>
            {previousActiveDays === null
              ? "UNKNOWN"
              : previousActiveDays >= 30
              ? "HIGH"
              : previousActiveDays >= 10
              ? "MEDIUM"
              : "LOW"}
          </strong>
        </div>

        {activeDays !== null && (
          <div style={{ fontSize: "9px", color: "#64748b", marginTop: "6px" }}>
            Total historical active days: {activeDays}
            {previousActiveDays !== null && previousActiveDays !== activeDays && (
              <> &nbsp;·&nbsp; Active days before this event: {previousActiveDays}</>
            )}
          </div>
        )}
      </div>

      {/* DEVIATION ANALYSIS */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          WHY THIS CASE IS UNUSUAL
        </div>

        <ul className="deviation-reasons">
          {frpDeviationRatio >= 2 && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> FRP significantly above historical P90
            </li>
          )}
          {frpDeviationRatio >= 1.5 && frpDeviationRatio < 2 && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> FRP elevated above historical P90
            </li>
          )}
          {detectionDeviation >= 2 && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> Detection count significantly above historical behaviour
            </li>
          )}
          {observation.association_type === "OSM_FEATURE_INTERSECTION" && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> Industrial facility association
            </li>
          )}
          {(observation.persistence_state === "RECURRING" || observation.persistence_state === "PERSISTENT") && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> Recurring facility activity
            </li>
          )}
          {observation.spatial_behavior_state === "UNUSUAL" && (
            <li className="reason-abnormal">
              <span className="reason-icon">✓</span> Spatial footprint expanded or shifted
            </li>
          )}

          {/* Normal dimensions */}
          {frpDeviationRatio < 1.5 && frpDeviationRatio > 0 && (
            <li className="reason-normal">
              <span className="reason-icon">○</span> FRP intensity: normal
            </li>
          )}
          {detectionDeviation < 1.5 && detectionDeviation > 0 && (
            <li className="reason-normal">
              <span className="reason-icon">○</span> Detection count: normal
            </li>
          )}
          {observation.spatial_behavior_state === "NORMAL" && (
            <li className="reason-normal">
              <span className="reason-icon">○</span> Spatial behaviour: normal
            </li>
          )}
        </ul>
      </div>

      <div className="investigation-section">
        <div className="investigation-section-title">
          DEVIATION METRICS
        </div>

        <div className="investigation-grid" style={{ marginBottom: "12px" }}>
          <Metric
            label="OBSERVED FRP"
            value={currentFrp !== null ? `${currentFrp.toFixed(2)} MW` : "—"}
            highlight={frpDeviationLabel === "HIGH"}
          />
          <Metric
            label="HISTORICAL P90"
            value={baselineP90 !== null ? `${baselineP90.toFixed(2)} MW` : "—"}
          />
          <Metric
            label="HISTORICAL P95"
            value={baselineP95 !== null ? `${baselineP95.toFixed(2)} MW` : "—"}
          />
          <Metric
            label="OBSERVED / P90"
            value={frpDeviationRatio !== null ? `${frpDeviationRatio.toFixed(1)}x` : "—"}
            highlight={frpDeviationLabel === "HIGH"}
          />
        </div>

        <div className="investigation-grid">
          <Metric
            label="OBSERVED DETECTIONS"
            value={observationCount !== null ? observationCount : "—"}
            highlight={detectionDeviationLabel === "HIGH"}
          />
          {detectionBaseline && detectionBaseline.p90 > 0 && (
            <Metric
              label="HISTORICAL P90 DETECTIONS"
              value={detectionBaseline.p90.toFixed(1)}
            />
          )}
          <Metric
            label="CURRENT BEHAVIOUR"
            value={behavior}
            highlight={behavior === "UNUSUAL"}
          />
          <Metric
            label="HISTORICAL BEHAVIOUR"
            value={observation.historical_behavior_state ?? "NORMAL"}
          />
        </div>

        <div className="behavior-score-block">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="behavior-score-label">
              BEHAVIOUR SCORE
            </div>

            <div className="behavior-score-description">
              Explainable deviation from the facility's historical pattern.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
            <div
              className={`behavior-score-value ${
                behaviorScore !== null && behaviorScore >= 70
                  ? "score-high"
                  : behaviorScore !== null && behaviorScore >= 40
                  ? "score-medium"
                  : ""
              }`}
            >
              {behaviorScore !== null ? behaviorScore.toFixed(1) : "—"}
            </div>
            
            <div style={{ fontSize: '10px', fontWeight: 'bold', color: behavior === 'UNUSUAL' ? '#f87171' : '#94a3b8' }}>
              {behavior}
            </div>
            
            <div style={{ fontSize: '9px', fontWeight: 'bold', color: priority === 'HIGH' ? '#fecaca' : priority === 'MEDIUM' ? '#fed7aa' : '#cbd5e1' }}>
              {priority} PRIORITY
            </div>
          </div>
        </div>
      </div>

      {/* HISTORICAL BEHAVIOUR */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          HISTORICAL BEHAVIOUR
        </div>

        <div className="behaviour-grid">

          <Metric
            label="BEHAVIOUR"
            value={behavior}
            highlight={
              behavior === "UNUSUAL"
            }
          />

          <Metric
            label="SOURCE PERSISTENCE"
            value={persistence}
          />

          <Metric
            label="PRIOR ACTIVE DAYS"
            value={
              previousActiveDays !==
              null
                ? `${previousActiveDays} (before this event)`
                : "—"
            }
          />

          <Metric
            label="ACTIVITY RATE"
            value={
              activityFrequency !==
              null
                ? `${(
                    activityFrequency *
                    100
                  ).toFixed(1)}%`
                : "Not available"
            }
          />

        </div>
      </div>

      {/* SPATIAL BEHAVIOUR */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          SPATIAL BEHAVIOUR
        </div>
        <div style={{ fontSize: '9px', color: '#94a3b8', marginBottom: '12px', fontStyle: 'italic' }}>
          * FIRMS coordinates represent satellite thermal observations and are not exact fire boundaries.
        </div>

        {/* Plain-language spatial summary */}
        <div
          style={{
            padding: "10px 12px",
            background: "rgba(100,116,139,0.08)",
            border: "1px solid rgba(100,116,139,0.2)",
            borderRadius: "6px",
            marginBottom: "14px",
            fontSize: "11px",
            color: "#cbd5e1",
            lineHeight: "1.5",
          }}
        >
          {spatialState === "NORMAL"
            ? "Current thermal footprint remains within the historical facility activity envelope."
            : spatialState === "WATCH"
            ? "Current thermal footprint shows a minor deviation from the historical facility activity envelope."
            : spatialState === "UNUSUAL"
            ? "Current thermal footprint has expanded or shifted significantly beyond the historical facility activity envelope."
            : spatialState === "INSUFFICIENT_HISTORY"
            ? "Insufficient historical data to assess spatial behaviour for this source."
            : "Spatial behaviour data not available for this source."}
        </div>

        <div className="investigation-grid">
          <Metric
            label="SPATIAL STATE"
            value={spatialState}
            highlight={spatialState === 'UNUSUAL'}
          />
          <Metric
            label="HISTORICAL RADIUS"
            value={histRadius !== null ? `${histRadius.toFixed(2)} km` : "—"}
          />
          <Metric
            label="CURRENT RADIUS"
            value={currentRadius !== null ? `${currentRadius.toFixed(2)} km` : "—"}
          />
          <Metric
            label="EXPANSION RATIO"
            value={spatialExpansion !== null ? `${spatialExpansion.toFixed(1)}×` : "—"}
            highlight={spatialExpansion !== null && spatialExpansion >= 2}
          />
        </div>

        {/* Advanced metrics — centroid shift and score */}
        {centroidShift !== null && (
          <details style={{ marginTop: "8px" }}>
            <summary style={{ fontSize: "10px", color: "#64748b", cursor: "pointer" }}>
              Advanced spatial metrics
            </summary>
            <div className="investigation-grid" style={{ marginTop: "8px" }}>
              <Metric
                label="CENTROID SHIFT"
                value={`${centroidShift.toFixed(2)} km`}
              />
              <Metric
                label="SPATIAL SCORE"
                value={spatialScore !== null ? spatialScore.toFixed(1) : "—"}
              />
            </div>
          </details>
        )}
      </div>

      {/* HISTORY CHART */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          FACILITY THERMAL HISTORY
        </div>

        {historyLoading ? (
          <div className="history-loading">
            Loading historical behaviour...
          </div>
        ) : history.length === 0 ? (
          <div className="history-empty">
            No prior activity recorded for this source.
          </div>
        ) : (
          <>
            <div className="history-chart">

              {chartData.map(
                (item) => (
                  <div
                    className="history-column"
                    key={item.key}
                    title={`${item.date}: ${item.frp.toFixed(
                      2
                    )} MW • ${
                      item.count
                    } observations`}
                  >
                    <div className="history-bar-area">
                      <div
                        className={`history-bar ${
                          item.isSelected
                            ? "history-bar-selected"
                            : ""
                        }`}
                        style={{
                          height: `${item.height}%`,
                        }}
                      />
                    </div>

                    <div className="history-date">
                      {formatShortDate(
                        item.date
                      )}
                    </div>
                  </div>
                )
              )}

            </div>

            <div className="history-legend">
              <span>
                <i className="history-marker-normal" />
                Historical activity
              </span>

              <span>
                <i className="history-marker-selected" />
                Selected case
              </span>
            </div>
          </>
        )}
      </div>

      {/* WHY THIS CASE */}
      <div className="investigation-section">
        <div className="investigation-section-title">
          WHY THIS CASE?
        </div>

        {reasonCodes.length > 0 ? (
          <div className="reason-code-list">
            {reasonCodes.map(
              (reason, index) => (
                <div
                  className={`reason-code reason-${reason.type}`}
                  key={`${reason.label}-${index}`}
                >
                  <div className="reason-code-title">
                    <span>
                      {reason.type ===
                      "deviation"
                        ? "▲"
                        : "●"}
                    </span>

                    {reason.label}
                  </div>

                  <div className="reason-code-detail">
                    {reason.detail}
                  </div>
                </div>
              )
            )}
          </div>
        ) : evidence.length > 0 ? (
          <ul className="evidence-list">
            {evidence
              .slice(0, 4)
              .map((item, index) => (
                <li key={index}>
                  {item}
                </li>
              ))}
          </ul>
        ) : (
          <div className="history-empty">
            No additional evidence available.
          </div>
        )}
      </div>

      {/* RAW EVIDENCE */}
      {evidence.length > 0 && (
        <div className="investigation-section">
          <div className="investigation-section-title">
            CONTEXTUAL EVIDENCE
          </div>

          <ul className="evidence-list">
            {evidence
              .slice(0, 3)
              .map((item, index) => (
                <li key={index}>
                  {item}
                </li>
              ))}
          </ul>
        </div>
      )}

      {/* INTERPRETATION */}
      <div className="investigation-interpretation">
        <div className="interpretation-title">
          SYSTEM INTERPRETATION
        </div>

        <p>
          {(() => {
            const raw = observation.interpretation && observation.interpretation !== "—"
              ? observation.interpretation
              : observation.decision_interpretation && observation.decision_interpretation !== "—"
              ? observation.decision_interpretation
              : priority === "HIGH"
              ? "Abnormal thermal behaviour relative to the available historical baseline. Suitable for human investigation."
              : "Thermal activity associated with the selected source. Review historical behaviour and contextual evidence.";
            
            const isUnknownSource = 
              !observation.facility_name || 
              String(observation.facility_name).toUpperCase().includes("UNKNOWN") || 
              String(observation.facility_name).toUpperCase().includes("UNMAPPED");
            
            if (isUnknownSource) {
              const persist = observation.persistence_state === 'RECURRING' || observation.persistence_state === 'PERSISTENT' ? 'Recurring ' : '';
              const behav = observation.behavior_state?.toLowerCase() ?? 'unusual';
              return `${persist}unmatched thermal activity shows ${behav} behaviour relative to its historical baseline. Suitable for human verification.`;
            }
            
            return raw.replace(/not evidence of an unregistered industry/gi, "Candidate industrial association");
          })()}
        </p>
      </div>

      {/* COORDINATES */}
      <div className="investigation-coordinates">
        {toNumber(
          observation.latitude
        ) !== null
          ? toNumber(
              observation.latitude
            ).toFixed(5)
          : "—"}

        {" , "}

        {toNumber(
          observation.longitude
        ) !== null
          ? toNumber(
              observation.longitude
            ).toFixed(5)
          : "—"}
      </div>

      {showReport && (
        <InvestigationReport 
          observation={observation} 
          onClose={() => setShowReport(false)} 
        />
      )}
    </aside>
  );
}

// ----------------------------------------------------------
// Metric
// ----------------------------------------------------------

function Metric({
  label,
  value,
  highlight = false,
}) {
  return (
    <div className="metric">
      <div className="metric-label">
        {label}
      </div>

      <div
        className={`metric-value ${
          highlight
            ? "metric-highlight"
            : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

// ----------------------------------------------------------
// Fingerprint metric
// ----------------------------------------------------------

function FingerprintMetric({
  label,
  value,
  detail,
}) {
  return (
    <div className="fingerprint-metric">
      <div className="fingerprint-label">
        {label}
      </div>

      <div className="fingerprint-value">
        {value}
      </div>

      <div className="fingerprint-detail">
        {detail}
      </div>
    </div>
  );
}

// ----------------------------------------------------------
// Deviation row
// ----------------------------------------------------------

function DeviationRow({
  label,
  value,
  detail,
  emphasis = false,
}) {
  return (
    <div className="deviation-row">
      <div className="deviation-main">
        <div className="deviation-label">
          {label}
        </div>

        <div
          className={`deviation-value ${
            emphasis
              ? "deviation-high"
              : value ===
                "ELEVATED"
              ? "deviation-elevated"
              : ""
          }`}
        >
          {value}
        </div>
      </div>

      <div className="deviation-detail">
        {detail}
      </div>
    </div>
  );
}

// ----------------------------------------------------------
// Date formatting
// ----------------------------------------------------------

function formatShortDate(date) {
  if (!date) return "—";

  const parsed =
    new Date(`${date}T00:00:00`);

  if (
    Number.isNaN(
      parsed.getTime()
    )
  ) {
    return String(date).slice(5);
  }

  return parsed.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
    }
  );
}

export default InvestigationPanel;