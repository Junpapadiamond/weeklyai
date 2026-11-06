import type { Task } from "../types";

export const tasks: Record<string, Task> = {
  // Adaption Labs
  "788": {
    kind: "learning",
    title: ["看新标注如何改变下一次预测", "See how feedback changes the next prediction"],
    instruction: ["Adaption 研究让模型随新数据调整的方法。试着补一条标注，看同批请求的最近邻分类如何改变。", "Adaption researches models that adapt to new data. Add a label to see how a nearest-neighbor classifier changes its answers."],
    result: ["请求分类回放", "Classification replay"],
    axis: ["示例请求长度（词）", "Sample request length (words)"],
    classes: [["简短答复", "Short reply"], ["详细答复", "Detailed reply"]],
    train: [
      [6,0],
      [34,1],
      [15,1],
    ],
    tests: [
      [8,0],
      [16,1],
      [30,1],
    ],
    source: "https://adaptionlabs.ai/",
    concept: true,
  },
  // AMI Labs
  "793": {
    kind: "path",
    title: ["在小世界里检验下一步预测", "Test next-state predictions in a small world"],
    instruction: ["AMI 研究能预测动作后果的世界模型。给这个格子世界追加动作，观察遇墙后的下一状态。", "AMI researches world models that predict the consequences of actions. Append a move and see what happens when a wall is in the way."],
    result: ["预测轨迹", "Predicted trajectory"],
    target: ["目标格", "Goal"],
    obstacle: ["墙", "Wall"],
    goal: 9,
    walls: [5,6],
    source: "https://amilabs.xyz/",
    concept: true,
  },
  // Autoheal
  "p_bf3a5bc707e82f13": {
    kind: "patch",
    title: ["修好会丢任务的重试策略", "Repair a retry policy that drops jobs"],
    instruction: ["Autoheal 帮团队持续改进软件代理。把重试补丁应用到同一批失败任务，核对它救回了哪些任务。", "Autoheal helps teams improve software agents. Apply a retry patch to the same failed jobs and check which ones recover."],
    result: ["工作流回归结果", "Workflow regression results"],
    variant: "retry",
    original: ["attempts = 1", "attempts = 1"],
    fix: ["attempts = 3", "attempts = 3"],
    tests: [
      [0,1],
      [1,1],
      [4,0],
    ],
    source: "https://autoheal.ai/",
  },
  // CodeRabbit
  "p_5624c882190ab1b8": {
    kind: "patch",
    title: ["复现代码审查发现的越界错误", "Reproduce a boundary bug found in review"],
    instruction: ["审查库存扣减补丁，运行三个测试看缺陷能否复现。", "Review the stock deduction patch and run three tests to reproduce the bug."],
    result: ["库存函数测试", "Stock function tests"],
    variant: "stock",
    original: ["remaining = 5 - ordered", "remaining = 5 - ordered"],
    fix: ["remaining = max(0, 5 - ordered)", "remaining = max(0, 5 - ordered)"],
    tests: [
      [2,3],
      [5,0],
      [7,0],
    ],
    source: "https://www.coderabbit.ai/",
  },
  // Feather Robotics
  "p_26d7ea8ef443ce8a": {
    kind: "path",
    title: ["为移动机器人规划一条取料路线", "Plan a mobile robot’s route to a parts bin"],
    instruction: ["Feather 是可移动的双臂机器人平台。在简化工位图上追加移动命令，避开夹具接近料箱。", "Feather is a mobile, two-armed robotics platform. Append moves on a simplified workcell map to reach the bin without hitting fixtures."],
    result: ["机器人位置", "Robot position"],
    target: ["料箱", "Parts bin"],
    obstacle: ["夹具", "Fixture"],
    goal: 14,
    walls: [6,10],
    source: "https://feather.dev/",
    concept: true,
  },
  // Flapping Airplanes
  "513": {
    kind: "learning",
    title: ["多少训练样本才够区分这组信号？", "How many examples separate these signals?"],
    instruction: ["这家研究实验室探索如何用更少数据学习。增减最近邻实验的标注信号，核对三条留出样本的预测。", "This lab studies how to learn from less data. Toggle labeled signals in a nearest-neighbor experiment and check three held-out predictions."],
    result: ["留出集预测", "Held-out predictions"],
    axis: ["信号周期（格）", "Signal period (ticks)"],
    classes: [["短周期", "Short cycle"], ["长周期", "Long cycle"]],
    train: [
      [2,0],
      [12,1],
      [7,1],
    ],
    tests: [
      [3,0],
      [6,1],
      [11,1],
    ],
    source: "https://www.indexventures.com/companies/flapping-airplanes/",
    concept: true,
  },
  // Hang Ten Systems
  "p_4cf4af5293850191": {
    kind: "patch",
    title: ["检查旧结算逻辑迁移后是否一致", "Check billing behavior during a legacy migration"],
    instruction: ["Hang Ten 为企业改造旧软件。把账单从整元截断改为按美分入账，核对迁移后的测试结果。", "Hang Ten modernizes legacy enterprise software. Replace whole-dollar truncation with cent-based billing and check the migration tests."],
    result: ["迁移回归结果", "Migration regression results"],
    variant: "cents",
    original: ["cents = trunc(dollars) × 100", "cents = trunc(dollars) × 100"],
    fix: ["cents = round(dollars × 100)", "cents = round(dollars × 100)"],
    tests: [
      [2,200],
      [4.75,475],
      [9.99,999],
    ],
    source: "https://hangten.ai/",
  },
  // Quaddle
  "p_fd51b435bff0cf5c": {
    kind: "path",
    title: ["给桌面机器狗编一串走位动作", "Program a desktop robot dog’s movement blocks"],
    instruction: ["把方向动作接进程序，看机器狗在桌面示意图上如何走到垫子。", "Append directional blocks to move the robot dog to the mat on a tabletop diagram."],
    result: ["动作程序与落点", "Motion program and endpoint"],
    target: ["垫子", "Mat"],
    obstacle: ["积木", "Block"],
    goal: 11,
    walls: [5,9],
    source: "https://www.petoi.com/pages/quaddle-educational-robot-kit",
    concept: true,
  },
};
