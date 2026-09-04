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

  const queue = [...investigations]
    .sort(
      (a, b) =>
        (priorityOrder[a.investigation_priority] ?? 9) -
        (priorityOrder[b.investigation_priority] ?? 9) ||
        Number(b.behavior_score ?? 0) -
          Number(a.behavior_score ?? 0)
    );

  return (
    <section className="investigation-section">
      <div className="investigation-header">
        <div>
          <h2>Investigation Queue</h2>
          <p>
            Evidence-backed cases prioritized for human review.
          </p>
        </div>

        <div className="queue-count">
          {queue.length} cases
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="queue-empty">
          No medium or high priority cases.
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
                        item.investigation_priority ===
                        "HIGH"
                          ? "priority-high"
                          : "priority-medium"
                      }`}
                    >
                      {item.investigation_priority}
                    </span>
                  </td>

                  <td>
                    <div className="facility-name">
                      {item.facility_name ??
                        item.name ??
                        "Unknown source"}
                    </div>

                    <div className="facility-source">
                      {item.source_class ??
                        item.source_class_v2 ??
                        "UNKNOWN"}
                    </div>
                  </td>

                  <td>
                    {item.acq_date ?? "—"}
                  </td>

                  <td>
                    <span
                      className={`behavior-badge ${
                        item.behavior_state ===
                        "UNUSUAL"
                          ? "behavior-unusual"
                          : "behavior-watch"
                      }`}
                    >
                      {item.behavior_state ??
                        "—"}
                    </span>
                  </td>

                  <td className="score-cell">
                    {item.behavior_score !==
                    null &&
                    item.behavior_score !==
                      undefined
                      ? Number(
                          item.behavior_score
                        ).toFixed(1)
                      : "—"}
                  </td>

                  <td>
                    {item.max_frp_mw !== null &&
                    item.max_frp_mw !== undefined
                      ? `${Number(
                          item.max_frp_mw
                        ).toFixed(2)} MW`
                      : item.frp !== null &&
                        item.frp !== undefined
                      ? `${Number(
                          item.frp
                        ).toFixed(2)} MW`
                      : "—"}
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