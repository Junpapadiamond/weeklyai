import { HorseMark } from "./horse-mark";

export function RadarEmblem() {
  return (
    <div className="radar-emblem" aria-hidden="true">
      <svg className="radar-emblem__grid" viewBox="0 0 360 300" fill="none">
        <g stroke="currentColor" strokeWidth=".7">
          <circle cx="180" cy="150" r="128" />
          <circle cx="180" cy="150" r="94" />
          <circle cx="180" cy="150" r="56" strokeDasharray="2 5" />
          <path d="M180 7v286M32 150h296M89 59l182 182M89 241 271 59" />
          <path d="M30 32V20h12m276 12V20h-12M30 268v12h12m276-12v12h-12" />
        </g>
        <path d="m180 150 91-91" stroke="var(--primary)" strokeWidth="1.5" />
        <circle cx="271" cy="59" r="5" fill="var(--primary)" />
        <circle cx="271" cy="59" r="10" stroke="var(--primary)" strokeOpacity=".25" />
      </svg>
      <HorseMark className="radar-emblem__horse" />
      <span className="radar-emblem__label">LOOK CLOSER.</span>
      <span className="radar-emblem__coordinate">EARLY SIGNALS</span>
    </div>
  );
}
