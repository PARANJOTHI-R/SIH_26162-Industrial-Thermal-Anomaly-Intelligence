import "./InvestigationQueue.css";

function InvestigationQueue({
  investigations = [],
  onSelect,
}) {
  const priorityOrder = {
    HIGH: 0,
    MEDIUM: 1,
    LOW: 2,
  };

  // Only show candidates
  const candidates = investigations.filter((item) => {
    // 1. Strict boolean or string check if field exists
    if (item.is_investigation_candidate === true || String(item.is_investigation_candidate).toLowerCase() === "true") return true;
    if (item.is_investigation_candidate === false || String(item.is_investigation_candidate).toLowerCase() === "false") return false;
    
    // 2. Strict fallback logic if backend field is missing
    const behavior = String(item.behavior_state ?? item.behavior ?? "").trim().toUpperCase();
    const sourceClass = String(item.source_class ?? "").trim().toUpperCase();
    
    if (behavior === "NORMAL" || behavior === "INSUFFICIENT_HISTORY") return false;
    if (sourceClass === "AGRICULTURAL" || sourceClass === "FOREST_NATURAL") return false;
    if (sourceClass === "INDUSTRIAL_ASSOCIATED" && behavior === "NORMAL") return false;
    
    return behavior === "WATCH" || behavior === "UNUSUAL";
  });

  const queue = [...candidates].sort(
    (a, b) =>
      (priorityOrder[a.investigation_priority] ?? 9) -
      (priorityOrder[b.investigation_priority] ?? 9) ||
      Number(b.behavior_score ?? 0) - Number(a.behavior_score ?? 0)
  );

  const safeNumber = (val, maxDecimals = 1) => {
    const num = Number(val);
    return isNaN(num) ? "—" : num.toFixed(maxDecimals);
  };

  return (
    <section className="investigation-section">
      <div className="investigation-header">
        <div>
          <h2>Investigation Queue</h2>
          <p>
            Genuine human-review candidates: industrial-associated or persistent
            unmatched sources showing watch-level or unusual behaviour.
            Normal activity is excluded.
          </p>
        </div>

        <div className="queue-count">
          {queue.length} candidate{queue.length !== 1 ? "s" : ""}
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="queue-empty">
          No investigation candidates in this view.
          Normal and insufficient-evidence cases are not shown here.
        </div>
      ) : (
        <div className="queue-table-wrapper">
          <table className="queue-table">
            <thead>
              <tr>
                <th>Priority</th>
                <th>Facility / Source</th>
                <th>Date</th>
                <th>Behaviour</th>
                <th>Score</th>
                <th>Max FRP</th>
                <th>Evidence Quality</th>
              </tr>
            </thead>

            <tbody>
              {queue.map((item, index) => (
                <tr
                  key={`${item.facility_name}-${item.acq_date}-${index}`}
                  onClick={() => onSelect?.(item)}
                >
                  <td>
                    <span
                      className={`priority-badge ${
                        item.investigation_priority === "HIGH"
                          ? "priority-high"
                          : "priority-medium"
                      }`}
                    >
                      {item.investigation_priority}
                    </span>
                  </td>

                  <td>
                    <div className="facility-name">
                      {item.facility_name ?? item.name ?? "Unmatched source"}
                    </div>

                    <div className="facility-source">
                      {item.source_class === "INDUSTRIAL_ASSOCIATED"
                        ? "Industrial-associated"
                        : item.source_class === "UNKNOWN"
                        ? "Unmatched source"
                        : item.source_class_v2 ?? item.source_class ?? "UNKNOWN"}
                    </div>
                  </td>

                  <td>{item.acq_date ?? "—"}</td>

                  <td>
                    <span
                      className={`behavior-badge ${
                        item.behavior_state === "UNUSUAL"
                          ? "behavior-unusual"
                          : "behavior-watch"
                      }`}
                    >
                      {item.behavior_state ?? "—"}
                    </span>
                  </td>

                  <td className="score-cell">
                    {item.behavior_score !== null && item.behavior_score !== undefined
                      ? Number(item.behavior_score).toFixed(1)
                      : "—"}
                  </td>

                  <td>
                    <div className="frp-value">
                      Event peak: {safeNumber(item.max_frp_mw ?? item.frp, 1)} MW
                    </div>
                  </td>

                  <td>
                    <span
                      className={`quality-badge quality-${
                        item.evidence_quality?.toLowerCase() || "unknown"
                      }`}
                    >
                      {item.evidence_quality || "UNKNOWN"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default InvestigationQueue;