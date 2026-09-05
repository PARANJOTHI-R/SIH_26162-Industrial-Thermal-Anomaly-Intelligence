import { useEffect, useState } from "react";

import {
  getSummary,
  getThermalObservations,
  getInvestigations,
  getRegions,
} from "./services/api";

import SummaryCards from "./components/SummaryCards";
import MapView from "./components/MapView";
import InvestigationPanel from "./components/InvestigationPanel";

import "./index.css";
import InvestigationQueue from "./components/InvestigationQueue";
function App() {
  const [summary, setSummary] = useState(null);
  const [observations, setObservations] = useState([]);
  const [selectedObservation, setSelectedObservation] = useState(null);
  const [error, setError] = useState(null);
  const [investigations, setInvestigations] = useState([]);
  
  // Region
  const [region, setRegion] = useState("jamnagar");
  const [regions, setRegions] = useState([]);
  
  // Filters
  const [filterSourceClass, setFilterSourceClass] = useState("ALL");
  const [filterPriority, setFilterPriority] = useState("ALL");
  const [filterDate, setFilterDate] = useState("ALL");

  useEffect(() => {
    async function fetchRegions() {
      try {
        const data = await getRegions();
        setRegions(data.regions || []);
      } catch (err) {
        console.error("Failed to fetch regions:", err);
      }
    }
    fetchRegions();
  }, []);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryData, observationData, investigationsData] =
          await Promise.all([
            getSummary(region),
            getThermalObservations(region),
            getInvestigations(region, "ALL"),
          ]);

        console.log(
          "Summary received:",
          summaryData
        );

        console.log(
          "Thermal observations response:",
          observationData
        );

        setSummary(summaryData);

        // Backend normally returns:
        // { records: [...] }
        //
        // Also support a direct array response.
        if (Array.isArray(observationData)) {
          setObservations(observationData);
        } else if (
          Array.isArray(observationData?.records)
        ) {
          setObservations(
            observationData.records
          );
        } else if (
          Array.isArray(observationData?.observations)
        ) {
          setObservations(
            observationData.observations
          );
        } else {
          console.warn(
            "No valid thermal observation records found:",
            observationData
          );

          setObservations([]);
        }
        console.log(
          "Investigations received:",
          investigationsData
        );

        setInvestigations(
          Array.isArray(investigationsData) ? investigationsData : (investigationsData?.investigations || [])
        );
      } catch (err) {
        console.error(
          "Dashboard loading error:",
          err
        );

        setError(err.message);
        setObservations([]);
      }
    }

    loadDashboard();
  }, [region]);
  const handleInvestigationSelect = (investigation) => {
    if (!investigation) return;

    const facilityName = String(
      investigation.facility_name ??
      investigation.name ??
      ""
    )
      .trim()
      .toLowerCase();

    const date = String(
      investigation.acq_date ?? ""
    ).trim();

    // Find all raw FIRMS observations belonging
    // to this facility-day case.
    const matchingObservations = observations.filter(
      (observation) => {
        const observationFacility = String(
          observation.name ??
          observation.facility_name ??
          ""
        )
          .trim()
          .toLowerCase();

        const observationDate = String(
          observation.acq_date ?? ""
        ).trim();

        return (
          observationFacility === facilityName &&
          observationDate === date
        );
      }
    );

    // Select the strongest thermal observation
    // as the representative map point.
    const representativeObservation =
      matchingObservations.length > 0
        ? [...matchingObservations].sort(
          (a, b) =>
            Number(b.frp ?? 0) -
            Number(a.frp ?? 0)
        )[0]
        : null;

    if (representativeObservation) {
      setSelectedObservation({
        ...representativeObservation,

        // Case-level intelligence takes precedence.
        facility_name: String(
          investigation.facility_name ??
          representativeObservation.name ??
          "Unknown source"
        ).replace(/refineryrefinery/ig, 'Refinery'),

        behavior_state:
          investigation.behavior_state,

        behavior_score:
          investigation.behavior_score,

        persistence_state:
          investigation.persistence_state,

        investigation_priority:
          investigation.investigation_priority,

        observation_count:
          investigation.observation_count,

        max_frp_mw:
          investigation.max_frp_mw,

        mean_frp_mw:
          investigation.mean_frp_mw,

        total_frp_mw:
          investigation.total_frp_mw,

        previous_active_days:
          investigation.previous_active_days,

        frp_score:
          investigation.frp_score,

        detection_score:
          investigation.detection_score,

        frequency_score:
          investigation.frequency_score,

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

    // Fallback:
    // If no raw observation can be matched,
    // still allow the case to open.
    setSelectedObservation({
      ...investigation,

      facility_name: String(
        investigation.facility_name ??
        "Unknown source"
      ).replace(/refineryrefinery/ig, 'Refinery'),

      latitude:
        Number(investigation.latitude),

      longitude:
        Number(investigation.longitude),
    });
  };

  // --------------------------------------------------------
  // Apply Filters
  // --------------------------------------------------------
  
  const filteredInvestigations = investigations.filter(inv => {
    if (filterSourceClass !== "ALL") {
      const srcClass = inv.source_class_v2 ?? inv.source_class ?? "UNKNOWN";
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

  // Create a priority lookup map for observations
  const priorityMap = new Map();
  investigations.forEach(inv => {
    const facName = String(inv.facility_name ?? inv.name ?? "UNKNOWN")
      .trim().toLowerCase().replace(/refineryrefinery/ig, 'refinery');
    priorityMap.set(`${facName}_${inv.acq_date}`, inv.investigation_priority);
  });

  const filteredObservations = observations.filter(obs => {
    if (filterSourceClass !== "ALL") {
      const srcClass = obs.source_class_v2 ?? obs.source_class ?? "UNKNOWN";
      if (srcClass !== filterSourceClass) return false;
    }
    if (filterPriority !== "ALL") {
      const facName = String(obs.facility_name ?? obs.name ?? "UNKNOWN")
        .trim().toLowerCase().replace(/refineryrefinery/ig, 'refinery');
      const obsPriority = priorityMap.get(`${facName}_${obs.acq_date}`) || "LOW";
      if (obsPriority !== filterPriority) return false;
    }
    if (filterDate !== "ALL") {
      if (obs.acq_date !== filterDate) return false;
    }
    return true;
  });

  const uniqueDates = [...new Set(observations.map(o => o.acq_date).filter(Boolean))].sort().reverse();

  return (
    <div className="app">

      {/* ------------------------------------------------ */}
      {/* TOP BAR */}
      {/* ------------------------------------------------ */}

      <header className="topbar">

        <div>
          <div className="brand">
            SIH26162
          </div>

          <div className="subtitle">
            Industrial Thermal Intelligence
          </div>
        </div>

        <div className="system-status" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {regions.length > 0 && (
            <select 
              value={region} 
              onChange={(e) => setRegion(e.target.value)}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.2)',
                padding: '0.25rem 0.5rem',
                borderRadius: '4px',
                outline: 'none',
              }}
            >
              {regions.map(r => (
                <option key={r.id} value={r.id} style={{color: 'black'}}>
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

          <h1>
            Thermal Source Intelligence
          </h1>

          <p>
            Context-aware monitoring of
            industrial-associated thermal
            activity and historical site behaviour.
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

            <SummaryCards
              summary={summary}
            />

            {/* Filters */}
            <div className="dashboard-filters" style={{ display: 'flex', gap: '16px', margin: '16px 0', padding: '16px', background: '#0b111b', border: '1px solid #243044', borderRadius: '12px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8' }}>SOURCE CLASS</label>
                <select value={filterSourceClass} onChange={e => setFilterSourceClass(e.target.value)} style={{ padding: '8px', background: '#172033', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '4px' }}>
                  <option value="ALL">All Sources</option>
                  <option value="INDUSTRIAL_ASSOCIATED">Industrial-associated</option>
                  <option value="AGRICULTURAL">Agricultural</option>
                  <option value="FOREST_NATURAL">Forest / Natural</option>
                  <option value="OTHER">Other</option>
                  <option value="UNKNOWN">Unknown / Unmatched</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8' }}>PRIORITY</label>
                <select value={filterPriority} onChange={e => setFilterPriority(e.target.value)} style={{ padding: '8px', background: '#172033', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '4px' }}>
                  <option value="ALL">All Priorities</option>
                  <option value="HIGH">High Priority</option>
                  <option value="MEDIUM">Medium Priority</option>
                  <option value="LOW">Low Priority</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8' }}>DATE</label>
                <select value={filterDate} onChange={e => setFilterDate(e.target.value)} style={{ padding: '8px', background: '#172033', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '4px' }}>
                  <option value="ALL">All Dates</option>
                  {uniqueDates.map(date => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </select>
              </div>
            </div>


            {/* Map section */}

            <section className="dashboard-section">

              <div className="section-header">

                <h2>
                  Thermal Activity Map
                </h2>

                <span>
                  {observations.length} thermal observations
                </span>

              </div>


              {/* Map + Investigation Panel */}

              <div className="map-wrapper">

                <MapView
                  observations={filteredObservations}
                  onObservationSelect={
                    setSelectedObservation
                  }
                  selectedObservation={selectedObservation}
                  center={regions.find(r => r.id === region)?.center}
                />


                <InvestigationPanel
                  observation={
                    selectedObservation
                  }
                  onClose={() =>
                    setSelectedObservation(null)
                  }
                />

              </div>
              <InvestigationQueue
                investigations={filteredInvestigations}
                onSelect={handleInvestigationSelect}
              />

            </section>

          </>

        )}

      </main>

    </div>
  );
}

export default App;