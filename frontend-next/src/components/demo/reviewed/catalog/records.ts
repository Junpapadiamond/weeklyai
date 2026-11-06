import type { Task } from "../types";

export const tasks: Record<string, Task> = {
  // Abridge
  "1056": {
    kind: "evidence",
    title: ["把复诊对话整理成可核查的记录", "Turn a visit conversation into a reviewable note"],
    instruction: ["勾选对话里的事实，再核对或修改记录措辞。", "Select statements from the visit, then review or edit the note."],
    result: ["待复核的就诊记录", "Visit note for review"],
    rows: [
      [["患者：这周有两天睡不好。", "Patient: I slept poorly on two nights this week."], ["自述情况", "Patient report"], ["本周有两晚睡眠不佳。", "Poor sleep on two nights this week."]],
      [["医生：请把睡眠日志带来。", "Clinician: Please bring your sleep diary."], ["随访事项", "Follow-up"], ["下次携带睡眠日志。", "Bring the sleep diary to the next visit."]],
      [["患者：周二上午可以，时间还没定。", "Patient: Tuesday morning works. We have no time set yet."], ["预约状态", "Scheduling"], ["周二上午可行，具体时间待定。", "Tuesday morning is possible. Exact time pending."]],
    ],
    source: "https://support.abridge.com/hc/en-us/articles/30279907940371-Abridge-Web-Editor-Basics",
  },
  // Bridge Impact AI
  "p_092376f16efde3bb": {
    kind: "evidence",
    title: ["从会议纪要建立和解行动台账", "Build a reconciliation action register from meeting notes"],
    instruction: ["Bridge 帮组织跟踪与原住民社区协商的和解行动。选入会议里的明确承诺，保留待社区确认的事项。", "Bridge helps organizations track reconciliation work with Indigenous communities. Capture meeting commitments and keep community decisions open."],
    result: ["待协商的行动台账", "Action register for consultation"],
    rows: [
      [["采购组同意先把供应商征询稿送审。", "Procurement agreed to circulate the draft supplier invitation."], ["采购承诺", "Procurement commitment"], ["采购组发送征询稿。", "Procurement to circulate its draft."]],
      [["社区代表要求在发布前预留反馈时间。", "Community representatives asked for time to respond before publication."], ["咨询事项", "Consultation"], ["与代表协商反馈时间。", "Agree on a feedback window with representatives."]],
      [["培训主题还没有得到社区确认。", "The community has yet to confirm a training topic."], ["待确认", "Open question"], ["请社区确认培训主题。", "Seek community input on the training topic."]],
    ],
    source: "https://bridgeimpact.ai",
  },
  // Cori Clinical
  "p_2874b8371f74cb4e": {
    kind: "evidence",
    title: ["把既往试验经验带入新方案评审", "Use prior trial evidence in a protocol review"],
    instruction: ["从虚构试验档案选取证据，整理下次启动会要解决的问题。", "Use the fictional trial file to prepare questions for the next kickoff."],
    result: ["方案评审备忘", "Protocol review memo"],
    rows: [
      [["试验 A 结项：周一采样与快递取件冲突。", "Trial A closeout: Monday collection conflicted with courier pickup."], ["采样安排", "Collection schedule"], ["核对采样与取件时间。", "Check collection and pickup windows."]],
      [["站点 B：冷藏交接责任人未列入启动包。", "Site B: the refrigerated handoff owner was missing from the startup pack."], ["站点准备", "Site readiness"], ["在启动包补上交接责任人。", "Name a handoff owner in the startup pack."]],
      [["预算附录：周末运输尚无报价。", "Budget appendix: weekend shipping has no quote."], ["预算缺口", "Budget gap"], ["获取周末运输报价。", "Request a weekend shipping quote."]],
    ],
    source: "http://www.cori-clinical.com/",
  },
  // Daloopa
  "7": {
    kind: "evidence",
    title: ["把披露数字带回财务模型", "Trace reported figures into a model sheet"],
    instruction: ["从虚构财报选取科目，核对期间、单位和数值。", "Pull line items from the fictional filing and check period, units and value."],
    result: ["模型录入底稿", "Model input sheet"],
    rows: [
      [["第 4 页 · Q2 营收 840 万美元。", "Page 4 · Q2 revenue was USD 8.4m."], ["Q2 营收（百万美元）", "Q2 revenue (USD m)"], ["8.4", "8.4"]],
      [["第 4 页 · Q1 营收 750 万美元。", "Page 4 · Q1 revenue was USD 7.5m."], ["Q1 营收（百万美元）", "Q1 revenue (USD m)"], ["7.5", "7.5"]],
      [["附注 2 · Q2 研发费用 110 万美元。", "Note 2 · Q2 R&D expense was USD 1.1m."], ["Q2 研发（百万美元）", "Q2 R&D (USD m)"], ["1.1", "1.1"]],
    ],
    source: "https://daloopa.com/",
  },
  // Exa
  "36": {
    kind: "search",
    title: ["从网页资料里检索可引用的段落", "Retrieve passages from a web collection"],
    instruction: ["在三篇虚构网页中输入关键词，点开命中段落查出处。", "Type keywords into this three-page fictional collection and open a hit to inspect its source."],
    result: ["检索结果", "Retrieved passages"],
    query: ["电池", "battery"],
    rows: [
      [["储能试验日志 · §2", "Storage trial log · §2"], ["电池储能装置在夜间为站点供电。", "The battery storage unit powers the site overnight."], ["电池 储能 夜间", "battery storage overnight"]],
      [["电池回收手册 · §4", "Cell recovery manual · §4"], ["回收线按电池材料分类，再拆解外壳。", "The recycling line sorts battery materials before dismantling the casing."], ["电池 回收 材料", "battery recycling materials"]],
      [["光伏安装简报 · §1", "Solar installation brief · §1"], ["屋顶阵列在午间向楼内供电。", "The rooftop solar array supplies the building at midday."], ["光伏 太阳能 屋顶", "solar rooftop array"]],
    ],
    source: "https://exa.ai/",
  },
  // Falcon
  "p_8c739175143f5fc7": {
    kind: "evidence",
    title: ["把合同争议交给律师复核", "Prepare disputed contract terms for counsel"],
    instruction: ["从双方往来里挑出未决条款，改写给律师的问题。", "Pick unresolved terms and edit the questions for counsel."],
    result: ["律师评审单", "Counsel review sheet"],
    rows: [
      [["采购：草案写 60 天付款，我们提议 30 天。", "Buyer: the draft says 60 days. We propose 30."], ["付款期限", "Payment terms"], ["记录 30 天提议，请律师复核草案。", "Flag the proposed 30-day term for counsel."]],
      [["供应商：附件中没有数据删除时间。", "Supplier: the appendix has no data deletion date."], ["数据附件", "Data appendix"], ["请确认删除期限是否需要约定。", "Ask counsel to review the missing deletion period."]],
      [["法务：双方尚未同意责任上限。", "Legal: the parties have not agreed a liability cap."], ["责任上限", "Liability cap"], ["将责任上限列为待谈事项。", "Leave the cap open for negotiation."]],
    ],
    source: "https://www.falcon.law",
  },
  // FRANK
  "p_39ad18810d7dfdbc": {
    kind: "evidence",
    title: ["从客户邮件准备保单续保资料", "Prepare a renewal file from a broker’s inbox"],
    instruction: ["挑出会改变续保询价的事实，修改给经纪人的交接记录。", "Extract changes that matter for a renewal quote and edit the handoff."],
    result: ["经纪人续保底稿", "Broker renewal file"],
    rows: [
      [["客户：车队新加了两辆厢式车。", "Client: we added two vans to our fleet."], ["车辆变更", "Fleet change"], ["增加两辆厢式车，待补车辆信息。", "Add two vans, identifiers pending."]],
      [["客户：仓库已搬到西区。", "Client: our warehouse moved to the west district."], ["地址", "Location"], ["询问新仓库完整地址。", "Request the new warehouse address."]],
      [["经纪人：保险期于 12 月 1 日届满。", "Broker: the policy expires on 1 December."], ["续保日期", "Renewal date"], ["12 月 1 日前跟进续保。", "Follow up before 1 December."]],
    ],
    source: "https://frankinsurance.ai/us/en",
  },
  // GetReal Security
  "748": {
    kind: "evidence",
    title: ["把可疑视频的证据交给核验人员", "Assemble evidence for a suspicious video review"],
    instruction: ["GetReal 帮安全团队调查疑似伪造的媒体。把来件和核验记录中可追溯的线索放入案卷。", "GetReal helps security teams investigate suspected manipulated media. Build a case file from traceable submission and verification records."],
    result: ["媒体核验案卷", "Media verification file"],
    rows: [
      [["来件：对方只发送了转发的视频片段。", "Submission: the sender supplied a forwarded clip only."], ["素材来源", "Provenance"], ["没有原始文件，需索取原件。", "Request the original file."]],
      [["音轨记录：第 8 秒有一次中断。", "Audio log: an interruption was noted at second 8."], ["待查线索", "Review lead"], ["检查 00:08 的中断及剪辑上下文。", "Inspect the interruption at 00:08 in context."]],
      [["回拨记录：尚未通过已知号码核实身份。", "Callback log: identity has yet to be checked via a known number."], ["核验步骤", "Verification"], ["通过独立渠道核验身份。", "Verify identity through an independent channel."]],
    ],
    source: "https://www.getrealsecurity.com/",
  },
  // Gizmo
  "298": {
    kind: "quiz",
    title: ["把生物课笔记变成主动回忆练习", "Practice recall from biology notes"],
    instruction: ["先读示例笔记，再遮住关键词作答。答错的卡会回到队尾。", "Read the notes, then recall the hidden terms. Missed cards return to the queue."],
    result: ["生物复习卡", "Biology recall deck"],
    rows: [
      [["叶绿体负责光合作用。", "Photosynthesis takes place in chloroplasts."], ["哪种细胞器负责光合作用？", "Which organelles carry out photosynthesis?"], ["叶绿体", "chloroplasts"]],
      [["细胞核保存遗传信息。", "The nucleus stores genetic information."], ["哪个结构保存遗传信息？", "Which structure stores genetic information?"], ["细胞核", "nucleus"]],
      [["核糖体参与蛋白质合成。", "Ribosomes synthesize proteins."], ["哪种结构合成蛋白质？", "Which structures synthesize proteins?"], ["核糖体", "ribosomes"]],
    ],
    source: "https://help.gizmo.ai/en/articles/14472668-how-does-gizmo-work",
  },
  // Helpfeel
  "801": {
    kind: "search",
    title: ["用客户自己的说法找到 FAQ", "Find an FAQ in the customer’s own words"],
    instruction: ["试试“钱还没到”或“改地址”，查看对应的支持条目。", "Try “money missing” or “move house” to retrieve the matching support article."],
    result: ["匹配的 FAQ", "Matched FAQ"],
    query: ["钱还没到", "money missing"],
    rows: [
      [["退款进度", "Refund status"], ["已退款订单可在付款记录中查看原路退回进度。", "Open the original payment record to track a refunded order."], ["钱还没到 退款 退钱", "money missing refund reimbursement"]],
      [["修改寄送地址", "Change shipping address"], ["在订单发货前打开配送资料，更新收件地址。", "Update the shipping address in delivery details before dispatch."], ["改地址 搬家 收件", "move house address shipping"]],
      [["更换登录邮箱", "Change sign-in email"], ["在账户设置中验证新邮箱。", "Verify your new email in account settings."], ["邮箱 登录 账号", "email login account"]],
    ],
    source: "https://www.helpfeel.com/",
  },
  // Kello
  "p_83ab91df1654988d": {
    kind: "search",
    title: ["用岗位要求检索候选人的工作证据", "Find candidate work that matches a role brief"],
    instruction: ["输入想找的技能，点开候选人的虚构作品记录核对依据。", "Type a role skill, then inspect the fictional work record behind each match."],
    result: ["与岗位相关的作品", "Role-relevant work"],
    query: ["编译器", "compiler"],
    rows: [
      [["林 · 编译器贡献", "Lin · compiler contributor"], ["维护编译器优化过程，并公开了基准测试。", "Maintained a compiler optimization pass and published benchmarks."], ["编译器 优化 基准", "compiler optimization benchmarks"]],
      [["梅 · 平台工程师", "Mei · platform engineer"], ["构建分布式构建缓存，并记录了迁移方案。", "Built a distributed build cache and documented the migration."], ["缓存 平台 分布式", "cache platform distributed"]],
      [["周 · 工具作者", "Zhou · tooling author"], ["为编译器开发调试器，发布了测试用例。", "Built a debugger for a compiler and published tests."], ["编译器 调试器 测试", "compiler debugger testing"]],
    ],
    source: "https://kello.ai/faq",
  },
  // Lucis
  "19": {
    kind: "evidence",
    title: ["把历次检验记录整理给医生", "Prepare longitudinal lab results for a clinician"],
    instruction: ["Lucis 把历次检验和医生复核连起来。选取不同日期的虚构记录，保留单位和缺失的上下文。", "Lucis brings lab results together for clinician review. Select dated fictional observations and preserve units and missing context."],
    result: ["就诊讨论单", "Visit discussion sheet"],
    rows: [
      [["1 月 8 日：铁蛋白 52 µg/L。", "8 Jan: ferritin 52 µg/L."], ["1 月结果", "January result"], ["铁蛋白 52 µg/L。", "Ferritin 52 µg/L."]],
      [["4 月 9 日：铁蛋白 47 µg/L。", "9 Apr: ferritin 47 µg/L."], ["4 月结果", "April result"], ["铁蛋白 47 µg/L。", "Ferritin 47 µg/L."]],
      [["转诊单：未注明两次是否同实验室。", "Referral: whether the same lab ran both tests is unspecified."], ["给医生的问题", "Question for clinician"], ["这两次测量可以直接比较吗？", "Are these two measurements directly comparable?"]],
    ],
    source: "https://www.lucis.life/",
  },
  // Mecka AI
  "p_0ae0feabf51fd8c0": {
    kind: "evidence",
    title: ["从第一视角录像标注训练片段", "Label first-person clips for a robotics dataset"],
    instruction: ["查看虚构的时间轴记录，选择可用片段并修改动作标签。", "Inspect the fictional timeline, select usable segments and edit action labels."],
    result: ["带时间戳的数据集", "Timestamped dataset"],
    rows: [
      [["00:02–00:05 · 手伸向蓝色料箱。", "00:02–00:05 · A hand reaches toward the blue bin."], ["00:02–00:05", "00:02–00:05"], ["伸手取物", "Reach"]],
      [["00:05–00:08 · 手指闭合，零件离开箱底。", "00:05–00:08 · Fingers close and lift a part clear of the bin."], ["00:05–00:08", "00:05–00:08"], ["抓取零件", "Grasp part"]],
      [["00:08–00:10 · 镜头被衣袖遮住。", "00:08–00:10 · A sleeve occludes the lens."], ["00:08–00:10", "00:08–00:10"], ["遮挡，待复核", "Occluded, review before use"]],
    ],
    source: "https://www.mecka.ai/",
  },
  // Mindset AI
  "770": {
    kind: "search",
    title: ["测试嵌入应用的知识助手能找到什么", "Test the knowledge behind an embedded assistant"],
    instruction: ["Mindset 让软件团队把助手嵌入自己的产品。以用户身份搜索，再核对哪段文档能支持回复。", "Mindset lets software teams embed assistants in their products. Search as an end user and inspect which passage can support a reply."],
    result: ["助手可引用的资料", "Retrievable help passages"],
    query: ["导出", "export"],
    rows: [
      [["团队手册 · 导出", "Team guide · export"], ["工作区管理员可在报表中导出 CSV。", "Workspace admins can export CSV from Reports."], ["导出 csv 报表", "export csv reports"]],
      [["权限手册 · 邀请", "Access guide · invites"], ["管理员可向团队邮箱发送邀请。", "Admins can invite members by team email."], ["权限 邀请 成员", "access invite members"]],
      [["计费手册 · 发票", "Billing guide · invoices"], ["账单联系人可在计费页下载月度发票。", "Billing contacts can download monthly invoices under Billing."], ["账单 发票 下载", "billing invoice download"]],
    ],
    source: "https://www.mindset.ai/",
  },
  // Mitti Labs
  "p_136bb9316567279c": {
    kind: "evidence",
    title: ["对照稻田遥感记录与地面观察", "Reconcile satellite observations with rice-field notes"],
    instruction: ["把同一地块的观测并入核查表，留下证据缺口。", "Combine matching observations in a field review and keep evidence gaps visible."],
    result: ["稻田核查表", "Paddy review sheet"],
    rows: [
      [["地块 R7 · 6 月 4 日：雷达图像出现变化。", "Plot R7 · 4 Jun: radar imagery changed."], ["卫星观测", "Satellite observation"], ["R7 的信号发生变化，原因待核。", "R7 signal changed, cause unconfirmed."]],
      [["地块 R7 · 6 月 5 日：田间记录确认排水。", "Plot R7 · 5 Jun: a field log confirms drainage."], ["地面核查", "Ground check"], ["6 月 5 日记录排水。", "Drainage logged on 5 Jun."]],
      [["地块 R8 · 当周没有地面记录。", "Plot R8 · no field log for the week."], ["核查缺口", "Evidence gap"], ["R8 需要地面观察。", "A field observation is needed for R8."]],
    ],
    source: "https://www.mittilabs.earth/",
  },
  // Myca
  "p_906edfdc6b6d7b36": {
    kind: "evidence",
    title: ["把田间群消息整理成派工单", "Turn field messages into an agronomy dispatch"],
    instruction: ["勾选群里的请求，修订地块、任务和截止时间。", "Select requests from the field chat and edit plot, job and deadline."],
    result: ["田间派工单", "Field dispatch"],
    rows: [
      [["07:10 · 北田：二号阀门还在漏水。", "07:10 · North field: valve two is still leaking."], ["北田工单", "North field job"], ["检查二号阀门。", "Inspect valve two."]],
      [["07:24 · 南田：苗盘到货，请今天点数。", "07:24 · South field: trays arrived. Count them today."], ["南田工单", "South field job"], ["今天清点到货苗盘。", "Count delivered trays today."]],
      [["07:32 · 仓库：明早可以送备用管。", "07:32 · Depot: spare pipe can be delivered tomorrow morning."], ["物资跟进", "Supply follow-up"], ["确认备用管配送时间。", "Confirm the spare pipe delivery."]],
    ],
    source: "https://www.myca.ag/",
  },
  // Rowspace
  "613": {
    kind: "evidence",
    title: ["把投委会问题连回底层资料", "Trace an investment memo to its underlying records"],
    instruction: ["从虚构基金资料提取可核对的数字与假设。", "Select figures and open assumptions from a fictional fund data room."],
    result: ["投委会底稿", "Investment committee notes"],
    rows: [
      [["运营月报 · 3 月经常性收入 42 万美元。", "Operations pack · March recurring revenue was USD 420k."], ["经营数据", "Operating figure"], ["3 月经常性收入 42 万美元。", "March recurring revenue: USD 420k."]],
      [["董事会纪要 · 两家客户仍在试点。", "Board minutes · two customers are still in pilot."], ["销售阶段", "Pipeline stage"], ["两家试点客户尚未签约。", "Two pilot customers have yet to sign."]],
      [["模型 v3 · 预测假设两家试点都转正。", "Model v3 · forecast assumes both pilots convert."], ["模型假设", "Model assumption"], ["核实试点转正假设。", "Review the assumed pilot conversions."]],
    ],
    source: "https://www.rowspace.ai/",
  },
  // StudyStash
  "p_80f4c5ac1f3f7f2b": {
    kind: "quiz",
    title: ["用课程讲义做一轮自适应练习", "Turn course notes into an adaptive practice round"],
    instruction: ["阅读这份统计讲义并开始练习，答错的概念会再次出现。", "Read the statistics notes and start practicing. Missed concepts appear again."],
    result: ["统计练习卡", "Statistics practice deck"],
    rows: [
      [["中位数是排序后的中间值。", "The median is the middle value of an ordered set."], ["有序数列的中间值叫作什么？", "What is the middle value in an ordered set?"], ["中位数", "median"]],
      [["众数是出现次数最多的值。", "The mode is the most frequent value."], ["出现最多的值是什么？", "What is the most frequently occurring value?"], ["众数", "mode"]],
      [["极差是最大值与最小值之差。", "The range is the maximum minus the minimum."], ["最大值减最小值是什么？", "What is the maximum minus the minimum?"], ["极差", "range"]],
    ],
    source: "https://studystash.com/en-gb",
  },
  // Veros
  "p_10349dcd577a3c99": {
    kind: "evidence",
    title: ["整理设立信托前的资产资料", "Prepare an asset inventory for a trust discussion"],
    instruction: ["从虚构家庭档案挑选资产与缺件，修订交接清单。", "Select assets and missing documents from the fictional household file."],
    result: ["待专业复核的资产清单", "Inventory for professional review"],
    rows: [
      [["档案 A：房契复印件已收到，所有权信息待核实。", "File A: deed copy received, title details unverified."], ["房产", "Property"], ["核对房契上的所有权信息。", "Verify title details on the deed."]],
      [["档案 B：经纪账户仅有旧对账单。", "File B: only an old brokerage statement is available."], ["投资账户", "Investment account"], ["索取近期对账单。", "Request a recent statement."]],
      [["档案 C：家庭联系人资料尚未确认。", "File C: family contact details are unconfirmed."], ["联系人", "Contact"], ["确认联系人及联系方式。", "Confirm contact details."]],
    ],
    source: "https://www.verostrust.com/",
  },
  // Winn.ai
  "737": {
    kind: "evidence",
    title: ["把销售通话里的承诺写回 CRM 草稿", "Capture sales-call commitments in a CRM draft"],
    instruction: ["从客户原话提取需求、负责人和下一步，修正记录。", "Capture needs, owners and next steps from the buyer’s words and correct the draft."],
    result: ["CRM 通话记录", "CRM call record"],
    rows: [
      [["客户：我们最想解决的是人工对账。", "Buyer: manual reconciliation is our biggest problem."], ["客户需求", "Buyer need"], ["减少人工对账。", "Reduce manual reconciliation."]],
      [["销售：我周五前把沙箱发给你。", "Rep: I will send you the sandbox by Friday."], ["下一步", "Next step"], ["销售周五前发送沙箱。", "Rep to send sandbox by Friday."]],
      [["客户：预算还需要财务主管批准。", "Buyer: our finance lead still has to approve the budget."], ["决策状态", "Decision status"], ["预算待财务主管批准。", "Finance lead approval pending."]],
    ],
    source: "https://winn.ai/",
  },
};
