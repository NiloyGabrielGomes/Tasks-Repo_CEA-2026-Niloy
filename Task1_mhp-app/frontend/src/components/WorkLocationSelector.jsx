import React, { useState, useEffect } from "react";
import { workLocationsAPI } from "../services/api";
export default function WorkLocationSelector({
  date = null,
  onChange = null,
  disabled = false,
}) {
  const [location, setLocation] = useState("Office");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const targetDate = date || new Date().toISOString().slice(0, 10);

  // Fetch current location on mount / date change
  useEffect(() => {
    const fetchLocation = async () => {
      try {
        const res = await workLocationsAPI.getMine(targetDate);
        if (res.data?.location) {
          setLocation(res.data.location);
        }
      } catch (err) {
        setLocation("Office");
      } finally {
        setLoaded(true);
      }
    };
    fetchLocation();
  }, [targetDate]);

  const handleChange = async (newLocation) => {
    if (newLocation === location || saving || disabled) return;

    setSaving(true);
    setError(null);
    try {
      await workLocationsAPI.set(targetDate, newLocation);
      setLocation(newLocation);
      if (onChange) onChange(newLocation);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update work location");
    } finally {
      setSaving(false);
    }
  };

  if (!loaded) {
    return (
      <div style={containerStyle}>
        <span style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
          Loading location…
        </span>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <label
        style={{
          fontSize: "0.85rem",
          fontWeight: 600,
          color: "#475569",
          marginBottom: "0.35rem",
          display: "block",
        }}
      >
        Work Location — {targetDate}
      </label>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          onClick={() => handleChange("Office")}
          disabled={disabled || saving}
          style={{
            ...btnStyle,
            ...(location === "Office" ? activeOfficeStyle : inactiveStyle),
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          🏢 Office
        </button>

        <button
          onClick={() => handleChange("WFH")}
          disabled={disabled || saving}
          style={{
            ...btnStyle,
            ...(location === "WFH" ? activeWfhStyle : inactiveStyle),
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          🏠 WFH
        </button>
      </div>

      {saving && (
        <span style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.25rem" }}>
          Saving…
        </span>
      )}
      {error && (
        <span style={{ fontSize: "0.8rem", color: "#dc2626", marginTop: "0.25rem" }}>
          {error}
        </span>
      )}
    </div>
  );
}

// ── Inline Styles ──────────────────────────────────────────────

const containerStyle = {
  padding: "0.75rem 1rem",
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: "8px",
  marginBottom: "1rem",
};

const btnStyle = {
  padding: "0.45rem 1rem",
  borderRadius: "6px",
  border: "2px solid transparent",
  fontSize: "0.9rem",
  fontWeight: 500,
  transition: "all 0.15s",
};

const activeOfficeStyle = {
  background: "#dcfce7",
  color: "#166534",
  borderColor: "#22c55e",
};

const activeWfhStyle = {
  background: "#fef3c7",
  color: "#92400e",
  borderColor: "#f59e0b",
};

const inactiveStyle = {
  background: "#f8fafc",
  color: "#64748b",
  borderColor: "#e2e8f0",
};
