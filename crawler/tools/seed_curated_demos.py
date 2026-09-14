"""Rebuild the authored, source-backed starter experiences. Never modifies products."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.demo_contract import validate_experience
from app.services.demo_experiences import envelope
from app.services.product_service import ProductService


def c(zh, en):
    return {"zh": zh, "en": en}


def option(zh, en, output_zh, output_en):
    return {"label": c(zh, en), "output": c(output_zh, output_en)}


def step(index, title, instruction, options, widget="choice", **extra):
    return {"id": "step-" + str(index), "widget": widget, "title": c(*title),
            "instruction": c(*instruction), "options": options, **extra}


def starters():
    yield "Exa", "workflow", c("把一个问题，变成有依据的研究简报。", "Turn a question into an evidence-led brief."), c(
        "你正在寻找一家适合小团队的知识库工具。走一遍搜索、提取内容、筛选证据和交付简报的流程。公司与结果均为虚构示例。",
        "Find a knowledge tool for a small team. Search, extract content, review evidence and deliver a brief. Companies and results are fictional."), [
        step(1, ("选择搜索范围", "Choose a search scope"), ("搜索意图已经准备好了。你想先查哪一类资料？", "The search intent is ready. Which type of evidence matters first?"), [
            option("找产品：小团队的 AI 知识库", "Products: knowledge tools for small teams", "搜索条件已建立\n查询：小团队 AI 知识库\n资料类型：公司\n下一步：检查三条示例候选资料。", "Query prepared: AI knowledge tools for small teams.\nCategory: companies.\nNext: inspect three sample candidates."),
            option("找文章：知识库选型经验", "Articles: choosing a knowledge tool", "搜索条件已建立\n查询：知识库选型与接入经验\n资料类型：网页文章\n下一步：优先查看包含实施细节的内容。", "Query prepared: knowledge-tool selection and integration.\nCategory: web articles.\nNext: prioritize implementation details.")]),
        step(2, ("查看搜索结果", "Inspect search results"), ("在示例结果中选择一个候选，查看正文提取会给你什么。", "Choose a sample candidate to see what content extraction provides."), [
            option("示例 A · Atlas Notes", "Example A · Atlas Notes", "标题：Atlas Notes 团队知识库\n正文摘要：支持将文档整理为可检索的团队资料。\n高亮片段：「可以连接内部文档并保留原文出处。」\n待核实：接入权限与更新频率。", "Atlas Notes team knowledge base\nExtract: organizes documents into searchable team resources.\nHighlight: “Connect internal documents and retain original references.”\nVerify: permissions and refresh frequency."),
            option("示例 B · Cedar Docs", "Example B · Cedar Docs", "标题：Cedar Docs 使用体验\n正文摘要：作者描述了导入文件、问答和人工核查的步骤。\n高亮片段：「回答旁边可以查看引用段落。」\n待核实：是否支持你的文件格式。", "Cedar Docs experience report\nExtract: import files, ask questions, review answers.\nHighlight: “Inspect a cited passage next to the answer.”\nVerify: support for your file formats.")]),
        step(3, ("筛选并核对证据", "Review the evidence"), ("搜索结果只是起点。决定哪些资料值得进入简报。", "A search result is a starting point. Decide what belongs in the brief."), [
            option("保留有正文依据的资料", "Keep evidence with source content", "保留：包含产品说明和引用段落的资料。\n标记：接入条件仍需核实。\n排除：只有推广标题、没有正文证据的条目。", "Keep entries with product descriptions and cited passages.\nFlag integration requirements for verification.\nExclude promotion-only titles without supporting content."),
            option("要求补充实施细节", "Request implementation details", "新增研究问题：支持哪些连接器？权限如何继承？\n暂缓判断：没有足够信息的候选。\n下一轮搜索将围绕实施文档展开。", "Add questions: which connectors are supported, and how are permissions inherited?\nDefer judgment on incomplete candidates.\nFocus the next search on implementation documents.")], "review"),
        step(4, ("整理研究交付物", "Package the research"), ("选一种交付形式，完成这次体验。", "Choose an output format to finish the workflow."), [
            option("一页简报", "One-page brief", "研究目标 → 候选概览 → 引用证据 → 待核实事项。\n你可以在完成页下载本次选择与示例结果，作为研究框架。", "Research goal → candidates → cited evidence → open questions.\nDownload your choices and example outcomes on the final page."),
            option("结构化候选清单", "Structured candidate list", "清单字段：候选名称、资料类型、正文摘要、引用片段、待核实事项。\n适合继续筛选与比较，不自动替你作出购买决定。", "Fields: candidate, source type, extract, highlight, open question.\nUse the list for further review and comparison.")])], c("Exa 的核心体验是找到相关网页，再提取能用于后续研究的内容。这里演示的是工作流程，没有执行真实搜索。", "Exa helps find relevant pages and extract content for research. This illustrates the workflow without running a live search."), "https://exa.ai/docs/reference/search"

    yield "Helix Digital Infrastructure", "concept", c("一座 AI 数据中心，需要的不只是服务器。", "An AI data center needs more than servers."), c(
        "作为项目规划者，为一个虚构的 AI 园区协调算力、电力和连接资源。所有规模数字只用于说明关系。",
        "Plan a fictional AI campus by coordinating compute, power and connectivity. All numbers are illustrative."), [
        step(1, ("选择园区任务", "Choose the campus purpose"), ("先确定负载，资源规划才有方向。", "Start with the workload to frame the resource plan."), [
            option("模型训练园区", "Model training campus", "规划重点：集中算力、电力接入、散热和网络连接。\n工作包：计算设施、电力供应、连接网络。", "Focus: concentrated compute, power access, cooling and connectivity.\nWork packages: compute facilities, power supply, network."),
            option("推理服务园区", "Inference service campus", "规划重点：服务连接、容量扩展和供电协调。\n工作包：服务节点、连接路径、分期资源准备。", "Focus: service connectivity, capacity expansion and power coordination.\nWork packages: service nodes, connectivity, staged resources.")]),
        step(2, ("调整示例规模", "Adjust the example scale"), ("拖动规划单元，看看配套资源如何一起变化。这里没有真实功耗测算。", "Move the planning units to see linked resources change. This is not a real power estimate."), [
            option("先做一期", "Plan a first phase", "优先核对一期资源是否齐备，再决定后续扩展。示例中每个规划单元对应两项配套检查。", "Check whether first-phase resources are available before expanding. Each sample planning unit adds two coordination checks."),
            option("分两期准备", "Prepare two phases", "把后续资源需求提前列入协调清单。示例计算展示的是资源依赖，不代表建设报价。", "Include future requirements in the coordination list. The calculation illustrates dependencies, not a construction quote.")], "dial",
            dial={"min": 1, "max": 12, "initial": 4, "factor": 2, "unit": c("规划单元", "Planning units"), "result_label": c("示例配套检查项", "Sample coordination checks")}),
        step(3, ("比较资源准备状态", "Compare resource readiness"), ("如果只能先解决一个问题，你会优先推进哪一项？", "Which dependency would you resolve first?"), [
            option("电力接入待确认", "Power access unconfirmed", "依赖路径：电力条件 → 容量规划 → 设施建设安排。\n下一步：确认供电和接入条件，再推进容量承诺。", "Dependency: power access → capacity plan → construction schedule.\nNext: confirm supply and access before committing capacity."),
            option("网络连接待确认", "Connectivity unconfirmed", "依赖路径：连接条件 → 园区互联 → 业务承载安排。\n下一步：补齐连接规划，再安排业务接入。", "Dependency: connectivity → campus interconnection → service placement.\nNext: complete the network plan before scheduling service access.")], "compare"),
        step(4, ("形成协同计划", "Create a coordination plan"), ("把选择转化为一个可交接的规划清单。", "Turn your choices into a handoff checklist."), [
            option("导出资源依赖清单", "Export resource dependencies", "交付：计算设施、电力、连接三个工作包，各自的前置条件和待确认项。\n完成页可下载你本次的决策路径。", "Deliver three work packages: compute, power and connectivity, with prerequisites and open items.\nDownload your decision path on the final page."),
            option("导出阶段推进清单", "Export a phased checklist", "阶段一：核对场地与关键资源。\n阶段二：协调建设与接入。\n阶段三：复核承载条件。\n这是一份概念示例，实际项目需要专业工程规划。", "Phase 1: check site and critical resources.\nPhase 2: coordinate construction and access.\nPhase 3: review readiness.\nReal projects require professional engineering plans.")])], c("Helix 协调数字基础设施中的计算设施、电力和连接。概念体验帮助理解这种整合的价值，并非可以直接操作的 Helix 软件。", "Helix coordinates compute infrastructure, power and connectivity. This concept explorer explains that coordination; it is not Helix software."), "https://www.helixdi.com/about/"

    yield "Exaforce", "workflow", c("从一条告警，到一份可追踪的调查。", "From an alert to a traceable investigation."), c(
        "你在安全运营台处理一条虚构的异常访问告警。补齐上下文、分诊、调查，再选择处置路线。不会操作真实系统。",
        "Triage a fictional unusual-access alert. Add context, investigate and choose a response path. No real systems are accessed."), [
        step(1, ("打开告警", "Open an alert"), ("选择一条示例告警，建立调查案件。", "Choose a sample alert to open a case."), [
            option("新设备上的管理员登录", "Admin login from a new device", "CASE-104 · 待分诊\n信号：管理员账户使用了未见过的设备。\n已知：账户、时间、设备标识。\n缺失：是否为批准的设备更换。", "CASE-104 · Awaiting triage\nSignal: admin account on a new device.\nKnown: account, time, device ID.\nMissing: whether the device change was approved."),
            option("服务账户访问模式变化", "Changed service-account access", "CASE-105 · 待分诊\n信号：服务账户访问了新的资源范围。\n已知：账户、资源、访问记录。\n缺失：是否有对应的发布变更。", "CASE-105 · Awaiting triage\nSignal: service account accessed a new resource scope.\nKnown: account, resource, access log.\nMissing: a matching deployment change.")]),
        step(2, ("补齐业务上下文", "Add operational context"), ("同一个信号，在不同上下文里可能有不同解释。", "The same signal can mean different things in different contexts."), [
            option("找到匹配的批准记录", "A matching approval exists", "新增证据：有对应的变更记录，时间窗口吻合。\n调查方向：核对实际访问是否超出批准范围。\n保留原始告警和证据链。", "Evidence: a matching change record within the time window.\nInvestigate whether actual access exceeded its scope.\nKeep the original alert and evidence trail."),
            option("没有找到批准记录", "No matching approval found", "新增证据：目前缺少对应的变更记录。\n调查方向：联系负责人确认，并继续核查关联访问。\n不把缺失信息直接当作攻击结论。", "Evidence: no matching change record yet.\nConfirm with the owner and inspect related access.\nMissing information alone does not establish an attack.")]),
        step(3, ("核查调查材料", "Review investigation evidence"), ("选择检查重点，然后确认已看过示例材料。", "Choose a review focus, then confirm the sample evidence was reviewed."), [
            option("核对身份与权限范围", "Check identity and permissions", "证据清单：账户身份、当前权限、批准范围、实际访问资源。\n待确认：是否存在超出授权范围的访问。", "Evidence: account identity, current permissions, approval scope, resources accessed.\nOpen question: did access exceed authorization?"),
            option("核对时间线与关联活动", "Check timeline and related activity", "证据清单：告警时间、变更时间、前后访问记录。\n待确认：活动是否与业务变更一致。", "Evidence: alert time, change time, access events before and after.\nOpen question: does activity match the business change?")], "review"),
        step(4, ("提交处置路线", "Choose a response path"), ("这里的处置只写入示例案件，不会执行真实操作。", "Responses update this sample case only; no real action is executed."), [
            option("交由分析师进一步调查", "Escalate for analyst investigation", "示例状态：已转交。\n交接包：原始告警、上下文、证据清单、未解决问题。\n最终判断与实际处置保留给负责团队。", "Sample status: escalated.\nHandoff: original alert, context, evidence, open questions.\nThe responsible team retains the final decision."),
            option("记录解释并继续观察", "Document explanation and monitor", "示例状态：记录待观察。\n交接包：已找到的解释、仍需验证的条件、后续检查点。\n关闭真实案件仍需经过组织流程。", "Sample status: documented for monitoring.\nHandoff: explanation, remaining conditions, follow-up checks.\nReal case closure follows organizational procedures.")])], c("Exaforce 将检测、分诊、调查和响应串成安全运营流程。体验的重点是上下文与证据如何帮助人作出判断。", "Exaforce connects detection, triage, investigation and response. This experience shows how context and evidence support human judgment."), "https://www.exaforce.com/platform"

    yield "Abridge", "workflow", c("把一次对话，整理成可核查的记录。", "Turn a conversation into a reviewable note."), c(
        "使用虚构的行政沟通片段，体验从对话到记录、证据核对和交接的路径。不涉及诊断，也不采集录音或真实个人信息。",
        "Use fictional administrative dialogue to explore note creation, evidence review and handoff. No diagnosis, recording or personal data is involved."), [
        step(1, ("准备示例对话", "Prepare a sample conversation"), ("选择一个已经获得示例参与者同意的虚构片段。", "Choose a fictional excerpt with assumed participant consent."), [
            option("确认下次会面时间", "Confirm a follow-up meeting", "示例原文\n工作人员：我们下周再见一次，方便吗？\n参与者：周二上午可以，具体时间请再通知我。", "Sample transcript\nStaff: Can we meet again next week?\nParticipant: Tuesday morning works. Please confirm the exact time."),
            option("确认资料交接方式", "Confirm a document handoff", "示例原文\n工作人员：资料整理好后会交给你。\n参与者：请提供电子版，我还需要确认收件方式。", "Sample transcript\nStaff: We will provide the documents once organized.\nParticipant: Please provide a digital copy. I still need to confirm delivery.")]),
        step(2, ("选择记录格式", "Choose a note format"), ("生成记录前，先确定这次需要保留什么。", "Decide what the note should retain."), [
            option("对话摘要与待办", "Summary and follow-up items", "记录草稿\n摘要：双方讨论了下一步的安排。\n已确定：参与者表达了偏好。\n待办：由工作人员确认具体安排。\n未说明的信息保留为空。", "Draft note\nSummary: the participants discussed next steps.\nEstablished: the participant expressed a preference.\nFollow-up: staff to confirm the arrangement.\nUnstated details remain blank."),
            option("只保留待确认事项", "Open items only", "待确认清单\n1. 具体执行安排。\n2. 参与者确认。\n3. 交接负责人。\n这份示例不会把未提到的内容补成事实。", "Open items\n1. Exact arrangement.\n2. Participant confirmation.\n3. Handoff owner.\nThe example does not turn unstated details into facts.")]),
        step(3, ("回到原文核对", "Review against the transcript"), ("选择核查方式，确认记录没有超出原文信息。", "Check that the note stays within the transcript."), [
            option("查看支持片段", "Inspect supporting passages", "证据核查：回到第一步的示例原文，确认偏好和待定条件。\n记录原则：区分已确定与尚未确认。", "Evidence review: revisit the sample transcript from step one.\nCheck preferences and unresolved details.\nSeparate confirmed facts from open items."),
            option("删除没有依据的推断", "Remove unsupported inferences", "修订示例：将「安排已确认」改为「具体安排待确认」。\n保留：参与者实际表达的内容。\n删除：未在对话中出现的细节。", "Sample revision: change “arrangement confirmed” to “exact arrangement pending.”\nKeep what was actually said.\nRemove details absent from the dialogue.")], "review"),
        step(4, ("完成记录交接", "Complete the handoff"), ("体验记录已经过人工检查，选择交接形式。", "The sample note has been reviewed. Choose a handoff format."), [
            option("保存可核查摘要", "Save a reviewable summary", "示例状态：已检查，待交接。\n记录包含摘要、待办与核查说明。\n完成页可下载此次体验记录。", "Sample status: reviewed, ready for handoff.\nThe note includes a summary, follow-up items and review notes.\nDownload the experience on the final page."),
            option("交给负责人复核", "Send for owner review", "示例状态：待负责人复核。\n附带材料：原文片段、记录草稿、待确认事项。\n这里不会写入任何真实医疗系统。", "Sample status: awaiting owner review.\nPackage: transcript excerpt, draft and open questions.\nNothing is written to a real clinical system.")])], c("Abridge 的公开工作流包含对话记录、笔记生成、编辑和证据核对。这个行政片段仅用于说明流程，不代表临床记录质量。", "Abridge’s documented workflow includes recording, note generation, editing and evidence review. This administrative example does not represent clinical note quality."), "https://support.abridge.com/hc/en-us/articles/30279907940371-Abridge-Web-Editor-Basics"

    yield "Lovable", "workflow", c("从一个想法，到能点的任务应用。", "From an idea to a working task app."), c(
        "需求已准备好：给一个小团队做任务清单。选择页面结构、操作预览、检查效果，再形成交付计划。",
        "The brief is ready: a task list for a small team. Choose the structure, use the preview, review it and plan the handoff."), [
        step(1, ("选择应用方向", "Choose the app direction"), ("不用写提示词，直接选择一份已准备好的产品简报。", "No prompt needed. Choose a prepared product brief."), [
            option("轻量个人任务清单", "A lightweight personal task list", "简报：一个页面里添加、完成和删除任务。\n第一版范围：任务列表、输入框、完成状态。\n优先验证任务操作是否清楚。", "Brief: add, complete and remove tasks on one page.\nScope: list, input and completion state.\nValidate whether the interactions are clear."),
            option("小团队项目检查表", "A small-team project checklist", "简报：用一个检查表跟进项目准备。\n第一版范围：创建任务、勾选检查项、统计完成数。\n演示数据只保存在当前页面。", "Brief: track project preparation in a checklist.\nScope: create tasks, check items, count completions.\nDemo data stays in this page.")]),
        step(2, ("打开可操作预览", "Open the working preview"), ("选择预览，然后试着添加一条任务、勾选完成或删除。", "Open the preview, then add a task, complete it or remove it."), [
            option("打开任务应用", "Open the task app", "预览已准备好。下面的输入框和按钮可以直接操作。\n试一试：添加「和朋友测试第一版」，再勾选完成。", "The preview is ready. Its inputs and buttons work.\nTry adding “Test the first version with a friend,” then complete it."),
            option("从检查表开始", "Start with the checklist", "先操作已有检查项，再补充自己的任务。\n你正在体验「想法 → 页面 → 操作反馈」这条链路。", "Check existing items, then add your own.\nExplore the path from idea to interface to interaction feedback.")], "app", app_kind="tasks"),
        step(3, ("检查第一版体验", "Review the first version"), ("决定下一轮迭代最值得改进的地方。", "Choose the most useful next improvement."), [
            option("优化任务完成反馈", "Improve completion feedback", "迭代清单：完成态更清楚、任务统计更明显、空列表提示更友好。\n这些是示例产品决策，不会提交给 Lovable。", "Iteration list: clearer completion state, visible progress and a helpful empty state.\nThese sample decisions are not sent to Lovable."),
            option("完善保存与协作", "Plan persistence and collaboration", "迭代清单：接入数据库、设计成员权限、处理并发更新。\n当前体验中的任务会随页面重置，不是已发布的团队产品。", "Iteration list: database storage, member permissions and concurrent updates.\nTasks reset with this demo; this is not a deployed team app.")], "review"),
        step(4, ("准备产品交付", "Prepare a handoff"), ("把体验中的选择整理成下一步行动。", "Turn your choices into next steps."), [
            option("生成第一版测试计划", "Create a first-version test plan", "测试计划：添加任务 → 修改状态 → 检查空列表 → 复核手机布局。\n到真实产品中继续连接数据、邀请用户和发布。", "Test plan: add a task → change its state → inspect the empty list → check mobile layout.\nContinue with real data, users and publishing in the actual product."),
            option("整理后续迭代清单", "Create an iteration checklist", "下一步：确认使用场景、决定保存方式、检查访问权限、邀请试用者。\n完成页可下载本次体验选择。", "Next: confirm use cases, choose persistence, review permissions and invite testers.\nDownload your choices on the final page.")])], c("应用生成类产品把需求变成界面，并通过预览和迭代继续完善。这里的任务应用是 WeeklyAI 准备的示例，不是 Lovable 的真实生成结果。", "App builders turn a brief into an interface and refine it through previews. This task app is an authored WeeklyAI example, not a real Lovable generation."), "https://docs.lovable.dev/"


def main():
    count = 0
    for name, tier, headline, scenario, steps, takeaway, source in starters():
        product = ProductService.get_product_by_id(name)
        if not product:
            print("Not in catalog:", name)
            continue
        spec = validate_experience({"version": 2, "confidence": "illustrative", "tier": tier,
            "headline": headline, "scenario": scenario, "steps": steps, "takeaway": takeaway,
            "sources": [{"url": source, "label": c("官方产品资料", "Official product documentation")}]})
        entry = envelope(product, spec, "curated")
        for folder in (ROOT / "backend/data/demos", ROOT / "crawler/data/demos"):
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / (entry["cache_key"] + ".json")
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
                if existing.get("spec") == entry["spec"]:
                    continue
            path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        count += 1
    print("Validated starter experiences:", count)


if __name__ == "__main__":
    main()
