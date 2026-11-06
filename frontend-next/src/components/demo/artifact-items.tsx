import { useId, useState } from "react";
import { ArrowLeft, ArrowRight, BookmarkSimple, Download, ListBullets } from "@phosphor-icons/react";
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
  const [active, setActive] = useState(draft.order?.[0] ?? 0);
  const id = useId();
  const List = ordered ? "ol" : "ul";
  const english = lang === "en";
  const order = draft.order ?? items.map((_, i) => i);
  const picked = draft.picked ?? [];
  const position = order.indexOf(active);
  const included = picked.includes(active);

  function move(by: number) {
    const next = [...order];
    next.splice(position, 1);
    next.splice(position + by, 0, active);
    onEdit({ ...draft, order: next });
  }

  function save() {
    downloadDemoText([title ?? label, english ? "Independent fictional example · Not vendor output" : "独立虚构示例 · 非原厂输出",
      label, ...itemNotes(items, ordered ? order : picked, lang), ...sources], "darkhorseradar-notes.txt");
  }

  return <div className={ordered ? "artifact-index artifact-index--sequence" : "artifact-index"}>
    <List className="experience-artifact__items" aria-label={label}>
      {order.map((itemId, i) => <li key={itemId}>
        <button type="button" aria-pressed={active === itemId} aria-controls={id} onClick={() => setActive(itemId)}>
          {ordered ? <span className="artifact-index__ordinal">{String(i + 1).padStart(2, "0")}</span>
            : picked.includes(itemId) ? <BookmarkSimple size={16} weight="fill" aria-label={english ? "In notes" : "已摘录"} /> : <ListBullets size={16} aria-hidden="true" />}
          <span>{items[itemId].label[lang]}</span>
        </button>
      </li>)}
    </List>
    <div className="artifact-index__detail" id={id}>
      <div aria-live="polite" aria-atomic="true">
        <h4>{items[active].label[lang]}</h4>
        <p>{items[active].detail[lang]}</p>
      </div>
      <div className="artifact-index__tools">
        {ordered ? <>
          <button type="button" disabled={position === 0} onClick={() => move(-1)}><ArrowLeft size={15} />{english ? "Move earlier" : "前移"}</button>
          <span role="status">{position + 1} / {items.length}</span>
          <button type="button" disabled={position === items.length - 1} onClick={() => move(1)}>{english ? "Move later" : "后移"}<ArrowRight size={15} /></button>
        </> : <button type="button" aria-pressed={included}
          onClick={() => onEdit({ ...draft, picked: included ? picked.filter(i => i !== active) : [...picked, active] })}>
          <BookmarkSimple size={15} weight={included ? "fill" : "regular"} />{english ? "Add to notes" : "摘录此项"}
        </button>}
        <button type="button" disabled={!ordered && !picked.length} onClick={save}><Download size={15} />
          {ordered ? (english ? "Save sequence" : "保存编排") : (english ? "Save notes" : "保存摘录") + (picked.length ? ` (${picked.length})` : "")}
        </button>
      </div>
    </div>
  </div>;
}
