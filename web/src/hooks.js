import { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";

// Fetches once (or when `key` changes) and reports errors.
export function useFetch(load, onError, key = "") {
  const [data, setData] = useState(null);
  useEffect(() => {
    let alive = true;
    load()
      .then((d) => alive && setData(d))
      .catch(onError);
    return () => {
      alive = false;
    };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return data;
}

// A live session on the server: fresh world, memory and agent; questions stream steps back.
export function useLiveSession(scenarioId, level, onError) {
  const [session, setSession] = useState(null);
  const [busy, setBusy] = useState(false);

  const restart = useCallback(() => {
    if (!scenarioId) return;
    api
      .newSession(scenarioId, level)
      .then((s) => setSession({ id: s.session, scenario: s.scenario, frames: s.frames }))
      .catch(onError);
  }, [scenarioId, level, onError]);

  useEffect(restart, [restart]);

  const ask = useCallback(
    async (question) => {
      if (!session || busy) return;
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
    [session, busy, onError]
  );

  return { session, busy, restart, ask };
}

// The selected step of a run: follows the newest step until the user picks an earlier one.
// Arrow keys step, space plays.
export function usePlayer(count, { followByDefault = true } = {}) {
  const [cursor, setCursor] = useState(0);
  const [follow, setFollow] = useState(followByDefault);
  const [playing, setPlaying] = useState(false);
  const last = Math.max(0, count - 1);
  const at = Math.min(cursor, last);

  useEffect(() => {
    if (follow) setCursor(last);
  }, [last, follow]);

  const go = useCallback(
    (i) => {
      const next = Math.max(0, Math.min(last, i));
      setCursor(next);
      setFollow(next >= last && followByDefault);
    },
    [last, followByDefault]
  );

  useEffect(() => {
    if (!playing) return undefined;
    if (at >= last) {
      setPlaying(false);
      return undefined;
    }
    const t = setTimeout(() => setCursor(at + 1), 1000);
    return () => clearTimeout(t);
  }, [playing, at, last]);

  useEffect(() => {
    const onKey = (e) => {
      if (["TEXTAREA", "INPUT", "SELECT"].includes(e.target.tagName)) return;
      if (e.key === "ArrowRight") go(at + 1);
      if (e.key === "ArrowLeft") go(at - 1);
      if (e.key === " ") {
        e.preventDefault();
        setPlaying((p) => !p);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [at, go]);

  const togglePlay = () => {
    if (!playing && at >= last) setCursor(0);
    setFollow(false);
    setPlaying((p) => !p);
  };
  const reset = () => {
    setCursor(0);
    setPlaying(false);
    setFollow(followByDefault);
  };

  return { at, follow, setFollow, playing, togglePlay, go, reset };
}
