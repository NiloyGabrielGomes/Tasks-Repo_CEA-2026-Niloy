import React, { useState, useEffect } from "react";
import { teamsAPI } from "../services/api";
export default function TeamParticipationView({
  teamName = null,
  date = null,
  isAdmin = false,
}) {
  const [data, setData] = useState(null);
  const [allTeams, setAllTeams] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const targetDate = date || new Date().toISOString().slice(0, 10);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (teamName) {
          const res = await teamsAPI.getTeamParticipation(teamName, targetDate);
          setData(res.data);
          setAllTeams(null);
        } else if (isAdmin) {
          // Fetch all teams
          const res = await teamsAPI.getAllTeamParticipation(targetDate);
          setAllTeams(res.data.teams);
          setData(null);
        } else {
          // Fetch current user's team
          const res = await teamsAPI.getMyTeamParticipation(targetDate);
          setData(res.data);
          setAllTeams(null);
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load team participation");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [teamName, targetDate, isAdmin]);

  if (loading) {
    return <div className="team-participation-loading">Loading team participation…</div>;
  }

  if (error) {
    return <div className="team-participation-error">⚠️ {error}</div>;
  }

  const renderTeamTable = (teamData) => {
    const { team, members, total_members } = teamData;
    if (!members || members.length === 0) {
      return (
        <div key={team} className="team-participation-section">
          <h4>{team} ({total_members} members)</h4>
          <p>No data for this date.</p>
        </div>
      );
    }

    const mealNames = [
      ...new Set(members.flatMap((m) => Object.keys(m.meals || {}))),
    ].sort();

    return (
      <div key={team} className="team-participation-section" style={{ marginBottom: "1.5rem" }}>
        <h4 style={{ margin: "0 0 0.5rem" }}>
          {team}{" "}
          <span style={{ color: "#64748b", fontWeight: 400, fontSize: "0.85rem" }}>
            ({total_members} members)
          </span>
        </h4>
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "0.9rem",
            }}
          >
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Location</th>
                {mealNames.map((meal) => (
                  <th key={meal} style={thStyle}>
                    {meal.charAt(0).toUpperCase() + meal.slice(1)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.user_id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={tdStyle}>
                    <span style={{ fontWeight: 500 }}>{member.user_name}</span>
                    <br />
                    <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                      {member.email}
                    </span>
                  </td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "4px",
                        fontSize: "0.8rem",
                        fontWeight: 500,
                        background:
                          member.work_location === "WFH" ? "#fef3c7" : "#dcfce7",
                        color:
                          member.work_location === "WFH" ? "#92400e" : "#166534",
                      }}
                    >
                      {member.work_location}
                    </span>
                  </td>
                  {mealNames.map((meal) => {
                    const isIn = member.meals?.[meal];
                    return (
                      <td key={meal} style={{ ...tdStyle, textAlign: "center" }}>
                        <span
                          style={{
                            color: isIn ? "#16a34a" : "#dc2626",
                            fontWeight: 600,
                          }}
                        >
                          {isIn ? "✓" : "✗"}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (allTeams) {
    return (
      <div className="team-participation-view">
        <h3 style={{ marginBottom: "1rem" }}>All Teams — {targetDate}</h3>
        {allTeams.map((t) => renderTeamTable(t))}
      </div>
    );
  }

  if (data) {
    return (
      <div className="team-participation-view">
        {renderTeamTable(data)}
      </div>
    );
  }

  return null;
}

// ── Inline styles ──────────────────────────────────────────────

const thStyle = {
  textAlign: "left",
  padding: "0.5rem 0.75rem",
  fontWeight: 600,
  color: "#475569",
  fontSize: "0.8rem",
  textTransform: "uppercase",
  letterSpacing: "0.025em",
};

const tdStyle = {
  padding: "0.5rem 0.75rem",
  color: "#334155",
};
