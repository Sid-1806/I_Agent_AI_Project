import { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";

// A live session: fresh world, memory and agent on the server; questions stream steps back.
export function useLiveSession(onError) {
  const [scenarios, setScenarios] = useState([]);
  const [scenarioId, setScenarioId] = useState("A1_route_blocked");
  const [level, setLevel] = useState("full");
  const [session, setSession] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getScenarios().then(setScenarios).catch(onError);
  }, [onError]);

  const restart = useCallback(() => {
    api
      .newSession(scenarioId, level)
      .then((s) => setSession({ id: s.session, scenario: s.scenario, frames: s.frames }))
      .catch(onError);
  }, [scenarioId, level, onError]);

  useEffect(() => {
    if (scenarios.length) restart();
  }, [scenarios.length, restart]);

  const ask = useCallback(
    async (question) => {
      if (!session) return;
      setBusy(true);
      try {
        await api.ask(session.id, question, (ev) => {
          if (ev.event === "frame") setSession((s) => ({ ...s, frames: [...s.frames, ev.frame] }));
          if (ev.event === "error") onError(new Error(ev.message));
        });
      } catch (e) {
        onError(e);
      } finally {
        setBusy(false);
      }
    },
    [session, onError]
  );

  return { scenarios, scenarioId, setScenarioId, level, setLevel, session, busy, restart, ask };
}

// A logged evaluation run, rebuilt step by step by the server.
export function useReplay(active, onError) {
  const [runs, setRuns] = useState([]);
  const [file, setFile] = useState("");
  const [replay, setReplay] = useState(null);

  useEffect(() => {
    if (active && !runs.length) api.getRuns().then(setRuns).catch(onError);
  }, [active, runs.length, onError]);

  const open = useCallback(
    (f) => {
      setFile(f);
      setReplay(null);
      if (f) api.getReplay(f).then(setReplay).catch(onError);
    },
    [onError]
  );

  return { runs, file, replay, open };
}
