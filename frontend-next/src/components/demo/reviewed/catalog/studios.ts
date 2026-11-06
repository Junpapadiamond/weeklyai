import type { Task } from "../types";

export const tasks: Record<string, Task> = {
  // Agnes AI
  "771": {
    kind: "slides",
    title: ["把活动简报排成一张可修改的幻灯片", "Turn an event brief into an editable slide"],
    instruction: ["Agnes 能从简报制作幻灯片。在这张本地样稿中修改标题、要点和版式。", "Agnes can turn a brief into slides. Edit the headline, key point and layout in this local draft."],
    result: ["活动提案预览", "Event slide preview"],
    source: "https://agnes.ai",
  },
  // BioRender
  "p_6593d2e4daf31cb8": {
    kind: "diagram",
    title: ["画出细胞信号传递示意图", "Build a cell signaling figure"],
    instruction: ["在画布中加入或移去分子标注，查看配体、受体和细胞内信号的位置。", "Add or remove molecular annotations on a canvas showing a ligand, receptor and intracellular signal."],
    result: ["信号通路示意图", "Signaling pathway figure"],
    source: "https://www.biorender.com",
  },
  // ChipMango
  "p_f1235aa42ae2b834": {
    kind: "logic",
    title: ["在浏览器验证一个与门", "Verify an AND gate in a browser lab"],
    instruction: ["ChipMango 提供芯片设计与验证学习环境。切换两个引脚，观察与门输出和真值表。", "ChipMango offers chip design and verification learning environments. Toggle the input pins and check the AND gate against its truth table."],
    result: ["引脚状态与真值表", "Pin states and truth table"],
    source: "https://chipmango.com/",
  },
  // Duqu
  "p_351670ea439517fa": {
    kind: "advance",
    title: ["看发票垫款如何影响可用现金", "Model the cash released by an invoice advance"],
    instruction: ["修改发票面额与示例费用率，核对预付净额。", "Change the face value and illustrative fee to calculate net cash released."],
    result: ["示例预付净额", "Illustrative net advance"],
    source: "https://www.duqu.ai/",
  },
  // Legato
  "p_6ad50cb4bf699fc0": {
    kind: "mix",
    title: ["看听力眼镜如何突出面前的说话人", "Explore foreground speech in a hearing-glasses concept"],
    instruction: ["Legato 的眼镜帮助佩戴者在嘈杂环境里听清说话人。移动滑杆，对照两个声源的示意电平。", "Legato’s hearing glasses help a listener hear speech in noise. Move the slider to compare illustrative foreground and background levels."],
    result: ["声源电平示意", "Illustrative source levels"],
    source: "https://www.legatohearing.com/",
    concept: true,
  },
  // Namespace
  "p_a206b05fac257d83": {
    kind: "cache",
    title: ["让第二次构建复用第一次的产物", "Reuse artifacts from a previous build"],
    instruction: ["运行构建填充缓存，再改变源文件或依赖并重跑，查看哪些阶段重算。", "Build to populate a cache, change source or dependencies and rebuild to see which stages rerun."],
    result: ["构建轨迹", "Build trace"],
    source: "https://namespace.so",
  },
  // Orchids 1.0
  "1088": {
    kind: "builder",
    title: ["把一句需求变成能用的任务清单", "Turn a brief into a working task list"],
    instruction: ["Orchids 根据需求搭建应用。在这个本地清单样稿里改名称、添加任务，再勾选完成。", "Orchids builds apps from a brief. In this local checklist prototype, change the name, add a task and mark it complete."],
    result: ["应用预览", "App preview"],
    source: "https://www.orchids.app/blog/introducing-orchids-1-0",
  },
  // OSCP
  "p_3fec3b3edcde9e7e": {
    kind: "inertial",
    title: ["在失去卫星定位后推算轨迹", "Estimate a route after satellite fixes stop"],
    instruction: ["OSCP 的惯性传感器帮助设备在没有卫星定位时导航。改变假设的陀螺仪偏差，对照估计轨迹与参考路线。", "OSCP makes inertial sensors for navigation without satellite fixes. Vary the assumed gyro bias and compare the estimated path with the reference."],
    result: ["惯性推算轨迹", "Dead-reckoned path"],
    source: "https://www.oscp.com",
    concept: true,
  },
  // Peripheral Labs
  "p_924278a0941d8eae": {
    kind: "camera",
    title: ["从不同视角重看同一次传球", "Reframe the same pass from another viewpoint"],
    instruction: ["Peripheral 从多个视角重建体育场景。旋转这张简图，沿时间轴从不同角度追踪同一脚传球。", "Peripheral reconstructs sports scenes from multiple views. Rotate this diagram and scrub through the same pass from different angles."],
    result: ["球场重建示意", "Pitch reconstruction diagram"],
    source: "https://www.peripheral.so/",
    concept: true,
  },
  // Reliable Robotics
  "110": {
    kind: "redundancy",
    title: ["看一个传感器失效后还剩哪条链路", "Trace the remaining link after a sensor failure"],
    instruction: ["Reliable Robotics 开发飞机自动化系统。在简化架构里注入传感器故障，看看信号还有没有通路。", "Reliable Robotics develops aircraft automation systems. Inject a sensor failure in a simplified architecture and trace the remaining signal paths."],
    result: ["信号路径示意", "Signal path schematic"],
    source: "https://reliable.co/",
    concept: true,
  },
  // Restate
  "p_50ad83c1a36ba17a": {
    kind: "replay",
    title: ["让中断的订单从断点继续", "Resume an interrupted order from its checkpoint"],
    instruction: ["在扣款后模拟中断，再从日志恢复。对照从头重跑时的扣款次数。", "Interrupt an order after charging, then resume from its journal. Compare with a full restart."],
    result: ["订单执行日志", "Order execution journal"],
    source: "https://restate.dev",
  },
  // Seldon
  "11": {
    kind: "rollout",
    title: ["给新模型分一部分流量再决定是否回退", "Canary a new model before rolling it back"],
    instruction: ["为两个版本分配一批示例请求，对照已知失败样本计算错误数。", "Split a fixture batch between two model versions and count known failures before rolling back."],
    result: ["请求分布与错误数", "Traffic split and failures"],
    source: "https://seldon.io/",
  },
  // Tractable
  "10": {
    kind: "damage",
    title: ["把车身损伤标到估损草稿上", "Mark damaged panels in an appraisal draft"],
    instruction: ["Tractable 用车辆影像辅助估损。在虚构车身图上标记损伤，把需要复核的部位加入评估单。", "Tractable uses vehicle imagery to assist damage appraisals. Mark panels on a fictional vehicle and assemble the review sheet."],
    result: ["待复核部位", "Panels for review"],
    source: "https://tractable.ai/",
  },
};
