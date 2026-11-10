"use client";

import { useId, useState } from "react";
import { ArrowUpRight, CheckCircle, LockSimple, Key } from "@phosphor-icons/react";
import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { accessTasks, evaluateAccess, type AccessTaskId } from "@/lib/clutch-access";
import "@/styles/clutch-access.css";

type Props = { productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string; embedded?: boolean };

export default function ClutchAccessDemo({ productName, website, logoUrl, secondaryLogoUrl, embedded }: Props) {
  const { locale, t } = useSiteLocale();
  const lang = locale === "en-US" ? "en" : "zh";
  const [taskId, setTaskId] = useState<AccessTaskId>("debug");
  const [requestId, setRequestId] = useState("config");
  const [grant, setGrant] = useState<AccessTaskId | null>(null);
  const id = useId();
  const task = accessTasks[taskId];
  const request = task.requests.find(item => item.id === requestId)!;
  const result = evaluateAccess(taskId, requestId, grant);
  const StatusIcon = result.decision === "allowed" ? CheckCircle : result.decision === "approval" ? Key : LockSimple;
  const status = result.decision === "allowed" ? t("允许", "Allowed") : result.decision === "approval" ? t("需要授权", "Authorization required") : t("拒绝", "Denied");

  function changeTask(next: AccessTaskId) {
    setTaskId(next);
    setRequestId(accessTasks[next].requests[0].id);
    setGrant(null);
  }

  return <div className={`experience-shell experience-focus clutch-access${embedded ? " experience-focus--embedded" : ""}`}>
    <header className="focus-header">
      {!embedded && <div className="focus-product"><SmartLogo className="demo-product-logo" name={productName} website={website}
        logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} trustPrimaryLogo size={30} /><h3>{productName}</h3></div>}
      <h2 className="focus-promise">{t("让 AI 完成任务，哪些访问该开放？", "Which access does the assistant need to finish its task?")}</h2>
      <p className="clutch-disclosure">{t("本地规则模拟 · 虚构数据 · 未调用 Clutch 或公司系统", "Local rules simulation · Fictional data · No Clutch or company systems connected")}</p>
    </header>
    <div className="clutch-workspace">
      <div className="clutch-controls">
        <label className="clutch-task" htmlFor={id + "-task"}>{t("AI 正在做什么", "Assistant's task")}
          <select id={id + "-task"} value={taskId} onChange={event => changeTask(event.target.value as AccessTaskId)}>
            {Object.values(accessTasks).map(item => <option key={item.id} value={item.id}>{item.label[lang]}</option>)}
          </select>
        </label>
        <p className="clutch-scope">{task.scope[lang]}</p>
        <fieldset className="clutch-requests"><legend>{t("它请求访问…", "It requests…")}</legend>
          {task.requests.map(item => <label key={item.id} className={item.id === requestId ? "is-selected" : undefined}>
            <input type="radio" name={id + "-request"} value={item.id} checked={item.id === requestId} onChange={() => setRequestId(item.id)} />
            <span>{item.label[lang]}</span>
          </label>)}
        </fieldset>
        {(request.decision === "approval" || grant === taskId) && <label className="clutch-grant">
          <input type="checkbox" checked={grant === taskId} onChange={event => setGrant(event.target.checked ? taskId : null)} />
          <span>{task.grant[lang]}</span>
        </label>}
      </div>
      <section className="clutch-result" aria-live="polite" aria-atomic="true" data-decision={result.decision}>
        <h3><StatusIcon size={22} aria-hidden="true" />{status}</h3>
        <p>{result.reason[lang]}</p>
        <h4>{t("AI 会拿到什么", "What the assistant receives")}</h4>
        <pre>{result.content[lang]}</pre>
      </section>
    </div>
    <footer className="clutch-footer">
      <details><summary>{t("示例规则与产品资料", "Example rules & product sources")}</summary>
        <p>{t("这里演示按任务限制访问。凭证由连接层代用是本示例的设计，不代表已验证 Clutch 的内部实现。", "This illustrates task-scoped access. Credential use through a connection layer is this example's design, not a verified description of Clutch's implementation.")}</p>
        <a href="https://www.clutch.security/agentic-ai/agent-guardrails" target="_blank" rel="noopener noreferrer">{t("官方：智能体访问控制", "Official: agent guardrails")} <ArrowUpRight size={14} /></a>
        <a href="https://www.clutch.security/use-cases/least-privilege-enforcement" target="_blank" rel="noopener noreferrer">{t("官方：最小权限", "Official: least privilege")} <ArrowUpRight size={14} /></a>
      </details>
      <a href="https://www.clutch.security/" target="_blank" rel="noopener noreferrer">{t("前往官方产品", "Visit the official product")} <ArrowUpRight size={16} /></a>
    </footer>
  </div>;
}
