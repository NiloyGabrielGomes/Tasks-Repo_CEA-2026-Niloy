import { useState, useEffect, useRef, useCallback } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

 // Custom hook that opens an SSE connection to the headcount stream
 
export default function useHeadcountStream(date = null) {
  const [headcount, setHeadcount] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    // Clean up any previous connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Not authenticated");
      setIsConnected(false);
      return;
    }

    let url = `${API_URL}/api/stream/headcount?token=${encodeURIComponent(token)}`;
    if (date) {
      url += `&date=${encodeURIComponent(date)}`;
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;

    // ── Headcount event ───────────────────────────────────────
    es.addEventListener("headcount", (e) => {
      try {
        const data = JSON.parse(e.data);
        setHeadcount(data);
        setError(null);
        setIsConnected(true);
      } catch (parseErr) {
        console.error("Failed to parse headcount SSE data:", parseErr);
      }
    });

    es.addEventListener("heartbeat", () => {
      setIsConnected(true);
    });

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    es.onerror = () => {
      setIsConnected(false);
      es.close();
      eventSourceRef.current = null;

      // Auto-reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.info("SSE reconnecting…");
        connect();
      }, 5000);
    };
  }, [date]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connect]);

  return { headcount, isConnected, error };
}