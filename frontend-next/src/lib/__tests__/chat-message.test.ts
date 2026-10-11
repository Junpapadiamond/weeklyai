import { renderToStaticMarkup } from "react-dom/server";
import { createElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { ChatMessageBubble } from "@/components/chat/chat-message";

vi.mock("@/components/layout/locale-provider", () => ({
  useSiteLocale: () => ({ t: (zh: string) => zh }),
}));

function render(content: string) {
  return renderToStaticMarkup(createElement(ChatMessageBubble, { message: { id: "answer", role: "assistant", content } }));
}

describe("research answer source links", () => {
  it.each([
    ["Myca (https://www.myca.ag/)", "https://www.myca.ag/", ")"],
    ["官网（https://www.myca.ag/）。", "https://www.myca.ag/", "）。"],
    ["Read https://example.com/release.", "https://example.com/release", "."],
    ["See (https://example.com/AI_(tool)).", "https://example.com/AI_(tool)", ")."],
  ])("keeps prose punctuation outside %s", (content, href, suffix) => {
    const html = render(content);
    expect(html).toContain(`href="${href}"`);
    expect(html).toContain(`>${href}</a>${suffix}`);
  });

  it("renders named source links", () => {
    expect(render("[资料来源](https://example.com/release)")).toContain(
      'href="https://example.com/release" target="_blank" rel="noopener noreferrer">资料来源</a>',
    );
  });

  it("does not accept HTML or executable links from the model", () => {
    const html = render('<script>alert(1)</script> [link](javascript:alert(1))');
    expect(html).not.toContain('<script>');
    expect(html).not.toContain('href=');
  });
});
