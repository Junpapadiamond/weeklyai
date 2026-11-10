import { useId, useState } from "react";
import { ArrowUp, ArrowDown, Download } from "@phosphor-icons/react";
import { downloadDemoText, itemNotes, type ArtifactItemsData, type ItemDraft } from "@/lib/demo-notes";

type Props = {
  items: ArtifactItemsData;
  ordered: boolean;
  lang: "zh" | "en";
  label: string;
  draft: ItemDraft;
  onEdit: (draft: ItemDraft) => void;
  sources?: string[];
  title?: string;
};

export function ArtifactItems({ items, ordered, lang, label, draft, onEdit, title, sources = [] }: Props) {
  const [editing, setEditing] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const id = useId();
  const List = ordered ? "ol" : "ul";
  const english = lang === "en";
  const order = draft.order ?? items.map((_, i) => i);
  const picked = draft.picked ?? [];

  function move(itemId: number, by: number) {
    const position = order.indexOf(itemId);
    if (position + by < 0 || position + by >= order.length) return;
    const next = [...order];
    next.splice(position, 1);
    next.splice(position + by, 0, itemId);
    onEdit({ ...draft, order: next });
    setAnnouncement(english ? `${items[itemId].label[lang]}: position ${position + by + 1} of ${items.length}`
      : `${items[itemId].label[lang]}：第 ${position + by + 1} 项，共 ${items.length} 项`);
  }

  function save() {
    downloadDemoText([title ?? label, english ? "Independent fictional example · Not vendor output" : "独立虚构示例 · 非原厂输出",
      label, ...itemNotes(items, ordered ? order : picked, lang), ...sources], "darkhorseradar-notes.txt");
  }

  return <div className={ordered ? "artifact-index artifact-index--sequence" : "artifact-index"}>
    <List className="experience-artifact__items" aria-label={label} id={id}>
      {order.map((itemId, i) => <li key={itemId}>
        {ordered ? <span className="artifact-index__ordinal" aria-hidden="true">{String(i + 1).padStart(2, "0")}</span> : null}
        <div className="artifact-index__text">
          <h4>{items[itemId].label[lang]}</h4>
          <p>{items[itemId].detail[lang]}</p>
          {editing ? <div className="artifact-index__item-tools">
            {ordered ? <>
              <button type="button" disabled={i === 0} aria-label={(english ? "Move earlier: " : "前移：") + items[itemId].label[lang]} onClick={() => move(itemId, -1)}><ArrowUp size={15} aria-hidden="true" />{english ? "Move earlier" : "前移"}</button>
              <button type="button" disabled={i === items.length - 1} aria-label={(english ? "Move later: " : "后移：") + items[itemId].label[lang]} onClick={() => move(itemId, 1)}><ArrowDown size={15} aria-hidden="true" />{english ? "Move later" : "后移"}</button>
            </> : <label>
              <input type="checkbox" checked={picked.includes(itemId)} aria-label={(english ? "Include in notes: " : "摘录：") + items[itemId].label[lang]}
                onChange={event => onEdit({ ...draft, picked: event.target.checked ? [...picked, itemId] : picked.filter(value => value !== itemId) })} />
              {english ? "Include in notes" : "加入摘录"}
            </label>}
          </div> : null}
        </div>
      </li>)}
    </List>
    <div className="artifact-index__tools">
      <button type="button" aria-expanded={editing} aria-controls={id} onClick={() => setEditing(value => !value)}>
        {editing ? (english ? "Done editing" : "完成整理") : ordered ? (english ? "Arrange sequence" : "调整顺序") : (english ? "Select notes" : "选择摘录")}
      </button>
      {editing ? <button type="button" disabled={!ordered && !picked.length} onClick={save}><Download size={15} aria-hidden="true" />
          {ordered ? (english ? "Save sequence" : "保存编排") : (english ? "Save notes" : "保存摘录") + (picked.length ? ` (${picked.length})` : "")}
      </button> : null}
    </div>
    <span role="status" className="artifact-index__status">{announcement}</span>
  </div>;
}
