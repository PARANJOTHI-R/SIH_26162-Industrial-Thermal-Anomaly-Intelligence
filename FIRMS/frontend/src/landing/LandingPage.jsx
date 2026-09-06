import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./landing.css";

/* ------------------------------------------------------------------ */
/* Smooth-scroll helper                                                  */
/* ------------------------------------------------------------------ */
function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

/* ------------------------------------------------------------------ */
/* Counter — animates a number up when in viewport                      */
/* ------------------------------------------------------------------ */
function AnimatedCounter({ target, suffix = "" }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const duration = 900;
          const steps = 40;
          let step = 0;
          const timer = setInterval(() => {
            step++;
            setDisplay(Math.round((target * step) / steps));
            if (step >= steps) clearInterval(timer);
          }, duration / steps);
        }
      },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [target]);

  return (
    <span ref={ref} className="lp-counter">
      {display}
      {suffix}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Hero Map — professional GIS analytical figure                        */
/* ------------------------------------------------------------------ */
function HeroMap() {
  return (
    <div className="lp-map-canvas">
      {/* Water impression */}
      <div className="lp-map-water" />

      {/* Road impressions */}
      <div className="lp-map-road lp-road-h" style={{ top: "45%" }} />
      <div className="lp-map-road lp-road-h" style={{ top: "70%" }} />
      <div className="lp-map-road lp-road-v" style={{ left: "38%" }} />
      <div className="lp-map-road lp-road-v" style={{ left: "65%" }} />

      {/* Industrial facility polygons */}
      <div className="lp-facility" style={{ left: "10%", top: "18%", width: "24%", height: "20%" }}>
        <span className="lp-facility-label">Refinery Complex A</span>
      </div>
      <div className="lp-facility" style={{ left: "53%", top: "26%", width: "18%", height: "15%" }}>
        <span className="lp-facility-label">Petrochemical Unit B</span>
      </div>
      <div className="lp-facility" style={{ left: "28%", top: "58%", width: "20%", height: "13%" }}>
        <span className="lp-facility-label">Industrial Zone C</span>
      </div>

      {/* Thermal observations — flat dots, no glow */}
      {/* HIGH — red dot with analytical callout */}
      <div className="lp-thermal-dot lp-high" style={{ left: "22%", top: "26%" }} />

      {/* MEDIUM — orange dots */}
      <div className="lp-thermal-dot lp-medium" style={{ left: "60%", top: "31%" }} />
      <div className="lp-thermal-dot lp-medium" style={{ left: "64%", top: "35%" }} />

      {/* LOW — amber dots */}
      <div className="lp-thermal-dot lp-low" style={{ left: "36%", top: "64%" }} />
      <div className="lp-thermal-dot lp-low" style={{ left: "40%", top: "60%" }} />
      <div className="lp-thermal-dot lp-low" style={{ left: "79%", top: "71%" }} />

      {/* Analytical callout attached to high-priority event */}
      <div className="lp-map-callout" style={{ top: 12, right: 12 }}>
        <div className="lp-map-callout-title">Investigation Candidate</div>
        <div className="lp-map-callout-row">
          <span>Observed FRP</span>
          <span className="lp-map-callout-val lp-thermal">16.63 MW</span>
        </div>
        <div className="lp-map-callout-row">
          <span>Historical P90</span>
          <span className="lp-map-callout-val">4.99 MW</span>
        </div>
        <div className="lp-map-callout-row">
          <span>Ratio</span>
          <span className="lp-map-callout-val lp-thermal">3.33× P90</span>
        </div>
        <div className="lp-map-callout-row">
          <span>State</span>
          <span className="lp-map-callout-val lp-watch">WATCH</span>
        </div>
      </div>

      {/* Simple legend */}
      <div className="lp-map-legend">
        <div className="lp-map-legend-item">
          <div className="lp-legend-dot" style={{ background: "#A3241A" }} />
          High priority
        </div>
        <div className="lp-map-legend-item">
          <div className="lp-legend-dot" style={{ background: "#C4611A" }} />
          Thermal event
        </div>
        <div className="lp-map-legend-item">
          <div className="lp-legend-dot" style={{ background: "rgba(23,107,120,0.5)", border: "1.5px solid #176B78", borderRadius: "2px", width: "10px", height: "7px" }} />
          Industrial area
        </div>
      </div>

      <div className="lp-map-label">
        Conceptual visualization — not actual satellite imagery
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Landing Page                                                    */
/* ------------------------------------------------------------------ */
export default function LandingPage() {
  const navigate = useNavigate();
  const goDashboard = () => navigate("/dashboard");

  return (
    <div className="lp-root">

      {/* ---- NAV ---- */}
      <nav className="lp-nav">
        <div className="lp-nav-brand">
          <div className="lp-nav-brand-name">SIH26162</div>
          <div className="lp-nav-brand-sub">Industrial Thermal Intelligence</div>
        </div>
        <div className="lp-nav-links">
          <button className="lp-nav-link" onClick={() => scrollTo("how-it-works")}>How It Works</button>
          <button className="lp-nav-link" onClick={() => scrollTo("pilot-results")}>Results</button>
          <button className="lp-nav-link" onClick={() => scrollTo("technology")}>Technology</button>
          <button className="lp-nav-link" onClick={() => scrollTo("limitations")}>Limitations</button>
          <button className="lp-nav-cta" onClick={goDashboard}>Open Dashboard</button>
        </div>
      </nav>

      {/* ---- HERO ---- */}
      <section className="lp-hero">
        <div className="lp-hero-content">
          <div className="lp-hero-eyebrow">
            <span className="lp-hero-eyebrow-dot" />
            SIH 2026 · Problem Statement SIH26162
          </div>
          <h1 className="lp-hero-headline">
            From Satellite Thermal Signals to{" "}
            <span className="lp-hero-teal">Industrial Thermal Intelligence</span>
          </h1>
          <p className="lp-hero-sub">
            Detect, contextualize and analyse persistent thermal activity
            around industrial facilities using NASA FIRMS, geospatial
            infrastructure data and historical site behaviour.
          </p>
          <div className="lp-hero-actions">
            <button className="lp-btn-primary" onClick={goDashboard}>
              Explore Thermal Intelligence
            </button>
            <button className="lp-btn-secondary" onClick={() => scrollTo("how-it-works")}>
              How It Works ↓
            </button>
          </div>
          <div className="lp-credibility-strip">
            <span className="lp-cred-label">Data sources</span>
            <span className="lp-cred-item">NASA FIRMS</span>
            <span className="lp-cred-item">OpenStreetMap</span>
            <span className="lp-cred-item">ESA WorldCover</span>
            <span className="lp-cred-item">Geospatial Analytics</span>
          </div>
        </div>
        <div className="lp-hero-visual">
          <HeroMap />
        </div>
      </section>

      {/* ---- PROBLEM ---- */}
      <hr className="lp-section-divider" />
      <div>
        <div className="lp-section">
          <div className="lp-section-eyebrow">The Problem</div>
          <div className="lp-problem-grid">
            <div>
              <h2 className="lp-section-heading">
                A Thermal Anomaly Is Only the Beginning
              </h2>
              <div className="lp-problem-text">
                <p>
                  NASA FIRMS provides satellite thermal anomaly observations, but
                  an observation alone does not tell an investigator:
                </p>
                <p>
                  Whether it is associated with industrial infrastructure.
                  Whether it is natural, agricultural, or another source.
                  Whether the source is persistent. Whether the activity is{" "}
                  <em>normal</em> for that specific site. Whether current
                  behaviour meaningfully differs from historical behaviour.
                  Whether the observation deserves targeted investigation.
                </p>
                <div className="lp-problem-statement">
                  "Detection tells you where to look. Intelligence helps explain
                  why it matters."
                </div>
              </div>
            </div>

            <div className="lp-pipeline-viz">
              {[
                { label: "Thermal Anomaly Detection",    badge: "NASA FIRMS",       cls: "lp-badge-orange" },
                { label: "Geographic Context",           badge: "OSM + WorldCover",  cls: "lp-badge-teal"   },
                { label: "Source Classification",        badge: "5 classes",         cls: "lp-badge-teal"   },
                { label: "Historical Behaviour Profile", badge: "Site Fingerprint",  cls: "lp-badge-purple" },
                { label: "Deviation Analysis",           badge: "Behaviour Score",   cls: "lp-badge-orange" },
                { label: "Investigation Candidate",      badge: "Human Review",      cls: "lp-badge-green"  },
              ].map((item, i) => (
                <div key={item.label}>
                  <div className="lp-pipeline-step">
                    <span className="lp-pipeline-step-num">0{i + 1}</span>
                    <span className="lp-pipeline-step-label">{item.label}</span>
                    <span className={`lp-pipeline-step-badge ${item.cls}`}>{item.badge}</span>
                  </div>
                  {i < 5 && <div className="lp-pipeline-arrow">↓</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ---- CAPABILITIES ---- */}
      <hr className="lp-section-divider" />
      <div className="lp-section-alt">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Capabilities</div>
          <h2 className="lp-section-heading">
            One Intelligence Layer Across the Thermal Lifecycle
          </h2>
          <p className="lp-section-sub">
            Five analytical stages convert raw satellite observations into
            evidence-backed investigation candidates.
          </p>
          <div className="lp-cap-grid">
            <div className="lp-cap-card">
              <div className="lp-cap-num">01</div>
              <div className="lp-cap-title">Thermal Event Detection</div>
              <div className="lp-cap-body">
                Nearby observations within the same spatial-temporal window
                are aggregated into meaningful thermal events. Raw FIRMS
                observations are preserved for provenance.
              </div>
              <div className="lp-cap-tags">
                <span className="lp-cap-tag">NASA FIRMS</span>
                <span className="lp-cap-tag">Clustering</span>
              </div>
            </div>
            <div className="lp-cap-card">
              <div className="lp-cap-num">02</div>
              <div className="lp-cap-title">Source Classification</div>
              <div className="lp-cap-body">
                Each thermal event is classified using OSM infrastructure and
                land-cover context:{" "}
                <strong>Industrial-associated · Agricultural · Forest/Natural · Other · Unknown/Unmatched.</strong>{" "}
                Industrial-associated indicates contextual association with
                mapped infrastructure — not a confirmed industrial fire.
              </div>
              <div className="lp-cap-tags">
                <span className="lp-cap-tag">OSM</span>
                <span className="lp-cap-tag">WorldCover</span>
              </div>
            </div>
            <div className="lp-cap-card">
              <div className="lp-cap-num">03</div>
              <div className="lp-cap-title">Site Thermal Fingerprint</div>
              <div className="lp-cap-body">
                The system builds a historical behaviour profile per facility:
                typical FRP, mean/median, P90/P95, activity frequency,
                persistence and spatial footprint.
                <br /><br />
                Every industrial site has a thermal behaviour pattern. This
                history is the analytical baseline.
              </div>
              <div className="lp-cap-tags">
                <span className="lp-cap-tag">Historical Baseline</span>
                <span className="lp-cap-tag">P90/P95</span>
              </div>
            </div>
            <div className="lp-cap-card">
              <div className="lp-cap-num">04</div>
              <div className="lp-cap-title">Behaviour Deviation</div>
              <div className="lp-cap-body">
                Current events are compared against the historical baseline
                across FRP intensity, detection frequency, persistence and
                spatial behaviour.
              </div>
              <div className="lp-cap-tags">
                <span className="lp-cap-tag">NORMAL</span>
                <span className="lp-cap-tag">WATCH</span>
                <span className="lp-cap-tag">UNUSUAL</span>
              </div>
            </div>
            <div className="lp-cap-card">
              <div className="lp-cap-num">05</div>
              <div className="lp-cap-title">Investigation Intelligence</div>
              <div className="lp-cap-body">
                Contextual and behavioural evidence is synthesized into
                evidence quality, investigation priority and an explainable
                candidate report.
                <br /><br />
                The system prioritizes cases for human review. It does not
                automatically declare an incident.
              </div>
              <div className="lp-cap-tags">
                <span className="lp-cap-tag">Evidence Quality</span>
                <span className="lp-cap-tag">Priority</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- HOW IT WORKS ---- */}
      <hr className="lp-section-divider" />
      <div id="how-it-works">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Pipeline</div>
          <h2 className="lp-section-heading">From Detection to Investigation Candidate</h2>
          <p className="lp-section-sub">
            Eight analytical stages convert raw satellite observations into
            evidence-backed investigation candidates.
          </p>
          <div className="lp-pipeline-row">
            {[
              { n: "01", title: "Observe",       sub: "NASA FIRMS thermal observations" },
              { n: "02", title: "Cluster",        sub: "Spatiotemporal aggregation" },
              { n: "03", title: "Contextualize",  sub: "OSM + land-cover context" },
              { n: "04", title: "Classify",       sub: "Industrial / Agricultural / Natural / Unknown" },
              { n: "05", title: "Learn",          sub: "Site thermal fingerprints" },
              { n: "06", title: "Compare",        sub: "Current vs historical baseline" },
              { n: "07", title: "Prioritize",     sub: "Evidence quality + deviation" },
              { n: "08", title: "Investigate",    sub: "GIS dashboard + report" },
            ].map((col, i, arr) => (
              <div key={col.n} style={{ display: "flex", alignItems: "flex-start" }}>
                <div className="lp-pipeline-col">
                  <div className="lp-pipeline-node">{col.n}</div>
                  <div className="lp-pipeline-col-title">{col.title}</div>
                  <div className="lp-pipeline-col-sub">{col.sub}</div>
                </div>
                {i < arr.length - 1 && <div className="lp-pipeline-connector" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ---- BASELINE COMPARISON ---- */}
      <hr className="lp-section-divider" />
      <div className="lp-section-alt">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Context-Aware Analysis</div>
          <h2 className="lp-section-heading">
            Normal for One Facility Can Be Abnormal for Another
          </h2>
          <p className="lp-section-sub">
            A fixed global FRP threshold misses the context of a facility's
            normal operating behaviour. The system compares activity against
            each site's historical pattern.
          </p>
          <div className="lp-baseline-grid">
            <div className="lp-baseline-card lp-baseline-normal">
              <div className="lp-baseline-facility">Facility A — Normal Operating Day</div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Typical FRP range</span>
                <span className="lp-baseline-val">3 – 5 MW</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Current event FRP</span>
                <span className="lp-baseline-val">4 MW</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Observed / P90</span>
                <span className="lp-baseline-val">0.9×</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Result</span>
                <span className="lp-baseline-val lp-result-normal">NORMAL</span>
              </div>
            </div>
            <div className="lp-baseline-card lp-baseline-watch">
              <div className="lp-baseline-facility">Reliance Refinery — Jun 9, 2026</div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Historical P90</span>
                <span className="lp-baseline-val">4.99 MW</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Observed peak FRP</span>
                <span className="lp-baseline-val lp-watch">16.63 MW</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Observed / P90</span>
                <span className="lp-baseline-val lp-watch">3.33×</span>
              </div>
              <div className="lp-baseline-row">
                <span className="lp-baseline-key">Result</span>
                <span className="lp-baseline-val lp-result-watch">WATCH · HIGH Evidence</span>
              </div>
            </div>
          </div>
          <div className="lp-baseline-note">
            * Pilot dataset results. Reliance Refinery, Jamnagar. Evidence quality: HIGH.
            Investigation priority: MEDIUM. Persistence: RECURRING.
            This is an investigation candidate — not an automatically confirmed industrial fire or accident.
          </div>
        </div>
      </div>

      {/* ---- PILOT RESULTS ---- */}
      <hr className="lp-section-divider" />
      <div id="pilot-results">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Pilot Dataset</div>
          <h2 className="lp-section-heading">Demonstrated on Industrial Regions</h2>
          <p className="lp-section-sub">
            Current pilot dataset results across two industrial regions.
          </p>
          <div className="lp-results-grid">
            <div className="lp-result-card">
              <div className="lp-result-region">Jamnagar</div>
              <div className="lp-result-region-sub">Petrochemical and refinery region, Gujarat</div>
              <div className="lp-result-stat-grid lp-grid-5">
                {[
                  { val: 185, key: "Raw FIRMS Obs." },
                  { val: 128, key: "Thermal Events" },
                  { val: 105, key: "Facility-Days" },
                  { val: 11,  key: "Facilities" },
                  { val: 7,   key: "Investigation Candidates" },
                ].map(({ val, key }) => (
                  <div className="lp-result-stat" key={key}>
                    <div className="lp-result-stat-val"><AnimatedCounter target={val} /></div>
                    <div className="lp-result-stat-key">{key}</div>
                  </div>
                ))}
              </div>
              <div className="lp-result-pilot-note">
                * Current pilot dataset / system results. Not national statistics.
              </div>
            </div>
            <div className="lp-result-card">
              <div className="lp-result-region">Thoothukudi</div>
              <div className="lp-result-region-sub">Industrial port region, Tamil Nadu</div>
              <div className="lp-result-stat-grid lp-grid-6">
                {[
                  { val: 302, key: "Raw FIRMS Obs." },
                  { val: 198, key: "Thermal Events" },
                  { val: 110, key: "Facility-Days" },
                  { val: 6,   key: "Facilities" },
                  { val: 19,  key: "Investigation Candidates" },
                  { val: 15,  key: "Persistent Unmatched" },
                ].map(({ val, key }) => (
                  <div className="lp-result-stat" key={key}>
                    <div className="lp-result-stat-val"><AnimatedCounter target={val} /></div>
                    <div className="lp-result-stat-key">{key}</div>
                  </div>
                ))}
              </div>
              <div className="lp-result-pilot-note">
                * Current pilot dataset / system results. Not national statistics.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- CASE STUDY — dark section ---- */}
      <div className="lp-section-dark">
        <div className="lp-section">
          <div className="lp-section-eyebrow-dark">Investigation Example</div>
          <div className="lp-case-grid">
            <div>
              <h2 className="lp-section-heading-dark">
                Detecting a Site-Specific Thermal Deviation
              </h2>
              <p className="lp-section-sub-dark">
                The system identified elevated thermal intensity at a mapped
                refinery, significantly above the facility's historical
                operating pattern. The event was associated with mapped
                industrial infrastructure and assigned a MEDIUM investigation
                priority with HIGH evidence quality.
              </p>
              <button className="lp-btn-primary-dark" onClick={goDashboard}>
                View Investigation Dashboard
              </button>
            </div>
            <div className="lp-case-card">
              <div className="lp-case-header">
                <div className="lp-case-facility">Reliance Refinery</div>
                <div className="lp-case-date">June 9, 2026 · Jamnagar, Gujarat</div>
              </div>
              <div className="lp-case-metrics">
                <div className="lp-case-metric">
                  <div className="lp-case-metric-val lp-alert">16.63 MW</div>
                  <div className="lp-case-metric-key">Observed Peak FRP</div>
                </div>
                <div className="lp-case-metric">
                  <div className="lp-case-metric-val">4.99 MW</div>
                  <div className="lp-case-metric-key">Historical P90</div>
                </div>
                <div className="lp-case-metric">
                  <div className="lp-case-metric-val lp-alert">3.33×</div>
                  <div className="lp-case-metric-key">Observed / P90 Ratio</div>
                </div>
                <div className="lp-case-metric">
                  <div className="lp-case-metric-val">RECURRING</div>
                  <div className="lp-case-metric-key">Persistence</div>
                </div>
              </div>
              <div className="lp-case-badges">
                <span className="lp-case-badge lp-badge-watch">WATCH</span>
                <span className="lp-case-badge lp-badge-medium">MEDIUM Priority</span>
                <span className="lp-case-badge lp-badge-high-ev">HIGH Evidence</span>
                <span className="lp-case-badge lp-badge-assoc">OSM Intersection</span>
              </div>
              <div className="lp-case-disclaimer">
                Investigation candidate — not an automatically confirmed
                industrial fire or accident. The system identifies elevated
                thermal activity relative to historical behaviour for human
                review.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- UNKNOWN SOURCES ---- */}
      <hr className="lp-section-divider" />
      <div>
        <div className="lp-section">
          <div className="lp-section-eyebrow">Unmatched Thermal Activity</div>
          <div className="lp-unknown-grid">
            <div>
              <h2 className="lp-section-heading">
                What About Sources We Cannot Match?
              </h2>
              <p className="lp-section-sub">
                Not every persistent thermal source has a confirmed facility
                association in the available infrastructure data. The system
                maintains a separate layer for these sources.
              </p>
              <ul className="lp-unknown-rules">
                <li className="lp-unknown-rule">
                  <span className="lp-unknown-rule-icon">○</span>
                  <span className="lp-unknown-rule-text">
                    <strong>Not called "unregistered" or "illegal"</strong> —
                    absence of OSM data does not imply illegal operation.
                  </span>
                </li>
                <li className="lp-unknown-rule">
                  <span className="lp-unknown-rule-icon">○</span>
                  <span className="lp-unknown-rule-text">
                    Classified as <strong>persistent unmatched thermal sources</strong>{" "}
                    when recurring observations are detected at the same location.
                  </span>
                </li>
                <li className="lp-unknown-rule">
                  <span className="lp-unknown-rule-icon">○</span>
                  <span className="lp-unknown-rule-text">
                    Evidence is limited by available contextual data.{" "}
                    <strong>Requires human verification.</strong>
                  </span>
                </li>
                <li className="lp-unknown-rule">
                  <span className="lp-unknown-rule-icon">○</span>
                  <span className="lp-unknown-rule-text">
                    Thoothukudi pilot: 15 persistent unmatched sources identified.
                  </span>
                </li>
              </ul>
            </div>
            <div className="lp-unknown-flow">
              {[
                "Persistent unmatched thermal detections",
                "Repeated observations at same location",
                "No confirmed facility association in OSM",
                "Contextual evidence may be limited",
                "Flagged for human verification",
              ].map((txt, i) => (
                <div key={i}>
                  <div className="lp-unknown-flow-item">
                    <div className="lp-unknown-flow-icon" />
                    <div className="lp-unknown-flow-text">{txt}</div>
                  </div>
                  {i < 4 && (
                    <div className="lp-pipeline-arrow" style={{ margin: "2px 0 2px 28px" }}>↓</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ---- EVIDENCE TRAIL ---- */}
      <hr className="lp-section-divider" />
      <div className="lp-section-alt">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Evidence System</div>
          <h2 className="lp-section-heading">
            Every Investigation Candidate Comes With an Evidence Trail
          </h2>
          <p className="lp-section-sub">
            Six evidence categories are synthesized into every investigation report.
          </p>
          <div className="lp-evidence-grid">
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-thermal">Thermal</div>
              {["FRP (Fire Radiative Power)", "Detection count", "Acquisition metadata"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-infra">Infrastructure</div>
              {["OSM industrial association", "Facility intersection", "Proximity evidence"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-land">Land Cover</div>
              {["ESA WorldCover classification", "Contextual land use", "Secondary evidence layer"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-hist">Historical</div>
              {["Baseline FRP (mean / P90 / P95)", "Activity frequency", "Persistence pattern"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-spatial">Spatial</div>
              {["Historical activity footprint", "Current activity radius", "Centroid shift"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
            <div className="lp-evidence-card">
              <div className="lp-evidence-category lp-ev-decision">Decision</div>
              {["Behaviour state", "Evidence quality", "Investigation priority"].map(i => (
                <div className="lp-evidence-item" key={i}>{i}</div>
              ))}
            </div>
          </div>
          <div className="lp-evidence-closing">
            "Every conclusion should be traceable to evidence."
          </div>
        </div>
      </div>

      {/* ---- TECHNOLOGY — dark section ---- */}
      <div className="lp-section-dark" id="technology">
        <div className="lp-section">
          <div className="lp-section-eyebrow-dark">Technology</div>
          <h2 className="lp-section-heading-dark">Built on Open Geospatial Intelligence</h2>
          <p className="lp-section-sub-dark">
            Using NASA FIRMS data, open geospatial infrastructure and open-source tools.
          </p>
          <div className="lp-tech-grid">
            {[
              { name: "NASA FIRMS",        role: "Satellite thermal anomaly observations (VIIRS / MODIS)" },
              { name: "OpenStreetMap",     role: "Industrial infrastructure context and facility data" },
              { name: "ESA WorldCover",    role: "10 m land-cover classification for contextual evidence" },
              { name: "MapLibre GL",       role: "Interactive geospatial visualization" },
              { name: "Python + FastAPI",  role: "Data processing and intelligence backend" },
              { name: "React",             role: "Interactive intelligence dashboard" },
            ].map(({ name, role }) => (
              <div className="lp-tech-card" key={name}>
                <div className="lp-tech-name">{name}</div>
                <div className="lp-tech-role">{role}</div>
              </div>
            ))}
          </div>
          <div className="lp-tech-attribution">
            Data sources used under their respective open licences. No official partnership
            or endorsement by NASA, OpenStreetMap Foundation or ESA is implied or claimed.
          </div>
        </div>
      </div>

      {/* ---- LIMITATIONS ---- */}
      <hr className="lp-section-divider" />
      <div id="limitations">
        <div className="lp-section">
          <div className="lp-section-eyebrow">Responsible Interpretation</div>
          <div className="lp-limitations-grid">
            <div>
              <h2 className="lp-section-heading">
                Designed for Decision Support, Not Automated Accusation
              </h2>
              <div className="lp-strong-statement">
                "The system assists investigators.<br />It does not replace them."
              </div>
            </div>
            <ul className="lp-limitations-list">
              {[
                "FIRMS observations are satellite thermal anomalies, not exact fire boundaries.",
                "Industrial association is contextual evidence based on mapped infrastructure proximity.",
                "Land cover is secondary contextual evidence.",
                "Unknown/unmatched does not mean illegal or unregistered.",
                "Satellite observations can be affected by viewing geometry, cloud cover and data availability.",
                "Historical baselines depend on the quantity of available observations.",
                "The system produces investigation candidates for human review — not incident confirmations.",
              ].map(item => (
                <li className="lp-limitations-item" key={item}>
                  <span className="lp-limitations-icon">○</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* ---- FINAL CTA — dark ---- */}
      <section className="lp-cta-section">
        <h2 className="lp-cta-heading">
          Turn Thermal Observations Into Actionable Intelligence
        </h2>
        <p className="lp-cta-sub">
          Explore industrial-associated thermal activity, historical site behaviour
          and evidence-backed investigation candidates through the Thermal
          Intelligence dashboard.
        </p>
        <div className="lp-cta-actions">
          <button className="lp-btn-primary-dark" onClick={goDashboard}>
            Open Thermal Intelligence Dashboard
          </button>
          <button className="lp-btn-secondary-dark" onClick={() => scrollTo("how-it-works")}>
            Explore How It Works ↓
          </button>
        </div>
      </section>

      {/* ---- FOOTER ---- */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div>
            <div className="lp-footer-brand">SIH26162 — Industrial Thermal Intelligence</div>
            <div className="lp-footer-tagline">
              Evidence-backed geospatial intelligence for industrial thermal monitoring.
            </div>
          </div>
          <div className="lp-footer-links">
            <button className="lp-footer-link" onClick={goDashboard}>Dashboard</button>
            <button className="lp-footer-link" onClick={() => scrollTo("how-it-works")}>How It Works</button>
            <button className="lp-footer-link" onClick={() => scrollTo("technology")}>Technology</button>
            <button className="lp-footer-link" onClick={() => scrollTo("limitations")}>Limitations</button>
          </div>
        </div>
        <div className="lp-footer-attr">
          Thermal observation data: NASA FIRMS ·
          Infrastructure data: © OpenStreetMap contributors ·
          Land cover: ESA WorldCover 2021 ·
          No endorsement by NASA, OSM Foundation or ESA is implied or claimed.
        </div>
      </footer>

    </div>
  );
}
