import "./SummaryCards.css";

function SummaryCards({ summary }) {
  if (!summary) {
    return (
      <div className="summary-loading">
        Loading intelligence...
      </div>
    );
  }

  return (
    <div className="summary-grid">

      <div className="summary-card">
        <div className="summary-label">
          THERMAL EVENTS
        </div>

        <div className="summary-value">
          {summary.thermal_observations ?? 0}
        </div>
      </div>


      <div className="summary-card">
        <div className="summary-label">
          FACILITY DAYS
        </div>

        <div className="summary-value">
          {summary.facility_days ?? 0}
        </div>
      </div>


      <div className="summary-card">
        <div className="summary-label">
          FACILITIES
        </div>

        <div className="summary-value">
          {summary.facilities ?? 0}
        </div>
      </div>


      <div className="summary-card priority-card">
        <div className="summary-label">
          HIGH PRIORITY
        </div>

        <div className="summary-value">
          {summary.high_priority ?? 0}
        </div>
      </div>

    </div>
  );
}

export default SummaryCards;