"use client";

import { useEffect, useId, useRef, useState, useSyncExternalStore } from "react";
import { HorseMark } from "./horse-mark";

type RadarEmblemProps = {
  animated?: boolean;
  pauseLabel?: string;
  resumeLabel?: string;
};

const motionPreference = "(prefers-reduced-motion: reduce)";
const reducedMotionSnapshot = () => window.matchMedia(motionPreference).matches;
const staticServerSnapshot = () => true;
function subscribeMotionPreference(onChange: () => void) {
  const query = window.matchMedia(motionPreference);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** Brand illustration only: the signals do not represent live product activity. */
export function RadarEmblem({
  animated = false,
  pauseLabel = "Pause radar animation",
  resumeLabel = "Resume radar animation",
}: RadarEmblemProps) {
  const gradientId = useId();
  const root = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  const [onScreen, setOnScreen] = useState(true);
  const reducedMotion = useSyncExternalStore(subscribeMotionPreference, reducedMotionSnapshot, staticServerSnapshot);
  const interactive = animated && !reducedMotion;

  useEffect(() => {
    if (!animated) return;
    let intersects = true;
    const update = () => setOnScreen(intersects && !document.hidden);
    const observer = typeof IntersectionObserver === "undefined" ? null : new IntersectionObserver(([entry]) => {
      intersects = entry.isIntersecting;
      update();
    });
    if (root.current) observer?.observe(root.current);
    document.addEventListener("visibilitychange", update);
    return () => {
      observer?.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, [animated]);

  return (
    <div ref={root} className={`radar-emblem${animated ? " radar-emblem--animated" : ""}`}
      data-running={interactive && !paused && onScreen} data-paused={paused}>
      <div className="radar-emblem__art" aria-hidden="true">
        <svg className="radar-emblem__grid" viewBox="0 0 360 300" fill="none" focusable="false">
          <defs>
            <linearGradient id={gradientId} x1="180" y1="22" x2="271" y2="60" gradientUnits="userSpaceOnUse">
              <stop stopColor="var(--hero-signal, var(--primary))" stopOpacity="0" />
              <stop offset="1" stopColor="var(--hero-signal, var(--primary))" stopOpacity=".24" />
            </linearGradient>
          </defs>
          <g className="radar-emblem__rings" stroke="currentColor" strokeWidth=".7">
            <circle cx="180" cy="150" r="142" strokeDasharray="1 9" />
            <circle cx="180" cy="150" r="128" />
            <circle cx="180" cy="150" r="94" />
            <circle cx="180" cy="150" r="56" strokeDasharray="2 5" />
            <path d="M180 7v286M32 150h296" strokeOpacity=".45" />
            <path d="M89 59l182 182M89 241 271 59" strokeOpacity=".2" />
          </g>
          <g className="radar-emblem__scan radar-emblem__motion">
            <path d="M180 150V22a128 128 0 0 1 90.51 37.49Z" fill={`url(#${gradientId})`} />
            <path d="m180 150 90.51-90.51" stroke="currentColor" strokeWidth="1.6" />
            <circle cx="270.51" cy="59.49" r="2.8" fill="currentColor" />
          </g>
          {[{ x: 271, y: 59 }, { x: 271, y: 241 }, { x: 52, y: 150 }].map(({ x, y }, index) => (
            <g key={index} className={`radar-emblem__signal radar-emblem__signal--${index + 1}`}>
              <circle cx={x} cy={y} r="3" fill="currentColor" opacity=".55" />
              <g transform={`translate(${x} ${y})`}>
                <circle className="radar-emblem__echo radar-emblem__motion" r="9" stroke="currentColor" strokeWidth="1.2" />
                <circle className="radar-emblem__hit radar-emblem__motion" r="4" fill="currentColor" />
              </g>
            </g>
          ))}
          <path className="radar-emblem__lock radar-emblem__motion" d="M254 52v-10h10m14 0h10v10m0 14v10h-10m-14 0h-10V66" stroke="currentColor" strokeWidth="1.1" />
        </svg>
      </div>
      {interactive ? <button type="button" className="radar-emblem__horse-control" onClick={() => setPaused(value => !value)}
        aria-label={paused ? resumeLabel : pauseLabel} title={paused ? resumeLabel : pauseLabel}>
        <HorseMark className="radar-emblem__horse" />
      </button> : <HorseMark className="radar-emblem__horse" />}
    </div>
  );
}
