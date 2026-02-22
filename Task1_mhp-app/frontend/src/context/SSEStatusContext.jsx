

import { createContext, useContext, useState, useCallback, useRef } from 'react';

// ── Contexts ──────────────────────────────────────────────────────────────────

const SSEStatusContext  = createContext(null);  // { status, lastEventAt, triggerReconnect }
const SSEPublishContext = createContext(null);  // { publish, reconnectSignal }

// ── Provider ──────────────────────────────────────────────────────────────────

export function SSEStatusProvider({ children }) {
  
  const [status, setStatus] = useState(null);
  const [lastEventAt, setLastEventAt] = useState(null);

  const [reconnectSignal, setReconnectSignal] = useState(0);

  const triggerReconnect = useCallback(() => {
    setStatus('connecting');
    setReconnectSignal((s) => s + 1);
  }, []);

  const publish = useCallback(({ status: s, lastEventAt: ts }) => {
    if (s !== undefined) setStatus(s);
    if (ts !== undefined) setLastEventAt(ts);
  }, []);

  return (
    <SSEStatusContext.Provider value={{ status, lastEventAt, triggerReconnect }}>
      <SSEPublishContext.Provider value={{ publish, reconnectSignal }}>
        {children}
      </SSEPublishContext.Provider>
    </SSEStatusContext.Provider>
  );
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useSSEStatus() {
  const ctx = useContext(SSEStatusContext);
  if (!ctx) throw new Error('useSSEStatus must be used inside SSEStatusProvider');
  return ctx;
}

/** Write SSE connection status — use inside useHeadcountStream. */
export function useSSEPublish() {
  const ctx = useContext(SSEPublishContext);
  if (!ctx) return { publish: () => {}, reconnectSignal: 0 };
  return ctx;
}
