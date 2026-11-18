import { useCallback, useState } from "react";
import { X } from "lucide-react";
import Rail from "./components/shell/Rail.jsx";
import OperationsPage from "./pages/OperationsPage.jsx";
import ReplayPage from "./pages/ReplayPage.jsx";
import { useFetch } from "./hooks.js";
import * as api from "./api.js";

// A link like #replay=logs/<run>/<scenario>_run1.json&step=7 opens that moment of a logged run.
const link = Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)));

export default function App() {
  const [page, setPage] = useState(link.replay ? "replay" : "operations");
  const [error, setError] = useState("");
  const onError = useCallback((e) => setError(e?.message || String(e)), []);
  const config = useFetch(api.getConfig, onError);
  const scenarios = useFetch(api.getScenarios, onError) || [];

  return (
    <div className="shell">
      <Rail page={page} onPage={setPage} />
      <main className="main">
        {error && (
          <div className="error-bar" role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => setError("")} aria-label="Dismiss">
              <X size={14} />
            </button>
          </div>
        )}
        {/* Kept mounted so a conversation survives a look at a replay. */}
        <div hidden={page !== "operations"} className="page-slot">
          <OperationsPage config={config} scenarios={scenarios} onError={onError} />
        </div>
        {page === "replay" && <ReplayPage onError={onError} initialFile={link.replay} initialStep={Number(link.step) || 0} />}
      </main>
    </div>
  );
}
