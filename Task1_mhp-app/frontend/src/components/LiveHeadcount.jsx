import React from "react";
import useHeadcountStream from "../hooks/useHeadcountStream";
import "../css/LiveHeadCount.css";

export default function LiveHeadCount({ date = null, showTeams = false }) {
  const { headcount, isConnected, error } = useHeadcountStream(date);

  // ── Loading state ────────────────────────────────────────────
  if (!headcount && !error) {
    return (
      <div className="live-headcount live-headcount--loading">
        <span className="live-headcount__spinner" />
        Loading headcount…
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────
  if (error) {
    return (
      <div className="live-headcount live-headcount--error">
        ⚠️ {error}
      </div>
    );
  }

  const { meals, total_users, total_participating, timestamp } = headcount;
  const mealNames = Object.keys(meals || {});

  return (
    <div className="live-headcount">
      {/* Connection indicator */}
      <div className="live-headcount__header">
        <h3>
          Live Headcount
          <span
            className={`live-headcount__dot ${
              isConnected ? "live-headcount__dot--connected" : "live-headcount__dot--disconnected"
            }`}
            title={isConnected ? "Connected" : "Disconnected — reconnecting…"}
          />
        </h3>
        <span className="live-headcount__date">
          {headcount.date}
        </span>
      </div>

      {/* Summary bar */}
      <div className="live-headcount__summary">
        <span>
          <strong>{total_participating}</strong> / {total_users} participating
        </span>
        {timestamp && (
          <span className="live-headcount__timestamp">
            Last update: {new Date(timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Per-meal table */}
      <table className="live-headcount__table">
        <thead>
          <tr>
            <th>Meal</th>
            <th>Opted In</th>
            <th>Opted Out</th>
            <th>Office</th>
            <th>WFH</th>
          </tr>
        </thead>
        <tbody>
          {mealNames.map((meal) => {
            const m = meals[meal];
            return (
              <tr key={meal}>
                <td className="live-headcount__meal-name">
                  {meal.charAt(0).toUpperCase() + meal.slice(1)}
                </td>
                <td className="live-headcount__opted-in">{m.opted_in}</td>
                <td className="live-headcount__opted-out">{m.opted_out}</td>
                <td>{m.by_location?.Office ?? 0}</td>
                <td>{m.by_location?.WFH ?? 0}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Per-team breakdown */}
      {showTeams && mealNames.length > 0 && (
        <div className="live-headcount__teams">
          <h4>Per-Team Breakdown</h4>
          <table className="live-headcount__table">
            <thead>
              <tr>
                <th>Team</th>
                {mealNames.map((meal) => (
                  <th key={meal}>
                    {meal.charAt(0).toUpperCase() + meal.slice(1)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ...new Set(
                  mealNames.flatMap((meal) =>
                    Object.keys(meals[meal].by_team || {})
                  )
                ),
              ]
                .sort()
                .map((team) => (
                  <tr key={team}>
                    <td>{team}</td>
                    {mealNames.map((meal) => (
                      <td key={meal}>
                        {meals[meal].by_team?.[team] ?? 0}
                      </td>
                    ))}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}