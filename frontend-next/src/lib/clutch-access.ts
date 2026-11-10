type Copy = { zh: string; en: string };
export type AccessTaskId = "debug" | "billing";
export type AccessDecision = "allowed" | "approval" | "denied";
type Request = { id: string; label: Copy; decision: AccessDecision; reason: Copy; content: Copy; authorized?: { reason: Copy; content: Copy } };
type Task = { id: AccessTaskId; label: Copy; scope: Copy; grant: Copy; requests: Request[] };
const copy = (zh: string, en: string): Copy => ({ zh, en });

export const CLUTCH_PRODUCT_ID = "p_16ab841852cd830c";

/** Illustrative local policies, not Clutch configuration or connected-system results. */
export const accessTasks: Record<AccessTaskId, Task> = {
  debug: {
    id: "debug",
    label: copy("排查测试库连接失败", "Debug a test database connection"),
    scope: copy("测试环境 · 只读排错", "Test environment · Read-only troubleshooting"),
    grant: copy("模拟临时授权：仅 sandbox-db 的只读连接检查", "Simulate a temporary grant: sandbox-db connection check, read-only"),
    requests: [
      { id: "config", label: copy("读取环境变量和部署配置", "Read environment values and deployment config"), decision: "allowed",
        reason: copy("排错需要地址、端口等非敏感配置；凭证值保持隐藏。", "Troubleshooting needs non-secret settings such as host and port. Credential values stay hidden."),
        content: copy("环境：test\nDB_HOST：sandbox-db\nDB_PORT：5443\nDB_PASSWORD：[由连接层管理，不返回原文]", "Environment: test\nDB_HOST: sandbox-db\nDB_PORT: 5443\nDB_PASSWORD: [managed by the connection layer; not returned]") },
      { id: "connection", label: copy("用测试凭证检查连接", "Check the connection using test credentials"), decision: "approval",
        reason: copy("需要使用测试库身份。先限定为本任务的只读连接，再由连接层代用凭证。", "This requires a test database identity. Scope it to this task's read-only connection before the connection layer uses the credential."),
        content: copy("尚未返回连接结果。", "No connection result is available yet."),
        authorized: { reason: copy("只允许本任务连接测试库；AI 收到检查结果，不收到密码。", "Only this task's test connection is allowed. The assistant receives the check result, not the password."),
          content: copy("连接检查：端口不匹配\n配置端口：5443\n测试服务端口：5432\n下一步：将测试配置端口改为 5432 后重试。", "Connection check: port mismatch\nConfigured port: 5443\nTest service port: 5432\nNext: change the test configuration to port 5432 and retry.") } },
      { id: "password", label: copy("把数据库密码显示在对话里", "Show the database password in the chat"), decision: "denied",
        reason: copy("排错不需要展示密码原文。连接授权也不包含向 AI 或对话返回凭证。", "Troubleshooting does not require the plaintext password. A connection grant does not grant credential disclosure."),
        content: copy("不返回密码。可选择「用测试凭证检查连接」。", "No password returned. Choose the test connection check instead.") },
      { id: "production", label: copy("连接生产数据库", "Connect to the production database"), decision: "denied",
        reason: copy("当前任务只涉及测试环境。测试库授权不能扩大成生产权限。", "This task is limited to the test environment. Its grant cannot expand into production access."),
        content: copy("不连接生产库。生产操作需要另立任务并单独审批。", "No production connection. Production work needs a separate task and approval.") },
    ],
  },
  billing: {
    id: "billing",
    label: copy("解释指定客户的账单", "Explain an assigned customer's bill"),
    scope: copy("工单 T-104 · 仅客户 C-18", "Ticket T-104 · Customer C-18 only"),
    grant: copy("模拟临时授权：仅 C-18 的 INV-104 付款状态", "Simulate a temporary grant: C-18 bill INV-104 status only"),
    requests: [
      { id: "ticket", label: copy("读取当前工单和账单", "Read the assigned ticket and bill"), decision: "allowed",
        reason: copy("当前工单属于客户 C-18，账单内容是回答本次问题所需的信息。", "The assigned ticket belongs to C-18. Its bill is needed to answer this question."),
        content: copy("工单：T-104\n客户：C-18\n问题：这笔 120 元的账单是否已经付款？", "Ticket: T-104\nCustomer: C-18\nQuestion: Has this CNY 120 bill been paid?") },
      { id: "payment", label: copy("查询这张账单的付款状态", "Look up this bill's payment status"), decision: "approval",
        reason: copy("回答是否付款需要访问支付系统，但范围只限这张账单的状态。", "Answering this needs payment-system access, scoped to the status of this bill."),
        content: copy("尚未返回付款状态。", "No payment status is available yet."),
        authorized: { reason: copy("只返回 C-18 这张账单的付款状态，不返回完整支付资料。", "Only this C-18 bill's status is returned, without complete payment details."),
          content: copy("账单：INV-104\n金额：120 元\n状态：已付款\n可回复：这张账单已付款，无需重复支付。", "Bill: INV-104\nAmount: CNY 120\nStatus: Paid\nPossible reply: This bill is paid; no further payment is needed.") } },
      { id: "card", label: copy("读取完整银行卡号", "Read the full payment-card number"), decision: "denied",
        reason: copy("解释付款状态不需要完整卡号。付款状态授权也不开放这些资料。", "A full card number is unnecessary for explaining payment status. The status grant does not expose it."),
        content: copy("不返回完整卡号；仍可查询获授权账单的付款状态。", "No full card number returned. The authorized bill's status can still be checked.") },
      { id: "customers", label: copy("读取其他客户的支付记录", "Read other customers' payment records"), decision: "denied",
        reason: copy("其他客户不在 T-104 的任务范围内。当前授权不能跨客户使用。", "Other customers are outside ticket T-104. This grant cannot be used across customers."),
        content: copy("不返回其他客户记录。", "No other customer records returned.") },
    ],
  },
};

export function evaluateAccess(taskId: AccessTaskId, requestId: string, grant: AccessTaskId | null) {
  const request = accessTasks[taskId].requests.find(item => item.id === requestId);
  if (!request) throw new Error("Unknown sample access request");
  const authorized = request.decision === "approval" && grant === taskId ? request.authorized : undefined;
  return { decision: authorized ? "allowed" as const : request.decision,
    reason: authorized?.reason ?? request.reason, content: authorized?.content ?? request.content };
}
