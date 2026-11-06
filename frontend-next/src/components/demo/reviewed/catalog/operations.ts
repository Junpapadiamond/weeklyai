import type { Task } from "../types";

export const tasks: Record<string, Task> = {
  // allO
  "12": {
    kind: "ledger",
    title: ["把点单直接分给后厨和吧台", "Split a table order between kitchen and bar"],
    instruction: ["为 6 号桌增减菜品，出餐票和桌单金额会一起更新。", "Change quantities for table six and watch station tickets and the table total update."],
    result: ["6 号桌出餐单", "Table 6 order tickets"],
    unit: ["€", "€"],
    rows: [
      [["意面", "Pasta"], ["后厨", "Kitchen"], 12],
      [["沙拉", "Salad"], ["后厨", "Kitchen"], 8],
      [["柠檬水", "Lemonade"], ["吧台", "Bar"], 4],
    ],
    source: "https://allo.restaurant/",
  },
  // Axya
  "p_5112981b460c193a": {
    kind: "threshold",
    title: ["从零件报价里找出能按期交货的供应商", "Shortlist suppliers for a machined part"],
    instruction: ["调整单件预算和交货期限，对照三份虚构报价。", "Set unit budget and delivery deadline against three fictional quotes."],
    result: ["可用报价", "Eligible quotes"],
    axes: [
      [["最高单价（€）", "Max unit price (€)"], "max", 48],
      [["最长交期（天）", "Max lead time (days)"], "max", 14],
    ],
    rows: [
      [["东港 CNC", "Eastport CNC"], 42,18],
      [["河湾加工", "Riverside Tooling"], 47,10],
      [["松林工坊", "Pine Works"], 53,7],
    ],
    source: "https://axya.co",
  },
  // Baselayer
  "p_d8e903f15095c832": {
    kind: "policy",
    title: ["在代理付款前检查身份与授权", "Check identity and authority before agent payments"],
    instruction: ["启用核验条件，重放三笔虚构请求。", "Enable verification requirements and replay three fictional requests."],
    result: ["交易核验日志", "Transaction verification log"],
    rules: [["要求商户身份已验证", "Require verified business"], ["要求代理持有付款授权", "Require agent payment mandate"]],
    rows: [
      [["批发商 A · 已核验，代理获准付款", "Wholesaler A · verified, agent authorized"], []],
      [["商户 B · 缺少身份记录", "Merchant B · business identity missing"], [0]],
      [["商户 C · 代理只有查询权限", "Merchant C · read-only agent"], [1]],
    ],
    source: "https://baselayer.com/",
  },
  // Corridor
  "p_e3c3120213a52416": {
    kind: "threshold",
    title: ["为团队筛选福利方案", "Shortlist benefit plans for a team"],
    instruction: ["调整每人月预算和家庭保障额度下限，对照虚构方案。", "Set a per-person monthly budget and a minimum family allowance for sample plans."],
    result: ["进入经纪人讨论的方案", "Plans to discuss with a broker"],
    axes: [
      [["最高月费（$）", "Max monthly cost ($)"], "max", 180],
      [["最低家庭津贴（$）", "Min family allowance ($)"], "min", 300],
    ],
    rows: [
      [["基础方案", "Core"], 140,200],
      [["家庭方案", "Family"], 175,400],
      [["扩展方案", "Extended"], 220,600],
    ],
    source: "https://corridoradvisors.com/",
  },
  // Cradle
  "3": {
    kind: "threshold",
    title: ["选出值得送去湿实验的蛋白变体", "Shortlist protein variants for the wet lab"],
    instruction: ["用虚构筛选数据权衡稳定性与活性，决定下一批验证对象。", "Trade stability against activity in a fictional screen to pick variants for testing."],
    result: ["待验证变体", "Variants for validation"],
    axes: [
      [["最低熔解温度（°C）", "Min melting point (°C)"], "min", 55],
      [["最低相对活性（%）", "Min relative activity (%)"], "min", 75],
    ],
    rows: [
      [["亲本 P0", "Parent P0"], 52,100],
      [["变体 A7", "Variant A7"], 58,84],
      [["变体 C2", "Variant C2"], 65,60],
    ],
    source: "https://www.cradle.bio/",
  },
  // Ditto
  "p_04dd7e17d62fdfe3": {
    kind: "slots",
    title: ["让介绍落到双方都能赴约的时间", "Turn an introduction into a date both can make"],
    instruction: ["点击双方有空的时段，查看真正重叠的见面时间。", "Edit both people’s availability to find mutually possible dates."],
    result: ["双方都能赴约", "Mutual availability"],
    times: [["周三 18:00", "Wed 18:00"], ["周三 19:00", "Wed 19:00"], ["周四 18:00", "Thu 18:00"]],
    rows: [
      [["阿南", "Nan"], [0,1]],
      [["小林", "Lin"], [1,2]],
    ],
    source: "https://ditto.ai/",
  },
  // Dyna.Ai
  "173": {
    kind: "routing",
    title: ["安排银行语音代理如何接听来电", "Route inbound banking calls with a voice agent"],
    instruction: ["为每类来意指定处理队列，查看这批示例来电的去向。", "Assign a destination to each intent and inspect where the sample calls land."],
    result: ["来电处理队列", "Call queues"],
    queues: [["自助服务", "Self-service"], ["专员回拨", "Specialist callback"], ["安全团队", "Security team"]],
    rows: [
      [["余额查询", "Balance enquiry"], ["来电 A：我想查本期余额。", "Call A: I want my current balance."], 0],
      [["身份异常", "Identity issue"], ["来电 B：这笔交易不是我操作的。", "Call B: I did not make this transaction."], 2],
      [["资料变更", "Profile change"], ["来电 C：我要更新登记号码。", "Call C: I need to update my number."], 1],
    ],
    source: "https://dyna.ai/",
  },
  // Finches
  "p_f9d850fa4bd23a23": {
    kind: "threshold",
    title: ["找出本周需要跟进的原料产区", "Flag sourcing origins that need attention"],
    instruction: ["调节示例预警线，找出干旱时间长且库存少的产区。", "Set sample alert thresholds to find origins with long dry spells and little stock."],
    result: ["采购跟进名单", "Sourcing watchlist"],
    axes: [
      [["最少无雨天数", "Min dry days"], "min", 8],
      [["库存最多可用天数", "Max stock cover (days)"], "max", 12],
    ],
    rows: [
      [["北谷 · 可可", "North Valley · cocoa"], 12,8],
      [["沿岸 · 咖啡", "Coast · coffee"], 5,6],
      [["高地 · 可可", "Highland · cocoa"], 16,18],
    ],
    source: "https://www.finches.ai/",
  },
  // Fini AI
  "766": {
    kind: "policy",
    title: ["让售后代理识别哪些退款需要转人工", "Decide which refund cases a support agent should escalate"],
    instruction: ["设置退款护栏，查看哪些工单能按示例规则处理。", "Set refund guardrails and inspect which cases can proceed under the sample policy."],
    result: ["退款分流记录", "Refund routing log"],
    rules: [["要求存在重复扣款凭据", "Require duplicate-charge evidence"], ["要求订单归属已核对", "Require verified order ownership"]],
    rows: [
      [["工单 102 · 重复扣款，归属已核验", "Ticket 102 · duplicate verified, owner matched"], []],
      [["工单 103 · 仅有一次扣款", "Ticket 103 · only one charge found"], [0]],
      [["工单 104 · 付款人身份待核", "Ticket 104 · account owner unverified"], [1]],
    ],
    source: "https://www.usefini.com/",
  },
  // Flow Engineering
  "p_afbcdbb77cfb30ac": {
    kind: "threshold",
    title: ["用台架数据验收硬件需求", "Verify a hardware requirement against bench results"],
    instruction: ["修改需求上限，追踪哪些原型需要重新验证。", "Edit requirement limits and trace which prototypes meet both bench checks."],
    result: ["通过两项需求的原型", "Prototypes meeting both requirements"],
    axes: [
      [["最大质量（g）", "Max mass (g)"], "max", 320],
      [["最大静态功耗（mW）", "Max idle draw (mW)"], "max", 90],
    ],
    rows: [
      [["原型 A · 台架 01", "Rev A · bench 01"], 300,105],
      [["原型 B · 台架 02", "Rev B · bench 02"], 315,85],
      [["原型 C · 台架 03", "Rev C · bench 03"], 345,75],
    ],
    source: "https://www.flowengineering.com/",
  },
  // General Analysis
  "161": {
    kind: "policy",
    title: ["用攻击样本测试代理的防线", "Red-team an agent with attack fixtures"],
    instruction: ["启用防护再重放相同请求，观察仍能穿过的攻击。", "Enable defenses and replay the same requests to see which attacks get through."],
    result: ["攻击回放记录", "Attack replay log"],
    rules: [["拒绝外部文档里的指令", "Reject instructions inside external documents"], ["限制敏感文件读取", "Restrict sensitive file reads"]],
    rows: [
      [["正常请求 · 摘要公开手册", "Control · summarize a public manual"], []],
      [["注入 · 网页要求忽略任务", "Injection · webpage overrides user task"], [0]],
      [["越权 · 请求访问密钥文件", "Overreach · request for a secret file"], [1]],
    ],
    source: "https://generalanalysis.com/",
  },
  // Go.AI
  "p_d22b01f389ff1fa2": {
    kind: "policy",
    title: ["检查本地部署的数据能否离开内网", "Check whether data leaves an on-premises deployment"],
    instruction: ["为一组银行内部请求设置网络边界，检查实际放行的路径。", "Set network boundaries for sample bank requests and inspect permitted paths."],
    result: ["数据流向审查", "Data path review"],
    rules: [["禁止外部推理端点", "Block external inference"], ["禁止日志离开本地", "Keep logs on premises"]],
    rows: [
      [["客户摘要 → 本地模型与本地日志", "Client summary → local model and local logs"], []],
      [["敏感文档 → 公网模型", "Sensitive document → public model endpoint"], [0]],
      [["审计日志 → 外部监控平台", "Audit log → external monitoring"], [1]],
    ],
    source: "https://go.ai/",
  },
  // Helix Digital Infrastructure
  "131": {
    kind: "budget",
    title: ["给数据中心园区分配接入电力", "Allocate utility capacity across a data-center site"],
    instruction: ["Helix 协调数据中心、电力与网络建设。调整机房和冷却单元数，检查示例园区的电力余量。", "Helix coordinates data centers, power and connectivity. Change the hall and cooling counts to inspect the sample site’s remaining power."],
    result: ["园区电力余量", "Remaining site power"],
    unit: ["MW", "MW"],
    capacity: 32,
    rows: [
      [["计算机房", "Compute hall"], 8],
      [["冷却单元", "Cooling plant"], 3],
      [["网络设备间", "Network room"], 2],
    ],
    source: "https://www.helixdi.com/",
    concept: true,
  },
  // Instinct
  "p_bd97057d7bb7aa84": {
    kind: "slots",
    title: ["把群聊里的空闲时间拼成共同计划", "Find a trip time that works for the whole chat"],
    instruction: ["点选三位朋友给出的时间，把交集整理成出行提议。", "Edit three friends’ availability to assemble a shared outing proposal."],
    result: ["全员可行的出行时间", "Times the whole group can go"],
    times: [["周六早", "Sat AM"], ["周六午", "Sat PM"], ["周日早", "Sun AM"]],
    rows: [
      [["阿乔", "Jo"], [0,1]],
      [["小梅", "May"], [1,2]],
      [["安迪", "Andy"], [0,1,2]],
    ],
    source: "https://techcrunch.com/2026/10/05/instinct-brings-its-ai-agent-to-group-chats-even-for-friends-without-an-account/",
  },
  // IVRy
  "25": {
    kind: "routing",
    title: ["搭一张餐厅电话分机表", "Build a restaurant phone routing tree"],
    instruction: ["给来电意图配置分机，重看三通来电的落点。", "Map caller intents to destinations and inspect the resulting call distribution."],
    result: ["分机收件箱", "Destination inboxes"],
    queues: [["自动语音", "Recorded answer"], ["前台", "Front desk"], ["值班经理", "Duty manager"]],
    rows: [
      [["营业时间", "Opening hours"], ["09:12 · 今天几点关门？", "09:12 · When do you close today?"], 0],
      [["订位", "Reservation"], ["09:14 · 想订八个人的桌。", "09:14 · A table for eight, please."], 1],
      [["失物", "Lost property"], ["09:17 · 我的包落在店里了。", "09:17 · I left my bag at the restaurant."], 2],
    ],
    source: "https://ivry.jp/",
  },
  // Kastle
  "p_7215e78c493d200d": {
    kind: "routing",
    title: ["把贷款服务请求分到下一位处理人", "Route loan servicing requests to the next owner"],
    instruction: ["为申请材料、还款咨询和争议选择处理去向。", "Assign destinations for missing documents, payment questions and disputes."],
    result: ["贷款服务工作队列", "Loan servicing queues"],
    queues: [["材料收集", "Document collection"], ["自助说明", "Self-service guidance"], ["人工复核", "Human review"]],
    rows: [
      [["缺材料", "Missing file"], ["档案 A：缺收入证明。", "File A: income document missing."], 0],
      [["还款日期", "Payment date"], ["档案 B：询问下一期到期日。", "File B: asks when the next payment is due."], 1],
      [["扣款争议", "Disputed debit"], ["档案 C：质疑重复扣款。", "File C: disputes a second debit."], 2],
    ],
    source: "https://www.kastle.ai/",
  },
  // Kontext
  "p_19b739473d2823ba": {
    kind: "policy",
    title: ["给代理接入业务工具时收紧权限", "Constrain an agent’s access to business tools"],
    instruction: ["打开运行时策略，查看每一项工具调用会被放行还是拦截。", "Enable runtime policies and inspect which tool calls can proceed."],
    result: ["工具调用轨迹", "Tool-call trace"],
    rules: [["客户库只读", "Read-only customer database"], ["禁止向外部地址导出", "Block external exports"]],
    rows: [
      [["crm.lookup · 查询客户 42", "crm.lookup · read customer 42"], []],
      [["crm.delete · 删除客户 42", "crm.delete · remove customer 42"], [0]],
      [["export.send · 将客户表发给外部邮箱", "export.send · send contacts outside the company"], [1]],
    ],
    source: "https://kontext.security/",
  },
  // Lamb Labs
  "p_98b5f813dc2c0fff": {
    kind: "budget",
    title: ["为固定权重芯片规划模型版本", "Budget separate chip runs for fixed model versions"],
    instruction: ["Lamb 把模型权重固化在芯片里。假设每种权重版本需独立生产一批，试算模型更新所需的批次。", "Lamb hardcodes model weights in silicon. Assuming a separate run for each weight version, budget the runs needed for model updates."],
    result: ["可用芯片批次", "Chip runs remaining"],
    unit: ["批", "runs"],
    capacity: 4,
    rows: [
      [["语音模型版本", "Speech model versions"], 1],
      [["视觉模型版本", "Vision model versions"], 1],
      [["翻译模型版本", "Translation model versions"], 1],
    ],
    source: "http://lamb-labs.com",
    concept: true,
  },
  // Latent Labs
  "2": {
    kind: "threshold",
    title: ["为结合任务筛选设计候选", "Screen designed binders for follow-up"],
    instruction: ["Latent Labs 研究用生成模型设计分子。用虚构结合读数和可溶性，挑出值得复测的设计。", "Latent Labs develops generative models for molecular design. Use fictional binding and solubility observations to shortlist designs for retesting."],
    result: ["待复测候选", "Candidates to retest"],
    axes: [
      [["最高解离常数（nM）", "Max dissociation constant (nM)"], "max", 30],
      [["最低可溶比例（%）", "Min soluble fraction (%)"], "min", 70],
    ],
    rows: [
      [["设计 L1", "Design L1"], 18,58],
      [["设计 L2", "Design L2"], 24,82],
      [["设计 L3", "Design L3"], 42,90],
    ],
    source: "https://www.latentlabs.com/",
  },
  // Lottie
  "p_7e044d9cd8bafe63": {
    kind: "slots",
    title: ["给护理机构的咨询安排一次看房", "Arrange a care-home viewing from an enquiry"],
    instruction: ["对照家属、接待人员和房间的时间，在排期表上找出交集。", "Match family, host and room availability to find a viewing slot."],
    result: ["可预约的看房时间", "Bookable viewing times"],
    times: [["周一 10:00", "Mon 10:00"], ["周一 14:00", "Mon 14:00"], ["周二 11:00", "Tue 11:00"]],
    rows: [
      [["家属", "Family"], [0,2]],
      [["接待人员", "Host"], [0,1,2]],
      [["可看房间", "Room available"], [0,1]],
    ],
    source: "https://foundcrm.lottie.org/",
  },
  // Modal Labs
  "733": {
    kind: "budget",
    title: ["为并发推理任务分配 GPU", "Allocate GPUs to concurrent inference jobs"],
    instruction: ["增减同时运行的工作容器，观察示例 GPU 配额何时不足。", "Change concurrent worker counts to see when the sample GPU quota runs out."],
    result: ["可用 GPU", "Available GPUs"],
    unit: ["块 GPU", "GPUs"],
    capacity: 8,
    rows: [
      [["图像推理容器", "Image inference worker"], 1],
      [["视频推理容器", "Video inference worker"], 4],
      [["批量嵌入容器", "Batch embedding worker"], 2],
    ],
    source: "https://modal.com/",
  },
  // Nous Research
  "p_c5d2b2652ee1cd28": {
    kind: "policy",
    title: ["给研究代理分配完成任务所需的工具", "Equip a research agent with the tools its brief needs"],
    instruction: ["Hermes Agent 能调用工具完成多步任务。为虚构研究任务划定工具权限，检查可执行的工作。", "Hermes Agent uses tools to carry out multi-step tasks. Set tool boundaries for a fictional research brief and inspect which jobs can run."],
    result: ["研究任务执行清单", "Research task execution list"],
    rules: [["只允许本地资料", "Restrict to local sources"], ["保存笔记前需确认", "Require approval before saving notes"]],
    rows: [
      [["读取本地访谈稿", "Read a local interview transcript"], []],
      [["检索外部公开档案", "Fetch an external public archive"], [0]],
      [["写入未经确认的研究笔记", "Write an unapproved research note"], [1]],
    ],
    source: "https://nousresearch.com",
  },
  // Numeral
  "p_e5735f993bbbf47c": {
    kind: "ledger",
    title: ["把销售流水归集到申报地区", "Group sales records by filing jurisdiction"],
    instruction: ["Numeral 帮商户处理跨地区销售税务。调整示例订单数量，先把销售额归集到相应地区。", "Numeral helps merchants manage sales-tax compliance across regions. Adjust sample order counts and reconcile gross sales by jurisdiction."],
    result: ["地区销售对账表", "Sales by jurisdiction"],
    unit: ["$", "$"],
    rows: [
      [["线下销售 · 东区", "In-store sale · East"], ["东区", "East"], 100],
      [["网店销售 · 西区", "Online sale · West"], ["西区", "West"], 60],
      [["网店销售 · 东区", "Online sale · East"], ["东区", "East"], 80],
    ],
    source: "https://www.numeral.com/",
  },
  // Phia
  "792": {
    kind: "threshold",
    title: ["比较同一款夹克的新货和二手价", "Compare new and resale offers for one jacket"],
    instruction: ["设置到手预算和最迟送达天数，查看符合条件的示例报价。", "Set an all-in budget and delivery deadline for the sample listings."],
    result: ["符合条件的同款", "Matching offers"],
    axes: [
      [["最高含运费价格（$）", "Max delivered price ($)"], "max", 105],
      [["最迟送达（天）", "Max shipping time (days)"], "max", 7],
    ],
    rows: [
      [["全新 · 品牌店", "New · brand store"], 145,3],
      [["近新 · 转售 A", "Like new · resale A"], 92,6],
      [["有磨损 · 转售 B", "Worn · resale B"], 68,10],
    ],
    source: "https://phia.com/",
  },
  // Photon
  "p_6cecf733c79e56d9": {
    kind: "routing",
    title: ["将消息事件接到代理处理器", "Wire messaging events to an agent handler"],
    instruction: ["为三种入站事件指定处理器，检查消息实际进入的队列。", "Assign handlers to inbound events and inspect their delivery queues."],
    result: ["消息处理轨迹", "Message delivery trace"],
    queues: [["回复处理器", "Reply handler"], ["附件解析器", "Attachment parser"], ["人工接手", "Human handoff"]],
    rows: [
      [["文本事件", "Text event"], ["evt_01 · “几点开门？”", "evt_01 · “When do you open?”"], 0],
      [["媒体事件", "Media event"], ["evt_02 · receipt.jpg", "evt_02 · receipt.jpg"], 1],
      [["转人工请求", "Handoff request"], ["evt_03 · “找工作人员”", "evt_03 · “Talk to a person”"], 2],
    ],
    source: "https://photon.codes/",
  },
  // ProcessUnity
  "p_3b2c605d428162a9": {
    kind: "policy",
    title: ["把资料不齐的供应商送去复审", "Route incomplete vendor files to further review"],
    instruction: ["启用准入条件，查看哪些第三方档案还缺材料。", "Enable intake requirements to find third-party files with missing evidence."],
    result: ["供应商准入队列", "Vendor intake queue"],
    rules: [["要求当前安全问卷", "Require a current security questionnaire"], ["要求数据处理协议", "Require a data processing agreement"]],
    rows: [
      [["北港托管 · 问卷与协议齐全", "Northport Hosting · both items current"], []],
      [["远峰分析 · 问卷已过期", "Summit Analytics · questionnaire expired"], [0]],
      [["绿湾云 · 协议未签", "Bay Cloud · agreement unsigned"], [1]],
    ],
    source: "https://www.processunity.com/",
  },
  // Reinforce Labs
  "p_66b854195d23626c": {
    kind: "policy",
    title: ["复测一条 AI 客服修复规则", "Replay an AI support evaluation after a fix"],
    instruction: ["逐项启用修复，用同一组失败样本验证还有哪些会漏过。", "Apply fixes to the same failure set and see which cases still get through."],
    result: ["回归评估结果", "Regression replay"],
    rules: [["拦截无来源的保证", "Reject unsupported guarantees"], ["屏蔽完整支付卡号", "Mask full payment card numbers"]],
    rows: [
      [["对照 · 回复含帮助文档链接", "Control · response cites the help article"], []],
      [["失败 A · 承诺一定获赔", "Failure A · guarantees reimbursement"], [0]],
      [["失败 B · 返回完整卡号", "Failure B · exposes a full card number"], [1]],
    ],
    source: "https://www.reinforcelabs.ai/",
  },
  // Saia
  "p_8cbeb8707136b534": {
    kind: "budget",
    title: ["看哪些推理负载能装进本地设备", "Fit inference workloads on an edge device"],
    instruction: ["Saia 设计本地推理芯片。改变常驻模型副本数，检查假设的设备内存能否装下这些负载。", "Saia designs chips for local inference. Vary resident model replicas to see whether they fit a hypothetical device memory budget."],
    result: ["设备剩余内存", "Remaining device memory"],
    unit: ["GB", "GB"],
    capacity: 16,
    rows: [
      [["文本模型副本", "Text model replica"], 6],
      [["视觉编码器副本", "Vision encoder replica"], 3],
      [["语音模型副本", "Speech model replica"], 2],
    ],
    source: "https://www.saiacompute.com/",
    concept: true,
  },
  // Satlyt
  "p_ca2f35d3c66d098d": {
    kind: "budget",
    title: ["决定卫星过站时传回哪些数据", "Pack a satellite downlink window"],
    instruction: ["调整原始图像、裁剪图与星上识别结果的数量，观察下传余量。", "Change the mix of raw scenes, crops and onboard detections to fit a downlink window."],
    result: ["过站剩余容量", "Remaining downlink capacity"],
    unit: ["MB", "MB"],
    capacity: 100,
    rows: [
      [["原始场景", "Raw scene"], 50],
      [["目标裁剪", "Target crop"], 12],
      [["检测摘要", "Detection summary"], 2],
    ],
    source: "https://satlyt.ai/",
    concept: true,
  },
  // SpaceFlow Technologies
  "p_1f3483df513b3f78": {
    kind: "threshold",
    title: ["把采购邮件中的报价配到订单要求", "Match emailed quotes to a purchase request"],
    instruction: ["为一批包装箱设定数量和总预算，再看哪些报价能转为订单草稿。", "Set the cartons required and total budget to identify quotes suitable for a draft order."],
    result: ["可起草订单的报价", "Quotes eligible for a draft order"],
    axes: [
      [["至少可供货（箱）", "Min cartons available"], "min", 80],
      [["整批最高价（€）", "Max lot cost (€)"], "max", 900],
    ],
    rows: [
      [["杉木供应 · 邮件 03", "Cedar Supply · email 03"], 60,600],
      [["南港包装 · 邮件 08", "Southport Packs · email 08"], 100,850],
      [["三角仓储 · 邮件 11", "Delta Stock · email 11"], 120,1050],
    ],
    source: "https://spaceflow.tech/legal/terms-of-service",
  },
  // Tynapse
  "p_975b2754c31cd744": {
    kind: "policy",
    title: ["在代理执行之前验证业务决策", "Verify agent decisions before execution"],
    instruction: ["把费用制度的条件加到审批前，再看哪些决定需要干预。", "Apply expense-policy conditions before approval and inspect interventions."],
    result: ["决策审计轨迹", "Decision audit trail"],
    rules: [["超限费用需经理批准", "Require manager sign-off over the limit"], ["报销必须附凭据", "Require receipts for reimbursement"]],
    rows: [
      [["费用 71 · 限额内且有凭据", "Expense 71 · within limit with receipt"], []],
      [["费用 72 · 超限且没有批准", "Expense 72 · over limit, no sign-off"], [0]],
      [["费用 73 · 无收据", "Expense 73 · receipt missing"], [1]],
    ],
    source: "https://tynapse.com/",
  },
};
