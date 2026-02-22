import { useState, useEffect, useRef, useCallback } from "react";
import { sseAPI } from "../services/api";
import { useSSEPublish } from "../context/SSEStatusContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

 // Custom hook that opens an SSE connection to the headcount stream
 
export default function useHeadcountStream(date = null) {
  const [headcount, setHeadcount] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const activeRef = useRef(true);   // flipped to false on unmount / reconnect

  // Global SSE status publisher (feeds Navbar indicator)
  const { publish, reconnectSignal } = useSSEPublish();

  const connect = useCallback(() => {
    // Cancel any in-flight token fetch or reconnect timer from a previous call
    activeRef.current = false;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Create a new cancellation scope for this connection attempt
    activeRef.current = true;
    const myActive = activeRef; // captured reference

    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
      setError("Not authenticated");
      setIsConnected(false);
      publish({ status: 'disconnected' });
      return;
    }

    publish({ status: 'connecting' });

    // ── Fetch a short-lived SSE token, then open EventSource ─────────────
    sseAPI
      .getSseToken()
      .then(({ token }) => {
        if (!myActive.current) return;   // component unmounted or reconnect fired

        let url = `${API_URL}/api/stream/headcount?token=${encodeURIComponent(token)}`;
        if (date) url += `&date=${encodeURIComponent(date)}`;

        const es = new EventSource(url);
        eventSourceRef.current = es;

        // ── Headcount event ─────────────────────────────────────────────
        es.addEventListener("headcount", (e) => {
          if (!myActive.current) return;
          try {
            const data = JSON.parse(e.data);
            setHeadcount(data);
            setError(null);
            setIsConnected(true);
            publish({ status: 'connected', lastEventAt: new Date() });
          } catch (parseErr) {
            console.error("Failed to parse headcount SSE data:", parseErr);
          }
        });

        es.addEventListener("heartbeat", () => {
          if (myActive.current) {
            setIsConnected(true);
            publish({ status: 'connected', lastEventAt: new Date() });
          }
        });

        es.onopen = () => {
          if (!myActive.current) return;
          setIsConnected(true);
          setError(null);
          publish({ status: 'connected', lastEventAt: new Date() });
        };

        es.onerror = () => {
          if (!myActive.current) return;
          setIsConnected(false);
          publish({ status: 'disconnected' });
          es.close();
          eventSourceRef.current = null;

          // Auto-reconnect after 5 seconds (re-fetches a fresh SSE token)
          reconnectTimeoutRef.current = setTimeout(() => {
            console.info("SSE reconnecting…");
            connect();
          }, 5000);
        };
      })
      .catch((err) => {
        if (!myActive.current) return;
        console.error("Failed to obtain SSE token:", err);
        setError("Failed to connect to live updates");
        setIsConnected(false);
        publish({ status: 'disconnected' });

        // Retry after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      });
  }, [date, publish]);

  useEffect(() => {
    if (reconnectSignal > 0) connect();
  }, [reconnectSignal]);

  useEffect(() => {
    connect();

    return () => {
      activeRef.current = false;
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