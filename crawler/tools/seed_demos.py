#!/usr/bin/env python3
"""Write the hand-authored seed demos.

These five cover every tier, so the demo system works with no API key
configured and there is a known-good reference for what a generated spec should
look like. Each is validated with the same validator the API uses before it is
written - a seed that would be rejected at read time is a seed that never ships.

    python3 crawler/tools/seed_demos.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.services.demo_spec import SpecError, validate_spec  # noqa: E402

OUT_DIR = os.path.join(ROOT, "crawler", "data", "demos", "published")

# Sources are the ones already on each product record. Nothing here is invented:
# a figure is either cited to that record or flagged as example data.
EXA_SRC = "https://www.menlotimes.com/ai-robotics"
FIREWORKS_SRC = "https://techcrunch.com/2026/01/19/here-are-the-49-us-ai-startups-that-"
DALOOPA_SRC = "https://vcnewsdaily.com"
ROGO_SRC = "https://www.thisweekinfintech.com/p/rogo-s-160m-bet-on-agentic-ai-twif"
APPTRONIK_SRC = "https://wellows.com/blog/tech-startups/"


def loc(zh: str, en: str) -> dict:
    return {"zh": zh, "en": en}


def example(label_zh, label_en, value_zh, value_en):
    return {"label": loc(label_zh, label_en), "value": loc(value_zh, value_en),
            "evidence_ref": None, "is_example": True}


def sourced(label_zh, label_en, value_zh, value_en, ref):
    return {"label": loc(label_zh, label_en), "value": loc(value_zh, value_en),
            "evidence_ref": ref, "is_example": False}


SEEDS = [
    {
        "version": 1, "product_slug": "exa", "product_name": "Exa", "tier": "sandbox",
        "title": loc("当搜索理解语义", "When search understands meaning"),
        "premise": loc(
            "Exa 是为 AI 应用设计的搜索 API：用一句话描述你要找的东西，而不是猜关键词。",
            "Exa is a search API for AI apps: describe what you want in a sentence instead of guessing keywords."),
        "confidence": "verified",
        "evidence": [{"claim": "Exa raised a $250M Series C at a $2.2B valuation to build the search layer for AI agents.",
                      "source_url": EXA_SRC}],
        "steps": [
            {"id": "problem", "label": loc("问题", "The problem"),
             "narration": loc("关键词搜索找不到「像这样的公司」——它匹配的是字符串，不是含义。",
                              "Keyword search cannot find 'companies like this one'. It matches strings, not meaning."),
             "widget": {"type": "split_compare",
                        "input": "startups building developer tools for LLM evaluation",
                        "left": {"title": loc("关键词检索", "Keyword search"),
                                 "body": loc("标题里带「LLM evaluation」的博客文章、一个维基页面，以及三篇为这个词做过 SEO 的清单文。每条结果都是在「谈论」这个话题的文章。",
                                             "Blog posts titled 'LLM evaluation', a Wikipedia page, and three SEO listicles that rank for the phrase. Every result is an article about the topic.")},
                        "right": {"title": loc("语义检索", "Neural search"),
                                  "body": loc("这个类别里工具的公司主页。查询描述的是一类公司，所以返回的就是公司本身。",
                                              "Company homepages for tools in that category. The query described a kind of company, so the results are companies.")},
                        "takeaway": loc("同一个查询：一边返回讨论这个话题的文章，一边返回真正做这件事的公司。",
                                        "Same query. One side returns articles about the topic; the other returns the companies doing it.")}},
            {"id": "try", "label": loc("试一下", "Try it"),
             "narration": loc("选一个查询，看这类描述性问题会得到什么形状的结果。",
                              "Pick a query and see the shape of result a descriptive question returns."),
             "widget": {"type": "query_response", "mode": "cached", "allow_free_input": False,
                        "presets": [
                            {"query": "companies doing AI for industrial inspection",
                             "response": loc("返回的是公司主页，而不是行业媒体的报道——查询描述的是一类组织，所以回来的是实体而不是文章。",
                                             "Returns company homepages rather than trade-press coverage — the query names a kind of organisation, so entities come back instead of articles.")},
                            {"query": "research papers on speculative decoding since 2025",
                             "response": loc("返回论文页面。时间限定是语义的一部分，不需要你自己拼过滤条件。",
                                             "Returns paper landing pages. The date phrase is part of the meaning, not a filter you had to construct.")},
                            {"query": "personal blogs by people who left large AI labs",
                             "response": loc("返回个人博客。这正是关键词搜索最吃力的一类查询：这些页面之间没有共同关键词，只有共同的描述。",
                                             "Returns individual blogs. This is the query type keyword search handles worst: no shared keyword links these pages, only a shared description.")}]}},
            {"id": "wire", "label": loc("接进去", "Wire it up"),
             "narration": loc("三个阶段：检索、取正文、交给模型。省掉的是自建抓取和清洗那一层。",
                              "Three stages: retrieve, fetch contents, hand to a model. What it removes is your own crawling and cleaning layer."),
             "widget": {"type": "pipeline", "stages": [
                 {"name": loc("检索", "Search"),
                  "input": loc("一句描述你想找什么的话", "a sentence describing what you want"),
                  "output": loc("带相关度分数的 URL 排序列表", "ranked URLs with relevance scores")},
                 {"name": loc("取正文", "Contents"),
                  "input": loc("上一步返回的那些 URL", "those URLs"),
                  "output": loc("清洗过的页面正文——不必自己维护一套抓取栈", "cleaned page text — no scraping stack of your own to maintain")},
                 {"name": loc("生成", "Answer"),
                  "input": loc("正文加上你的 prompt", "that text plus your prompt"),
                  "output": loc("有依据的回答，每条结论都能指回出处", "a grounded answer that can cite where each claim came from")}]}}],
    },
    {
        "version": 1, "product_slug": "fireworks-ai", "product_name": "Fireworks AI", "tier": "sandbox",
        "title": loc("把开源模型当成一个端点", "Open models as one endpoint"),
        "premise": loc(
            "Fireworks 托管开源模型并按 token 计费，让你在不自建 GPU 集群的情况下切换模型。",
            "Fireworks hosts open models behind a per-token endpoint, so you can switch models without running GPUs."),
        "confidence": "verified",
        "evidence": [{"claim": "Fireworks AI raised a $250M Series C in Oct 2025 at a $4B valuation, as a platform for open-source model apps.",
                      "source_url": FIREWORKS_SRC}],
        "steps": [
            {"id": "choice", "label": loc("取舍", "The tradeoff"),
             "narration": loc("自建推理还是托管端点，差别不在模型本身，而在你要维护什么。",
                              "Self-hosting versus a managed endpoint. The model is the same; what differs is what you maintain."),
             "widget": {"type": "split_compare",
                        "input": "serve an open-weights model to production traffic",
                        "left": {"title": loc("自建", "Run it yourself"),
                                 "body": loc("自己开 GPU、按峰值容量规划、持续跟进推理框架版本，并在流量低谷时照付闲置成本。",
                                             "Provision GPUs, size them for peak, keep a serving stack current, and carry idle cost between traffic spikes.")},
                        "right": {"title": loc("托管端点", "Managed endpoint"),
                                  "body": loc("一次 HTTP 调用，按 token 计费。闲置不花钱，换模型只是改一个字符串。",
                                              "One HTTP call, priced per token. Idle costs nothing; a model swap is a string change.")},
                        "takeaway": loc("对流量不稳定的产品，差别主要体现在闲置成本和切换成本上，而不是原始速度。",
                                        "For bursty products the difference shows up as idle cost and switching cost, not raw speed.")}},
            {"id": "shape", "label": loc("成本形状", "Cost shape"),
             "narration": loc("按 token 计费意味着成本随用量线性变化。拖动看这条线的形状——数字是示例，用来说明关系。",
                              "Per-token pricing makes cost move linearly with usage. Drag to see the shape — the figures are examples that illustrate the relationship."),
             "widget": {"type": "param_dial",
                        "param": loc("每月请求量（万次）", "Monthly requests (tens of thousands)"),
                        "min": 1, "max": 100, "step": 1, "unit": "×10k",
                        "formula_note": loc("按 token 计费时成本随请求量线性增长；自建的成本由预置容量决定，和实际用量关系不大。",
                                            "Per-token cost rises linearly with volume; self-hosted cost is set by provisioned capacity and barely moves with usage."),
                        "outputs": [
                            example("托管成本走势", "Managed cost trend", "随请求量线性增长——闲置时接近零", "linear in requests — near zero when idle"),
                            example("自建成本走势", "Self-hosted cost trend", "固定且需预先承诺——用不用都要付", "flat and pre-committed — paid whether used or not")]}},
            {"id": "swap", "label": loc("换模型", "Swapping models"),
             "narration": loc("统一端点的实际价值：评估新模型的成本从一次迁移变成一次改字符串。",
                              "The real value of a uniform endpoint: evaluating a new model costs a string change instead of a migration."),
             "widget": {"type": "pipeline", "stages": [
                 {"name": loc("选模型", "Pick a model"),
                  "input": loc("一个模型标识符", "a model identifier"),
                  "output": loc("不论指定哪个开源模型，请求结构都一样", "same request shape regardless of which open model you name")},
                 {"name": loc("调用", "Call"),
                  "input": loc("prompt 和参数", "prompt plus parameters"),
                  "output": loc("按 token 计费的补全结果", "completion, billed per token")},
                 {"name": loc("对比", "Compare"),
                  "input": loc("同一个 prompt，换成第二个模型 id", "the same prompt against a second model id"),
                  "output": loc("同口径对比，不需要重新部署任何东西", "a like-for-like comparison without redeploying anything")}]}}],
    },
    {
        "version": 1, "product_slug": "daloopa", "product_name": "Daloopa", "tier": "simulation",
        "title": loc("财报数字进模型之前", "Before the numbers reach the model"),
        "premise": loc(
            "Daloopa 把公司财报里的明细数据结构化，供金融分析师直接接入模型，减少手工抄录。",
            "Daloopa turns filing-level financial detail into structured data an analyst can pull straight into a model, instead of re-keying it."),
        "confidence": "illustrative",
        "evidence": [{"claim": "Daloopa announced a $47M Series C for AI data infrastructure in finance.",
                      "source_url": DALOOPA_SRC}],
        "steps": [
            {"id": "who", "label": loc("谁在用", "Who it is for"),
             "narration": loc("同一份数据，不同岗位关心的部分完全不同。选一个看看。",
                              "The same dataset matters differently depending on the desk. Pick one."),
             "widget": {"type": "scenario_branch", "branches": [
                 {"persona": loc("股票研究分析师", "Equity research analyst"),
                  "situation": loc("要在财报发布当天更新模型里的分部数据。",
                                   "Needs segment-level detail updated in a model the day earnings drop."),
                  "outcome": loc("拿到已结构化的历史序列，把时间花在判断上，而不是抄数字。",
                                 "Gets an already-structured history and spends the time on judgment rather than transcription.")},
                 {"persona": loc("买方投资经理", "Buy-side portfolio manager"),
                  "situation": loc("想知道一家公司某项指标的口径是否中途变过。",
                                   "Wants to know whether a company quietly changed how it defines a metric."),
                  "outcome": loc("对齐后的历史序列会暴露口径变化，这类问题在 PDF 里很难发现。",
                                 "An aligned history exposes definition changes that are hard to spot reading PDFs.")},
                 {"persona": loc("数据工程师", "Data engineer"),
                  "situation": loc("要把财报数据接入内部系统，但不想维护解析器。",
                                   "Needs filing data in internal systems without maintaining parsers."),
                  "outcome": loc("以数据源的形式接入，解析和口径对齐由上游负责。",
                                 "Consumes it as a feed; parsing and alignment stay upstream.")}]}},
            {"id": "flow", "label": loc("这条链路", "The chain"),
             "narration": loc("要点在最后一步：数字能追回它在原始文件里的位置。",
                              "The point is the last stage: a number can be traced back to where it appeared in the filing."),
             "widget": {"type": "pipeline", "stages": [
                 {"name": loc("原始披露", "Filing"),
                  "input": loc("季报和年报原文", "quarterly and annual disclosures"),
                  "output": loc("上千个科目行，为人阅读排版，不是为机器", "thousands of line items, formatted for humans not machines")},
                 {"name": loc("结构化", "Structure"),
                  "input": loc("这些文件", "those documents"),
                  "output": loc("带类型的字段，跨期使用一致的标签", "line items as typed fields with consistent labels across periods")},
                 {"name": loc("对齐历史", "Align history"),
                  "input": loc("同一家公司的多个报告期", "many periods of the same company"),
                  "output": loc("即使公司自己改过列报方式，也能得到可比序列", "a comparable series even where the company changed its own presentation")},
                 {"name": loc("溯源", "Trace"),
                  "input": loc("任意一个数字", "any single figure"),
                  "output": loc("它来自哪份文件的哪个位置——这一步才让数据可审计", "the document and position it came from — the part that makes it auditable")}]}},
            {"id": "moment", "label": loc("省下的那步", "The step removed"),
             "narration": loc("下面是示意对话，用来说明这个产品替代掉的是哪一段工作，不代表真实界面。",
                              "An illustrative exchange showing which piece of work this replaces. Not a real interface."),
             "widget": {"type": "transcript", "turns": [
                 {"speaker": "user", "text": loc("我要这家公司过去五年的分部收入，按季度。",
                                                 "I need five years of segment revenue for this company, quarterly.")},
                 {"speaker": "product", "text": loc("已返回结构化序列，每个季度都关联到它来自的那份披露文件。",
                                                    "Structured series returned, with each quarter linked to the filing it came from.")},
                 {"speaker": "user", "text": loc("这段时间中间他们改过分部的名字。",
                                                 "The segment names changed in the middle of that period.")},
                 {"speaker": "product", "text": loc("序列已跨越这次变更对齐，口径发生变化的报告期会被标出来，而不是悄悄合并。",
                                                    "The series is aligned across the change, and the periods where the definition moved are marked rather than silently merged.")},
                 {"speaker": "user", "text": loc("FY23 Q2 这个数字是哪来的？", "Where did the FY23 Q2 figure come from?")},
                 {"speaker": "product", "text": loc("它对应到那个季度披露文件里的具体一行——这正是让数字可核对而不是只能选择相信的原因。",
                                                    "It resolves to the specific line in that quarter's filing — which is what makes the number checkable rather than trusted.")}]}}],
    },
    {
        "version": 1, "product_slug": "rogo", "product_name": "Rogo", "tier": "simulation",
        "title": loc("投行分析师的那份初稿", "The analyst's first draft"),
        "premise": loc(
            "Rogo 面向金融机构做分析 agent：处理研究流程里重复的取数与初稿环节。",
            "Rogo builds analysis agents for financial institutions, aimed at the repetitive retrieval and first-draft parts of research work."),
        "confidence": "illustrative",
        "evidence": [{"claim": "Rogo raised a $160M Series D; adoption reported among large financial institutions.",
                      "source_url": ROGO_SRC}],
        "steps": [
            {"id": "job", "label": loc("要做的事", "The job"),
             "narration": loc("这里的工作不是「回答问题」，而是把一份初稿做到可以被人接手修改。",
                              "The job is not answering a question. It is getting a draft to the point where a person can take it over."),
             "widget": {"type": "pipeline", "stages": [
                 {"name": loc("取数", "Gather"),
                  "input": loc("一个研究问题，加上该用户有权限的文档范围", "a research question and a permitted document set"),
                  "output": loc("相关的财报、材料和电话会记录，范围限定在该用户可见的部分", "the relevant filings, decks and transcripts, scoped to what the user may see")},
                 {"name": loc("抽取", "Extract"),
                  "input": loc("这些文档", "those documents"),
                  "output": loc("与问题相关的具体数字和表述", "the specific figures and statements that bear on the question")},
                 {"name": loc("成稿", "Draft"),
                  "input": loc("抽取出来的材料", "extracted material"),
                  "output": loc("结构化初稿，每条结论都挂着它的出处", "a structured draft with each claim attached to its source")},
                 {"name": loc("人工接手", "Handoff"),
                  "input": loc("这份初稿", "the draft"),
                  "output": loc("由分析师修改并署名——agent 不负责发布", "an analyst edits and signs off — the agent does not publish")}]}},
            {"id": "who", "label": loc("场景", "Where it lands"),
             "narration": loc("选一个场景，看这套流程替代掉的具体是哪一段。",
                              "Pick a situation to see which stretch of work this actually replaces."),
             "widget": {"type": "scenario_branch", "branches": [
                 {"persona": loc("初级分析师", "Junior analyst"),
                  "situation": loc("周一早上要交一份行业对比的初稿。",
                                   "Owes a first-pass sector comparison on Monday morning."),
                  "outcome": loc("初稿变成审阅对象，而不是从零开始的写作任务。",
                                 "The draft becomes something to review rather than something to start from nothing.")},
                 {"persona": loc("合规负责人", "Compliance lead"),
                  "situation": loc("需要确认模型只接触了该用户有权限的材料。",
                                   "Needs assurance the model only touched material this user is cleared for."),
                  "outcome": loc("权限在取数阶段生效，而不是在输出阶段过滤——这决定了这类产品能不能进机构。",
                                 "Permissions apply at retrieval, not as an output filter — which is what decides whether this can enter an institution at all.")}]}},
            {"id": "shape", "label": loc("对话形状", "Shape of the exchange"),
             "narration": loc("示意对话，说明产品的工作方式，不代表真实界面。",
                              "An illustrative exchange showing how the work flows. Not a real interface."),
             "widget": {"type": "transcript", "turns": [
                 {"speaker": "user", "text": loc("对比这四家公司在最近两次业绩电话会里怎么描述价格压力。",
                                                 "Compare how these four companies described pricing pressure in their last two earnings calls.")},
                 {"speaker": "product", "text": loc("已根据八份记录整理出初稿，每处描述都链接到它来自的原文段落。",
                                                    "Draft assembled from the eight transcripts, with each characterisation linked to the passage it came from.")},
                 {"speaker": "user", "text": loc("其中一家不在我的权限范围内。", "One of those wasn't in my entitlements.")},
                 {"speaker": "product", "text": loc("那家公司在取数阶段就被排除了，初稿会写明这一点，而不是默默只讲三家。",
                                                    "That company was excluded at retrieval, and the draft says so rather than quietly covering three.")},
                 {"speaker": "user", "text": loc("关于折扣的那个说法出自哪里？", "Where does the claim about discounting come from?")},
                 {"speaker": "product", "text": loc("它对应到具体某一段原文。如果那段原文支撑不了这个说法，该删的就是这个说法——所以初稿给的是链接，不是断言。",
                                                    "It resolves to a specific passage. If the passage does not support it, the claim is the thing to cut — which is why the draft carries links rather than assertions.")}]}}],
    },
    {
        "version": 1, "product_slug": "apptronik", "product_name": "Apptronik", "tier": "concept",
        "title": loc("人形机器人凭什么进工厂", "What gets a humanoid onto a factory floor"),
        "premise": loc(
            "Apptronik 做人形机器人 Apollo，与 NASA 及梅赛德斯-奔驰有合作。硬件无法在浏览器里演示，所以这里解释的是它所处的位置和判断它的方式。",
            "Apptronik builds the Apollo humanoid and works with NASA and Mercedes-Benz. Hardware cannot be demoed in a browser, so this explains where it sits and how to judge it."),
        "confidence": "inferred",
        "evidence": [{"claim": "Apptronik builds the Apollo humanoid robot, partners with NASA, and signed a cooperation with Mercedes-Benz.",
                      "source_url": APPTRONIK_SRC}],
        "steps": [
            {"id": "signal", "label": loc("该看什么", "What to read"),
             "narration": loc("人形机器人公司很少公布可比参数，所以「有没有具名的产业伙伴」比参数表更能说明进展。下表中只有见于来源的才标注出处，其余标为示例。",
                              "Humanoid companies rarely publish comparable specs, so a named industrial partner says more about progress than a spec sheet. Only cells backed by the source are cited; the rest are marked as examples."),
             "widget": {"type": "spec_matrix", "subject": "Apptronik (Apollo)",
                        "competitors": ["Other humanoid programs"],
                        "rows": [
                            {"spec": loc("具名产业伙伴", "Named industrial partner"),
                             "values": [sourced("Apptronik", "Apptronik", "与梅赛德斯-奔驰合作", "Mercedes-Benz cooperation", 0),
                                        example("同类项目", "Peer programs", "情况不一——往往未公开", "varies — often unannounced")]},
                            {"spec": loc("具名机构伙伴", "Named institutional partner"),
                             "values": [sourced("Apptronik", "Apptronik", "NASA 合作方", "NASA partner", 0),
                                        example("同类项目", "Peer programs", "情况不一", "varies")]},
                            {"spec": loc("公开可比参数", "Public comparable specs"),
                             "values": [example("Apptronik", "Apptronik", "本条记录中未公布", "not published in this record"),
                                        example("同类项目", "Peer programs", "很少公布", "rarely published")]}]}},
            {"id": "chain", "label": loc("它在链条哪一段", "Where it sits"),
             "narration": loc("人形机器人的难点很少在于「能不能动」，而在于后面几段。",
                              "The hard part of humanoids is rarely whether the robot moves. It is the stages after that."),
             "widget": {"type": "pipeline", "stages": [
                 {"name": loc("本体", "The machine"),
                  "input": loc("执行器、结构、动力", "actuators, structure, power"),
                  "output": loc("能站、能走、能举的机器人——多数项目都能走到这一步", "a robot that can stand, walk and lift — the part most programs reach")},
                 {"name": loc("任务能力", "Task capability"),
                  "input": loc("真实产线上的一个具体工序", "a specific job on a real line"),
                  "output": loc("稳定完成一个窄任务，多数项目卡在这里", "reliable completion of one narrow task, which is where most programs stall")},
                 {"name": loc("产线集成", "Line integration"),
                  "input": loc("既有的工厂流程", "an existing factory process"),
                  "output": loc("适配为人设计的工作流，并通过安全审批", "fitting a workflow built for humans, including safety sign-off")},
                 {"name": loc("单位经济", "Unit economics"),
                  "input": loc("单台成本对比它替代的人力成本", "cost per unit against the labour it offsets"),
                  "output": loc("决定能不能部署的那个数字——而且几乎没人公布", "the number that decides deployment — and the one almost nobody publishes")}]}},
            {"id": "econ", "label": loc("判断依据", "The judgment"),
             "narration": loc("对 PM 来说有用的不是参数，而是这个关系：单位成本要落到什么区间才谈得上规模化。数字为示例，用于说明关系。",
                              "The useful thing for a PM is not a spec but a relationship: where unit cost has to land before scale is even a conversation. Figures are examples that illustrate the relationship."),
             "widget": {"type": "param_dial",
                        "param": loc("单台成本（万美元）", "Cost per unit (US$10k)"),
                        "min": 5, "max": 50, "step": 1, "unit": "×$10k",
                        "formula_note": loc("回本周期约等于单台成本除以它每年替代的人力成本；成本下降时，可部署的岗位范围会非线性扩大。",
                                            "Payback is roughly unit cost divided by the annual labour it offsets; as cost falls, the range of viable jobs widens faster than the cost drops."),
                        "outputs": [
                            example("高成本区间", "At high unit cost", "只有连续运转的岗位才算得过账", "only jobs that run continuously can justify it"),
                            example("低成本区间", "At low unit cost", "单班和季节性工作开始成立", "single-shift and seasonal work start to qualify")]}}],
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")
    args = parser.parse_args()

    failures = 0
    validated = []
    for seed in SEEDS:
        try:
            validated.append(validate_spec(seed))
            print(f"  ok    {seed['product_slug']:14} tier={seed['tier']:10} steps={len(seed['steps'])}")
        except SpecError as error:
            failures += 1
            print(f"  FAIL  {seed['product_slug']:14} {error}")

    if failures:
        print(f"\n{failures} seed(s) failed validation. Nothing written.")
        return 1

    if args.dry_run:
        print(f"\nDry run: {len(validated)} seeds valid, nothing written.")
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    for spec in validated:
        path = os.path.join(OUT_DIR, f"{spec['product_slug']}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(spec, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(f"\nWrote {len(validated)} demos to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
