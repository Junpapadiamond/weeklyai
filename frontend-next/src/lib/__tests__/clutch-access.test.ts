import { describe, expect, it } from "vitest";
import { accessTasks, evaluateAccess } from "../clutch-access";

describe("local task-scoped access illustration", () => {
  it("allows non-secret configuration without exposing a password", () => {
    const result = evaluateAccess("debug", "config", null);
    expect(result.decision).toBe("allowed");
    expect(result.content.en).toContain("DB_PORT: 5443");
    expect(result.content.en).toContain("not returned");
  });

  it("requires a task-specific grant for necessary protected requests and supports revocation", () => {
    for (const task of Object.values(accessTasks)) {
      const request = task.requests.find(item => item.decision === "approval")!;
      expect(evaluateAccess(task.id, request.id, null).decision).toBe("approval");
      expect(evaluateAccess(task.id, request.id, task.id).decision).toBe("allowed");
      expect(evaluateAccess(task.id, request.id, task.id === "debug" ? "billing" : "debug").decision).toBe("approval");
      expect(evaluateAccess(task.id, request.id, null).decision).toBe("approval");
    }
  });

  it("never turns a temporary grant into secret, production, or cross-customer access", () => {
    for (const task of Object.values(accessTasks)) {
      for (const request of task.requests.filter(item => item.decision === "denied")) {
        expect(evaluateAccess(task.id, request.id, task.id).decision).toBe("denied");
      }
    }
  });

  it("returns a useful task result in both languages after the scoped grant", () => {
    const debug = evaluateAccess("debug", "connection", "debug");
    expect(debug.content.zh).toContain("5432");
    expect(debug.content.en).toContain("5432");
    const billing = evaluateAccess("billing", "payment", "billing");
    expect(billing.content.zh).toContain("已付款");
    expect(billing.content.en).toContain("Paid");
  });

  it("does not fall back to an allowed request for unknown or mismatched requests", () => {
    expect(() => evaluateAccess("billing", "connection", "billing")).toThrow("Unknown sample access request");
  });
});
