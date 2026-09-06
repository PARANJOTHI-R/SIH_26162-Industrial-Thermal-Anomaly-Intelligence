import { useEffect, useState } from "react";

import {
  getSummary,
  getThermalObservations,
  getThermalEvents,
  getInvestigations,
  getRegions,
  getUnknownSources,
} from "./services/api";

import SummaryCards from "./components/SummaryCards";
import MapView from "./components/MapView";
import InvestigationPanel from "./components/InvestigationPanel";

import "./index.css";
import InvestigationQueue from "./components/InvestigationQueue";

function App() {
  const [summary, setSummary] = useState(null);
  const [observations, setObservations] = useState([]);
  const [globalEvents, setGlobalEvents] = useState([]);
  const [selectedObservation, setSelectedObservation] = useState(null);
  const [error, setError] = useState(null);
  const [investigations, setInvestigations] = useState([]);
  const [unknownSources, setUnknownSources] = useState([]);

  // Region
  const [region, setRegion] = useState("jamnagar");
  const [regions, setRegions] = useState([]);

  // Filters
  const [filterSourceClass, setFilterSourceClass] = useState("ALL");
  const [filterPriority, setFilterPriority] = useState("ALL");
  const [filterDate, setFilterDate] = useState("ALL");

  useEffect(() => {
    async function initGlobal() {
      try {
        const [regionsData, globalData] = await Promise.all([
          getRegions(),
          getThermalEvents("ALL"),
        ]);
        setRegions(regionsData.regions || []);
        
        let evts = [];
        if (Array.isArray(globalData)) evts = globalData;
        else if (Array.isArray(globalData?.events)) evts = globalData.events;
        setGlobalEvents(evts);
      } catch (err) {
        console.error("Failed to fetch global data:", err);
      }
    }
    initGlobal();
  }, []);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryData, observationData, investigationsData, unknownData] =
          await Promise.all([
            getSummary(region),
            getThermalObservations(region),
            getInvestigations(region, "ALL"),
            getUnknownSources(region),
          ]);

        console.log("Summary received:", summaryData);
        console.log("Thermal observations response:", observationData);

        setSummary(summaryData);
        setUnknownSources(unknownData?.sources ?? []);

        if (Array.isArray(observationData)) {
          setObservations(observationData);
        } else if (Array.isArray(observationData?.records)) {
          setObservations(observationData.records);
        } else if (Array.isArray(observationData?.observations)) {
          setObservations(observationData.observations);
        } else {
          console.warn(
            "No valid thermal observation records found:",
            observationData
          );
          setObservations([]);
        }

        console.log("Investigations received:", investigationsData);

        setInvestigations(
          Array.isArray(investigationsData)
            ? investigationsData
            : investigationsData?.investigations || []
        );
      } catch (err) {
        console.error("Dashboard loading error:", err);
        setError(err.message);
        setObservations([]);
      }
    }

    loadDashboard();
  }, [region]);

  const handleRegionChange = (newRegion) => {
    if (newRegion !== region) {
      if (selectedObservation && selectedObservation.region && selectedObservation.region !== newRegion) {
        setSelectedObservation(null);
      }
      setRegion(newRegion);
    }
  };

  const handleInvestigationSelect = (investigation) => {
    if (!investigation) return;

    const facilityName = String(
      investigation.facility_name ?? investigation.name ?? ""
    )
      .trim()
      .toLowerCase();

    const date = String(investigation.acq_date ?? "").trim();

    // Find all raw FIRMS observations belonging to this facility-day case from global events.
    // Find the matching raw observation from global events.
    let representativeObservation = null;

    if (investigation.event_id) {
       representativeObservation = globalEvents.find(e => e.event_id === investigation.event_id);
    }

    if (!representativeObservation) {
      const matchingObservations = globalEvents.filter((observation) => {
        const observationFacility = String(
          observation.name ?? observation.facility_name ?? ""
        )
          .trim()
          .toLowerCase();
  
        const observationDate = String(observation.event_date ?? observation.acq_date ?? "").trim();
  
        return (
          observationFacility === facilityName && observationDate === date
        );
      });
  
      representativeObservation = matchingObservations.length > 0 ? matchingObservations.reduce((prev, current) => {
        const prevFrp = Number(prev.max_frp ?? prev.frp ?? 0);
        const currFrp = Number(current.max_frp ?? current.frp ?? 0);
        return prevFrp > currFrp ? prev : current;
      }) : null;
    }
    
    // If no exact match is found (e.g. queue contains an investigation with no matching map point),
    // we can fallback to using the investigation record itself if it has coordinates.
    if (!representativeObservation && investigation.latitude && investigation.longitude) {
       representativeObservation = { ...investigation, event_id: investigation.id || String(Math.random()) };
    }

    if (representativeObservation) {
      if (representativeObservation.region && representativeObservation.region !== region) {
         setRegion(representativeObservation.region);
      }
      setSelectedObservation({
        ...representativeObservation,

        // Case-level intelligence takes precedence.
        facility_name: String(
          investigation.facility_name ??
            representativeObservation.name ??
            "Unknown source"
        ).replace(/refineryrefinery/gi, "Refinery"),

        behavior_state: investigation.behavior_state,
        behavior_score: investigation.behavior_score,
        persistence_state: investigation.persistence_state,
        investigation_priority: investigation.investigation_priority,
        observation_count: investigation.observation_count,
        max_frp_mw: investigation.max_frp_mw,
        mean_frp_mw: investigation.mean_frp_mw,
        total_frp_mw: investigation.total_frp_mw,
        previous_active_days: investigation.previous_active_days,
        active_days: investigation.active_days,
        frp_score: investigation.frp_score,
        detection_score: investigation.detection_score,
        frequency_score: investigation.frequency_score,
        evidence_quality: investigation.evidence_quality,
        is_investigation_candidate: investigation.is_investigation_candidate,
        
        spatial_behavior_state: investigation.spatial_behavior_state,
        spatial_behavior_score: investigation.spatial_behavior_score,
        historical_centroid_lat: investigation.historical_centroid_lat,
        historical_centroid_lon: investigation.historical_centroid_lon,
        current_centroid_lat: investigation.current_centroid_lat,
        current_centroid_lon: investigation.current_centroid_lon,
        centroid_shift_km: investigation.centroid_shift_km,
        historical_spatial_radius_km: investigation.historical_spatial_radius_km,
        current_spatial_radius_km: investigation.current_spatial_radius_km,
        spatial_expansion_ratio: investigation.spatial_expansion_ratio,
        historical_spatial_observation_count: investigation.historical_spatial_observation_count,

        baseline_mean_frp:
          investigation.baseline_mean_frp ??
          representativeObservation.baseline_mean_frp,

        baseline_p90_frp:
          investigation.baseline_p90_frp ??
          representativeObservation.baseline_p90_frp,

        baseline_median_frp:
          investigation.baseline_median_frp ??
          representativeObservation.baseline_median_frp,

        baseline_std_frp:
          investigation.baseline_std_frp ??
          representativeObservation.baseline_std_frp,

        baseline_active_days: investigation.baseline_active_days,
        baseline_period_days: investigation.baseline_period_days,

        // Preserve the case interpretation.
        interpretation:
          investigation.decision_interpretation ??
          representativeObservation.interpretation,

        evidence_summary:
          investigation.evidence_summary ??
          representativeObservation.evidence_summary,
      });

      return;
    }

    // Fallback: If no raw observation can be matched, still allow the case to open.
    setSelectedObservation({
      ...investigation,

      facility_name: String(
        investigation.facility_name ?? "Unknown source"
      ).replace(/refineryrefinery/gi, "Refinery"),

      latitude: Number(investigation.latitude),
      longitude: Number(investigation.longitude),
    });
  };

  // --------------------------------------------------------
  // Apply Filters
  // --------------------------------------------------------

  const filteredInvestigations = investigations.filter((inv) => {
    if (filterSourceClass !== "ALL") {
      const srcClass =
        inv.source_class_v2 ?? inv.source_class ?? "UNKNOWN";
      if (srcClass !== filterSourceClass) return false;
    }
    if (filterPriority !== "ALL") {
      if (inv.investigation_priority !== filterPriority) return false;
    }
    if (filterDate !== "ALL") {
      if (inv.acq_date !== filterDate) return false;
    }
    return true;
  });

  // Create a priority lookup map for map observations
  const priorityMap = new Map();
  investigations.forEach((inv) => {
    const facName = String(inv.facility_name ?? inv.name ?? "UNKNOWN")
      .trim()
      .toLowerCase()
      .replace(/refineryrefinery/gi, "refinery");
    priorityMap.set(`${facName}_${inv.acq_date}`, inv.investigation_priority);
  });

  const filteredObservations = globalEvents.filter((obs) => {
    if (filterSourceClass !== "ALL") {
      const srcClass =
        obs.source_class_v2 ?? obs.source_class ?? "UNKNOWN";
      if (srcClass !== filterSourceClass) return false;
    }
    if (filterPriority !== "ALL") {
      if (obs.investigation_priority !== filterPriority) return false;
    }
    if (filterDate !== "ALL") {
      if (obs.acq_date !== filterDate) return false;
    }
    return true;
  });

  const uniqueDates = [
    ...new Set(
      observations.map((o) => o.acq_date).filter(Boolean)
    ),
  ]
    .sort()
    .reverse();

  // Persistent unmatched sources (from /unknown-sources)
  const persistentSources = unknownSources.filter(
    (s) =>
      (s.persistence_class === "PERSISTENT" ||
        s.persistence_class === "RECURRING") &&
      s.event_count >= 3
  );
  const transientSources = unknownSources.filter(
    (s) =>
      s.persistence_class !== "PERSISTENT" &&
      s.persistence_class !== "RECURRING" &&
      s.event_count < 3
  );

  return (
    <div className="app">

      {/* ------------------------------------------------ */}
      {/* TOP BAR */}
      {/* ------------------------------------------------ */}

      <header className="topbar">

        <div>
          <div className="brand">SIH26162</div>
          <div className="subtitle">Industrial Thermal Intelligence</div>
        </div>

        <div className="system-status" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {regions.length > 0 && (
            <select
              value={region}
              onChange={(e) => handleRegionChange(e.target.value)}
              style={{
                background: "rgba(255, 255, 255, 0.1)",
                color: "white",
                border: "1px solid rgba(255,255,255,0.2)",
                padding: "0.25rem 0.5rem",
                borderRadius: "4px",
                outline: "none",
              }}
            >
              {regions.map((r) => (
                <option key={r.id} value={r.id} style={{ color: "black" }}>
                  {r.name}
                </option>
              ))}
            </select>
          )}
          <span className="status-dot"></span>
          SYSTEM ONLINE
        </div>

      </header>


      {/* ------------------------------------------------ */}
      {/* DASHBOARD */}
      {/* ------------------------------------------------ */}

      <main className="dashboard">

        {/* Intro */}
        <section className="intro">
          <h1>Thermal Source Intelligence</h1>
          <p>
            Context-aware monitoring of industrial-associated thermal activity
            and historical site behaviour.
          </p>
        </section>

        {/* Error */}
        {error ? (

          <div className="error-box">
            Backend connection failed: {error}
          </div>

        ) : (

          <>

            {/* Summary */}
            <SummaryCards summary={summary} />

            {/* Filters */}
            <div
              className="dashboard-filters"
              style={{
                display: "flex",
                gap: "16px",
                margin: "16px 0",
                padding: "16px",
                background: "#0b111b",
                border: "1px solid #243044",
                borderRadius: "12px",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "10px", fontWeight: "bold", color: "#94a3b8" }}>
                  SOURCE CLASS
                </label>
                <select
                  value={filterSourceClass}
                  onChange={(e) => setFilterSourceClass(e.target.value)}
                  style={{
                    padding: "8px",
                    background: "#172033",
                    color: "#e2e8f0",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                  }}
                >
                  <option value="ALL">All Sources</option>
                  <option value="INDUSTRIAL_ASSOCIATED">Industrial-associated</option>
                  <option value="AGRICULTURAL">Agricultural</option>
                  <option value="FOREST_NATURAL">Forest / Natural</option>
                  <option value="OTHER">Other</option>
                  <option value="UNKNOWN">Unknown / Unmatched</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "10px", fontWeight: "bold", color: "#94a3b8" }}>
                  PRIORITY
                </label>
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  style={{
                    padding: "8px",
                    background: "#172033",
                    color: "#e2e8f0",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                  }}
                >
                  <option value="ALL">All Priorities</option>
                  <option value="HIGH">High Priority</option>
                  <option value="MEDIUM">Medium Priority</option>
                  <option value="LOW">Low Priority</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "10px", fontWeight: "bold", color: "#94a3b8" }}>
                  DATE
                </label>
                <select
                  value={filterDate}
                  onChange={(e) => setFilterDate(e.target.value)}
                  style={{
                    padding: "8px",
                    background: "#172033",
                    color: "#e2e8f0",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                  }}
                >
                  <option value="ALL">All Dates</option>
                  {uniqueDates.map((date) => (
                    <option key={date} value={date}>
                      {date}
                    </option>
                  ))}
                </select>
              </div>
            </div>


            {/* Map section */}
            <section className="dashboard-section">

              <div className="section-header">
                <h2>Thermal Activity Map</h2>
                <span>{filteredObservations.length} thermal events — global map</span>
              </div>

              {/* Map + Investigation Panel */}
              <div className="map-wrapper">

                <MapView
                  observations={filteredObservations}
                  onObservationSelect={(obs) => {
                     // Check for cross region click
                     if (obs && obs.region && obs.region !== region) {
                       setRegion(obs.region);
                     }
                     
                     // Attempt to enrich with investigation intelligence if available
                     const matchingInv = investigations.find(i => 
                        (i.event_id && i.event_id === obs.event_id) || 
                        (i.facility_name === (obs.name || obs.facility_name) && i.acq_date === (obs.event_date ?? obs.acq_date))
                     );
                     
                     if (matchingInv) {
                       setSelectedObservation({
                         ...obs,
                         facility_name: String(matchingInv.facility_name ?? obs.name ?? "Unknown source").replace(/refineryrefinery/gi, "Refinery"),
                         behavior_state: matchingInv.behavior_state,
                         behavior_score: matchingInv.behavior_score,
                         persistence_state: matchingInv.persistence_state,
                         investigation_priority: matchingInv.investigation_priority,
                         observation_count: matchingInv.observation_count,
                         max_frp_mw: matchingInv.max_frp_mw,
                         mean_frp_mw: matchingInv.mean_frp_mw,
                         total_frp_mw: matchingInv.total_frp_mw,
                         previous_active_days: matchingInv.previous_active_days,
                         active_days: matchingInv.active_days,
                         frp_score: matchingInv.frp_score,
                         detection_score: matchingInv.detection_score,
                         frequency_score: matchingInv.frequency_score,
                         spatial_behavior_state: matchingInv.spatial_behavior_state,
                         spatial_behavior_score: matchingInv.spatial_behavior_score,
                         historical_centroid_lat: matchingInv.historical_centroid_lat,
                         historical_centroid_lon: matchingInv.historical_centroid_lon,
                         current_centroid_lat: matchingInv.current_centroid_lat,
                         current_centroid_lon: matchingInv.current_centroid_lon,
                         centroid_shift_km: matchingInv.centroid_shift_km,
                         historical_spatial_radius_km: matchingInv.historical_spatial_radius_km,
                         current_spatial_radius_km: matchingInv.current_spatial_radius_km,
                         spatial_expansion_ratio: matchingInv.spatial_expansion_ratio,
                         historical_spatial_observation_count: matchingInv.historical_spatial_observation_count,
                         decision_interpretation: matchingInv.decision_interpretation,
                         reason: matchingInv.reason,
                         evidence_quality: matchingInv.evidence_quality
                       });
                     } else {
                       setSelectedObservation(obs);
                     }
                  }}
                  selectedObservation={selectedObservation}
                  activeRegionId={region}
                  center={regions.find((r) => r.id === region)?.center}
                />

                <InvestigationPanel
                  observation={selectedObservation}
                  region={region}
                  onClose={() => setSelectedObservation(null)}
                />

              </div>

              {/* Investigation Queue — genuine human-review candidates only */}
              <InvestigationQueue
                investigations={filteredInvestigations}
                onSelect={handleInvestigationSelect}
              />

              {/* Unmatched Thermal Activity */}
              {unknownSources.length > 0 && (
                <section
                  className="investigation-section"
                  style={{ marginTop: "24px" }}
                >
                  <div className="investigation-header">
                    <div>
                      <h2>Unmatched Thermal Activity</h2>
                      <p>
                        Thermal sources with no confirmed facility association.
                        Requires human verification before classification.
                      </p>
                    </div>
                    <div className="queue-count">{unknownSources.length} sources</div>
                  </div>

                  <div
                    style={{
                      fontSize: "10px",
                      color: "#94a3b8",
                      marginBottom: "12px",
                      fontStyle: "italic",
                      padding: "8px 12px",
                      background: "rgba(56,189,248,0.05)",
                      border: "1px solid rgba(56,189,248,0.15)",
                      borderRadius: "6px",
                    }}
                  >
                    These are unmatched thermal detections — not confirmed
                    industrial events. Wording reflects uncertainty.
                  </div>

                  <div className="queue-table-wrapper">
                    <table className="queue-table">
                      <thead>
                        <tr>
                          <th>Source ID</th>
                          <th>Persistence</th>
                          <th>Events</th>
                          <th>Active Days</th>
                          <th>Max FRP</th>
                          <th>Land Cover</th>
                          <th>Evidence</th>
                          <th>Note</th>
                        </tr>
                      </thead>
                      <tbody>
                        {unknownSources.map((src, i) => (
                          <tr key={src.source_id ?? i}>
                            <td>
                              <span
                                style={{
                                  fontFamily: "monospace",
                                  fontSize: "11px",
                                  color: "#38bdf8",
                                }}
                              >
                                {src.source_id}
                              </span>
                            </td>
                            <td>
                              <span
                                className={`behavior-badge ${
                                  src.persistence_class === "PERSISTENT" ||
                                  src.persistence_class === "RECURRING"
                                    ? "behavior-unusual"
                                    : "behavior-watch"
                                }`}
                              >
                                {src.persistence_class ?? "—"}
                              </span>
                            </td>
                            <td>{src.event_count ?? "—"}</td>
                            <td>{src.active_days ?? "—"}</td>
                            <td>
                              {src.max_frp != null
                                ? `${Number(src.max_frp).toFixed(1)} MW`
                                : "—"}
                            </td>
                            <td
                              style={{ fontSize: "11px", color: "#94a3b8" }}
                            >
                              {src.landcover_context ?? "—"}
                            </td>
                            <td
                              style={{ fontSize: "11px", color: "#94a3b8" }}
                            >
                              {src.evidence_strength ?? "—"}
                            </td>
                            <td
                              style={{
                                fontSize: "10px",
                                color: "#64748b",
                                fontStyle: "italic",
                              }}
                            >
                              {src.persistence_class === "PERSISTENT" ||
                              src.persistence_class === "RECURRING"
                                ? "Persistent unmatched source — requires verification"
                                : "Transient unmatched event"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

            </section>

          </>

        )}

      </main>

    </div>
  );
}

export default App;