"use client";

import { useMemo, useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import type { Datum, LocalizedText, Widget } from "@/lib/demo-schema";

/** Every widget reads text through this, so a missing locale degrades to the
 *  other language rather than to an empty panel. */
function useText() {
  const { locale } = useSiteLocale();
  return useMemo(
    () => (value: LocalizedText | undefined) =>
      !value ? "" : (locale === "en-US" ? value.en || value.zh : value.zh || value.en),
    [locale]
  );
}

/**
 * Renders a value together with where it came from. This is the labelling
 * contract made visible: a figure is either traceable to a source or carries an
 * "example" marker. There is no unmarked number anywhere in a demo.
 */
function DatumValue({ datum, evidence }: { datum: Datum; evidence: { claim: string; source_url: string }[] }) {
  const text = useText();
  const { t } = useSiteLocale();
  const source = datum.evidence_ref !== null ? evidence[datum.evidence_ref] : undefined;
  return (
    <span className="demo-datum">
      <span className="demo-datum__value">{text(datum.value)}</span>
      {datum.is_example ? (
        <span className="demo-tag demo-tag--example">{t("示例数据", "example")}</span>
      ) : source ? (
        <a className="demo-tag demo-tag--source" href={source.source_url} target="_blank" rel="noopener noreferrer"
           title={source.claim}>
          {t("来源", "source")}
        </a>
      ) : null}
      <span className="demo-datum__label">{text(datum.label)}</span>
    </span>
  );
}

function SplitCompare({ widget }: { widget: Extract<Widget, { type: "split_compare" }> }) {
  const text = useText();
  const { t } = useSiteLocale();
  return (
    <div className="demo-split">
      <div className="demo-split__input">
        <span className="demo-eyebrow">{t("同一个输入", "Same input")}</span>
        <code>{widget.input}</code>
      </div>
      <div className="demo-split__panes">
        {(["left", "right"] as const).map((side) => (
          <article key={side} className={`demo-pane demo-pane--${side}`}>
            <h4>{text(widget[side].title)}</h4>
            <p>{text(widget[side].body)}</p>
          </article>
        ))}
      </div>
      <p className="demo-takeaway">{text(widget.takeaway)}</p>
    </div>
  );
}

function QueryResponse({ widget }: { widget: Extract<Widget, { type: "query_response" }> }) {
  const text = useText();
  const { t } = useSiteLocale();
  const [active, setActive] = useState(0);
  const preset = widget.presets[Math.min(active, widget.presets.length - 1)];
  return (
    <div className="demo-query">
      <div className="demo-query__presets" role="tablist" aria-label={t("示例查询", "Example queries")}>
        {widget.presets.map((item, index) => (
          <button
            key={item.query}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={`demo-chip${index === active ? " is-active" : ""}`}
            onClick={() => setActive(index)}
          >
            {item.query}
          </button>
        ))}
      </div>
      <div className="demo-query__panel">
        <span className="demo-eyebrow">
          {widget.mode === "live" ? t("实时结果", "Live result") : t("预先记录的结果", "Recorded result")}
        </span>
        <p>{text(preset.response)}</p>
      </div>
    </div>
  );
}

function PipelineWidget({ widget }: { widget: Extract<Widget, { type: "pipeline" }> }) {
  const text = useText();
  const { t } = useSiteLocale();
  const [open, setOpen] = useState(0);
  return (
    <div className="demo-pipeline">
      <ol className="demo-pipeline__stages">
        {widget.stages.map((stage, index) => (
          <li key={index}>
            <button
              type="button"
              className={`demo-stage${index === open ? " is-active" : ""}`}
              onClick={() => setOpen(index)}
              aria-expanded={index === open}
            >
              <span className="demo-stage__n">{index + 1}</span>
              <span className="demo-stage__name">{text(stage.name)}</span>
            </button>
          </li>
        ))}
      </ol>
      <div className="demo-pipeline__detail">
        <div>
          <span className="demo-eyebrow">{t("输入", "In")}</span>
          <p>{text(widget.stages[open].input)}</p>
        </div>
        <div>
          <span className="demo-eyebrow">{t("输出", "Out")}</span>
          <p>{text(widget.stages[open].output)}</p>
        </div>
      </div>
    </div>
  );
}

function SpecMatrix({
  widget,
  evidence,
}: {
  widget: Extract<Widget, { type: "spec_matrix" }>;
  evidence: { claim: string; source_url: string }[];
}) {
  const text = useText();
  const columns = [widget.subject, ...widget.competitors];
  return (
    <div className="demo-matrix">
      <table>
        <thead>
          <tr>
            <th scope="col" />
            {columns.map((name, index) => (
              <th key={name} scope="col" className={index === 0 ? "is-subject" : undefined}>
                {name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {widget.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              <th scope="row">{text(row.spec)}</th>
              {row.values.map((datum, index) => (
                <td key={index} className={index === 0 ? "is-subject" : undefined}>
                  <DatumValue datum={datum} evidence={evidence} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScenarioBranch({ widget }: { widget: Extract<Widget, { type: "scenario_branch" }> }) {
  const text = useText();
  const { t } = useSiteLocale();
  const [active, setActive] = useState(0);
  const branch = widget.branches[Math.min(active, widget.branches.length - 1)];
  return (
    <div className="demo-branch">
      <div className="demo-branch__picks" role="tablist" aria-label={t("选择场景", "Pick a situation")}>
        {widget.branches.map((item, index) => (
          <button
            key={index}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={`demo-chip${index === active ? " is-active" : ""}`}
            onClick={() => setActive(index)}
          >
            {text(item.persona)}
          </button>
        ))}
      </div>
      <div className="demo-branch__card">
        <div>
          <span className="demo-eyebrow">{t("情境", "Situation")}</span>
          <p>{text(branch.situation)}</p>
        </div>
        <div>
          <span className="demo-eyebrow">{t("结果", "Outcome")}</span>
          <p>{text(branch.outcome)}</p>
        </div>
      </div>
    </div>
  );
}

function HotspotShot({ widget }: { widget: Extract<Widget, { type: "hotspot_shot" }> }) {
  const text = useText();
  const [active, setActive] = useState(0);
  return (
    <div className="demo-hotspot">
      <div className="demo-hotspot__frame">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={widget.shot_url} alt="" loading="lazy" decoding="async" />
        {widget.hotspots.map((spot, index) => (
          <button
            key={index}
            type="button"
            className={`demo-pin${index === active ? " is-active" : ""}`}
            style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
            onClick={() => setActive(index)}
            aria-label={text(spot.note)}
          >
            {index + 1}
          </button>
        ))}
      </div>
      <ol className="demo-hotspot__notes">
        {widget.hotspots.map((spot, index) => (
          <li key={index} className={index === active ? "is-active" : undefined}>
            <button type="button" onClick={() => setActive(index)}>
              <span className="demo-pin demo-pin--inline">{index + 1}</span>
              {text(spot.note)}
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

function ParamDial({
  widget,
  evidence,
}: {
  widget: Extract<Widget, { type: "param_dial" }>;
  evidence: { claim: string; source_url: string }[];
}) {
  const text = useText();
  const { t } = useSiteLocale();
  const [value, setValue] = useState(() => widget.min + (widget.max - widget.min) / 2);
  const position = (value - widget.min) / (widget.max - widget.min || 1);
  return (
    <div className="demo-dial">
      <label className="demo-dial__control">
        <span className="demo-eyebrow">{text(widget.param)}</span>
        <input
          type="range"
          min={widget.min}
          max={widget.max}
          step={widget.step}
          value={value}
          onChange={(event) => setValue(Number(event.currentTarget.value))}
        />
        <output>
          {Number.isInteger(value) ? value : value.toFixed(1)} {widget.unit}
        </output>
      </label>
      {/* The bar shows where the dial sits in its range. It is a position
          indicator, not a claim about a modelled quantity. */}
      <div className="demo-dial__track" aria-hidden="true">
        <span style={{ width: `${Math.round(position * 100)}%` }} />
      </div>
      <p className="demo-dial__note">{text(widget.formula_note)}</p>
      <ul className="demo-dial__outputs">
        {widget.outputs.map((datum, index) => (
          <li key={index}>
            <DatumValue datum={datum} evidence={evidence} />
          </li>
        ))}
      </ul>
      <p className="demo-dial__caveat">
        {t(
          "滑块用于说明变量之间的关系，不代表该产品的实际报价。",
          "The slider illustrates how the variables relate. It is not a quote for this product."
        )}
      </p>
    </div>
  );
}

function TranscriptWidget({ widget }: { widget: Extract<Widget, { type: "transcript" }> }) {
  const text = useText();
  const { t } = useSiteLocale();
  const [shown, setShown] = useState(2);
  const visible = widget.turns.slice(0, Math.max(2, shown));
  const remaining = widget.turns.length - visible.length;
  return (
    <div className="demo-transcript">
      <ol>
        {visible.map((turn, index) => (
          <li key={index} className={`demo-turn demo-turn--${turn.speaker}`}>
            <span className="demo-turn__who">{turn.speaker === "user" ? t("用户", "User") : t("产品", "Product")}</span>
            <p>{text(turn.text)}</p>
          </li>
        ))}
      </ol>
      {remaining > 0 ? (
        <button type="button" className="demo-more" onClick={() => setShown(shown + 2)}>
          {t(`继续（还有 ${remaining} 条）`, `Continue (${remaining} more)`)}
        </button>
      ) : null}
    </div>
  );
}

export function DemoWidget({
  widget,
  evidence,
}: {
  widget: Widget;
  evidence: { claim: string; source_url: string }[];
}) {
  switch (widget.type) {
    case "split_compare":
      return <SplitCompare widget={widget} />;
    case "query_response":
      return <QueryResponse widget={widget} />;
    case "pipeline":
      return <PipelineWidget widget={widget} />;
    case "spec_matrix":
      return <SpecMatrix widget={widget} evidence={evidence} />;
    case "scenario_branch":
      return <ScenarioBranch widget={widget} />;
    case "hotspot_shot":
      return <HotspotShot widget={widget} />;
    case "param_dial":
      return <ParamDial widget={widget} evidence={evidence} />;
    case "transcript":
      return <TranscriptWidget widget={widget} />;
    default:
      return null;
  }
}
