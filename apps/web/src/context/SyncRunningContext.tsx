import React, { createContext, useContext, useState } from "react";

interface SyncRunningContextValue {
  syncRunning: boolean;
  setSyncRunning: (v: boolean) => void;
}

const SyncRunningContext = createContext<SyncRunningContextValue>({
  syncRunning: false,
  setSyncRunning: () => {},
});

export function SyncRunningProvider({ children }: { children: React.ReactNode }) {
  const [syncRunning, setSyncRunning] = useState(false);
  return (
    <SyncRunningContext.Provider value={{ syncRunning, setSyncRunning }}>
      {children}
    </SyncRunningContext.Provider>
  );
}

export function useSyncRunning() {
  return useContext(SyncRunningContext);
}
