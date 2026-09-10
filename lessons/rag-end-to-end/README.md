---
status: complete
structure: narrative
part: Part 3 知识与记忆
estimated_time: 约 2 小时
---

# 15 RAG 端到端

> RAG 可以拆成七个阶段：解析、切块、索引、检索、重排、生成、引用。每一阶段都可能出错，用户看到的通常只有「答错了」。这一课的目标不是把七步做得多好，而是让你能对一次答错说出「坏在第几步」，并且有数据证明。

<details class="case" markdown="1">
<summary>例子：问「数字商品能退款吗」，它答「7 天内可退」，政策原文里根本没这句</summary>

一个内部文档问答。用户问：数字商品能退款吗？

它答：「可以，7 天内可退，需要提供订单号。」后面带了引用 `[refund-policy@v1#3]`。

政策原文写的是两条：实体商品 7 天内可退；数字商品一经激活不予退款。

从这一次回答往回查，七步里有三步都能解释它，而且都说得通：

| 可能坏在 | 这个假设成立的话 |
|---|---|
| 切块 | 两条各有适用范围的规则被切进同一块，而「哪条管哪种商品」写在被切掉的小标题里，模型手上只剩两句并列的结论 |
| 检索 | 「数字商品」那一块没有进 top-k，模型只看到实体商品那条 |
| 生成 | 两块都在上下文里，模型挑了更常见的那条 |

光看这句回答，三个假设分不出来。分得出来只有一个办法：把 `refund-policy@v1#3` 的原文打出来，把这次检索的 top-k 打出来，把最后送进模型的那段上下文打出来。三样一摆，坏在第几步就是确定的。

而这三样，工单里那句「答错了」一样都没有。

!!! note "构造的例子"
    这段问答和这份退款政策是为讲清「按步定位」编的。

</details>

## 用户看到的只有一句“答错了”

用户只看到「答错了」，但原因可能是解析、切块、召回、重排、生成或引用任一步。把链路拆成可测的阶段，才能做有证据的优化。

## 检索链要能定位什么

- 能画出七步流水线，并为每一步说出一种典型失败和检测它的方法
- 能说清 BM25、向量检索、RRF 融合、引用校验各自解决什么问题
- 能用一个 golden set 算 Recall@k，改一个参数后判断哪一步变好、哪一步变坏

## 检索链建立在哪些基础上

- [04 Embedding 与向量检索基础](../embeddings-and-vector-search/README.md)：隔了九课，三条结论这一课直接要用——归一化之后余弦就是点积；切块大小决定召回粒度，改切块等于改召回；换 embedding 模型必须重建全部向量。忘了先回去翻一遍那一课的「怎么理解它」
- [05 Tool Calling](../tool-calling/README.md)：引用校验的思路和「模型输出是建议」一脉相承

## 把一次回答拆成七步

```mermaid
flowchart LR
    A[1 解析<br/>PDF/HTML → 文本] --> B[2 切块<br/>检索的最小单位]
    B --> C[3 索引<br/>BM25 倒排 + 向量]
    C --> D[4 检索<br/>词法 + 向量 → RRF]
    D --> E[5 重排<br/>少量候选，更贵的打分]
    E --> F[6 生成<br/>只从给定来源回答]
    F --> G[7 引用<br/>校验每条引用]
```

| 步 | 典型坏法 | 怎么发现 |
|---|---|---|
| 解析 | 表格变成乱序文字、页眉页脚混进正文 | 抽样看解析结果，不看最终答案 |
| 切块 | 太大：噪音多，分数平；太小：答案被撕开 | golden 短语是否还在同一块里；Recall@k 随块大小的变化 |
| 索引 | 文档更新了索引没更；权限字段没进索引 | 版本号和删除演练，第 17 课 |
| 检索 | 词法找不到同义改写；向量找不到精确数字和型号 | 分别算 BM25 和向量的 Recall@k，看各自漏什么 |
| 重排 | 重排器和检索器口径不一致，把对的排下去 | 重排前后 Recall@k 对比 |
| 生成 | 模型用了自己的知识而不是来源；来源里没有答案时硬编 | 引用率；「来源不含答案」的 golden 用例 |
| 引用 | 编造不存在的引用 id；引用和句子对不上 | 代码校验 |

### 有些文档根本没有文本层

扫描件、截图、拍下来的表格，抽取出来是空的或一堆乱码，后面六步全都白做。三条路：OCR 转成文字后照常走流水线；版面解析把表格和阅读顺序还原成结构（跨行跨列的表格尤其需要，OCR 会把它拍平成一行行碎字）；或者把整页图直接交给视觉模型。**前两条把图变成文本，后面六步一行都不用改；第三条要另搭一套。** 在纯文本的流水线里，一张没抽出文字的图确实进不了 BM25 索引，引用也无从指起。这是这套流水线的限制，并非「图没法检索」：把整页渲染成图走图文向量、或者先用视觉模型抽成结构化字段再入库，都能检索；引用相应地改成指页码、区域坐标或资源 id，不再是文本块 id。代价是多一套索引、多一种引用形态，评测也得重做一遍。先问一句这批文档值不值得。

### 检索这一步要两条腿走路

[BM25](https://en.wikipedia.org/wiki/Okapi_BM25) 匹配精确词，擅长型号、数字、专有名词，对同义改写无能为力。向量匹配语义，擅长改写，但对「3 到 5 天」和「1 到 2 天」这种只差数字的句子分辨力弱。

### 引用是生成阶段的校验

模型说「来源 `[refund-policy@v1#0]` 支持这句话」，这和第 05 课模型说「我调用了工具」是同一类陈述：一个建议，需要代码去核实。

### Agentic RAG 就是这条流水线加上第 06 课的循环

模型看到检索结果觉得不够，改写查询再查一次，或者换一个数据源。它没有改变七步里任何一步的坏法，只是让流水线可以跑多轮。**先把单轮做对。**

```mermaid
flowchart LR
    classDef model stroke:#7c6ee6,stroke-width:2.2px
    classDef runtime stroke:#0d806b,stroke-width:2px
    classDef data stroke:#4e83a3,stroke-width:1.8px
    classDef risk stroke:#b5472d,stroke-width:2px
    S[源文档] --> I[(索引)]
    I --> Q[检索]
    Q --> C{候选相关?}
    C -- 否 --> F1([召回失败])
    C -- 是 --> G[生成]
    G --> V{引用可验证?}
    V -- 否 --> F2([生成 / 引用失败])
    V -- 是 --> O([带来源回答])
    class S,I data
    class Q,C,V runtime
    class G model
    class F1,F2 risk
```

## 从文档进入，到引用出去

### 一、切块要看语义边界，不只看长度

```python
SENTENCE = re.compile(r"(?<=[.!?])\s+|(?<=[。！？])")

def units(text: str, max_chars: int) -> list[str]:
    """按段落切；单个段落超长时，退到句子级。"""
    out = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para or para.startswith("#"):
            continue
        out += SENTENCE.split(para) if len(para) > max_chars else [para]
    return out

def chunk_document(doc, version, text, max_chars, overlap_units=1) -> list[Chunk]:
    """把整段（或整句）攒到 max_chars，末尾几个单位带进下一块作为重叠。"""
    chunks, current = [], []
    for unit in units(text, max_chars):
        if current and len("\n\n".join(current + [unit])) > max_chars:
            chunks.append(Chunk(f"{doc}@v{version}#{len(chunks)}", doc, "\n\n".join(current)))
            current = current[-overlap_units:] if overlap_units else []
        current.append(unit)
    if current:
        chunks.append(Chunk(f"{doc}@v{version}#{len(chunks)}", doc, "\n\n".join(current)))
    return chunks
```

关键在 `units()`：以完整的段落或句子为最小单位，`max_chars` 只是攒够多少就切。固定字符数硬切会把「1 到 2 个工作日」切成「1 到」和「2 个工作日」——两边都答不了问题。

`overlap_units=1` 让相邻块共享一个段落。收益是跨段落的答案不会被切口吞掉，代价是索引变大——大多少取决于块大小和重叠策略：块大、只重叠一个短段落，可能只多几个百分点；块小、或者按句重叠好几句，多出三成也不奇怪。别背固定比例，入库前后数一下块数就知道。

`Chunk.id` 用 `"<doc>@v<version>#<n>"` 的形式，因为它最后要变成给用户看的引用；版本写进 id，旧版本和新版本不会混淆。

### 二、BM25：二十几行，值得亲手写一遍

```python
class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query, i) -> float:
        d, dl = self.docs[i], self.lengths[i]
        s = 0.0
        for t in tokenize(query):
            if t not in d:
                continue
            tf = d[t]
            s += self.idf[t] * tf * (self.k1 + 1) / (
                 tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
        return s
```

两个参数的含义值得记住：`k1` 控制词频饱和（一个词出现 10 次不该比出现 5 次强一倍），`b` 控制文档长度惩罚（长文档天然含更多词，要打折）。1.5 / 0.75 可以作为常见的起点，最终仍要用自己的语料调。

生产里用 PostgreSQL 的 `tsvector` 或 Elasticsearch，不用自己写。但知道它在算什么，才能解释「为什么这篇明明包含关键词却排在后面」。

### 三、RRF：只看名次，不看分数

```python
def rrf(*rankings: list[int], k: int = 60) -> list[int]:
    """Reciprocal Rank Fusion：每个文档的得分是各排名倒数之和。"""
    scores = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

BM25 的分数是几点几，没有上界；余弦相似度的取值范围是 -1 到 1（文本 embedding 算出来的多数落在 0 以上那半边，但这只是经验，不是保证）。量纲和范围都对不上，两者没法直接加。RRF 只用名次，所以不需要把两种分数拉到同一尺度——这是它成为常用融合方法的原因。

`k=60` 是论文里的经验值。它的作用是压平头部差距：第 1 名和第 2 名的分差不会大到让另一个检索器完全说不上话。

### 四、重排：候选少了，可以用更贵的打分

```python
def rerank(query, candidates, top_n=3) -> list[Chunk]:
    """真实系统用 cross-encoder；这里用二元组重叠做示意。"""
    q = tokenize(query)
    bigrams = {(a, b) for a, b in zip(q, q[1:])}

    def score(c):
        t = tokenize(c.text)
        hits = sum(1 for a, b in zip(t, t[1:]) if (a, b) in bigrams)
        return hits + 0.01 * sum(1 for w in q if w in t)   # 二元组为主，单词为辅

    return sorted(candidates, key=score, reverse=True)[:top_n]
```

重排的价值在于**它能看整个查询和整段文本的交互**，而检索阶段的向量是各自独立编码的。真实的 cross-encoder 把查询和候选拼在一起过一遍模型，每个候选都要一次推理——所以候选数必须先被检索压到几十个。

### 五、引用校验：id 存在还不够

```python
CITATION = re.compile(r"\[([A-Za-z0-9_.\-/]+@v\d+#\d+)\]")

def verify(answer: str, ctx: list[Chunk]) -> list[str]:
    by_id = {c.id: c for c in ctx}
    problems = []
    for sentence in re.split(r"(?<=[.!?])\s+|(?<=[。！？])", answer):
        for cid in CITATION.findall(sentence):
            if cid not in by_id:
                problems.append(f"[{cid}] 根本没被检索到")     # 编造的引用
                continue
            words = set(tokenize(CITATION.sub("", sentence))) - STOPWORDS
            if len(words & set(tokenize(by_id[cid].text))) < 2:
                problems.append(f"[{cid}] 支撑不了这句话: {sentence!r}")   # 挂错了
    if not CITATION.search(answer):
        problems.append("完全没有引用")
    return problems
```

**只检查 id 存在是不够的。** 模型可以把任何一句话挂在任何一个真实 id 后面，看起来有据可查，实际上是拼贴。第二道检查（词汇重叠）虽然粗糙，但能拦住一部分明显不相干的引用；它不是语义蕴含证明，仍需要 golden set 和人工抽样。

系统提示词那边要配合：

```python
system = ("Answer only from the sources below. After each sentence cite the "
          "source id in square brackets. If the sources do not contain the "
          "answer, say so.")
```

最后那句「来源里没有就直说」必须有，否则模型会用自己的知识补全。

### 六、Recall@k：所有调参的前提

```python
def recall_at_k(retriever, golden, chunks, ks=(1, 3, 5)) -> dict[int, float]:
    hits = {k: 0 for k in ks}
    for g in golden:                      # {"q": "...", "must_contain": "关键短语"}
        ranked = retriever(g["q"])
        for k in ks:
            if any(g["must_contain"] in chunks[i].text for i in ranked[:k]):
                hits[k] += 1
    return {k: hits[k] / len(golden) for k in ks}
```

参考项目 M4 用 31 条 golden 问答、`max_chars=600` 跑出的基线如下。它是这套示例语料和 hashing embedding 的结果，换一批语料后要重新计算。

!!! note "参考实现基线"
    数字取自 [M4 RAG 与 Memory](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m4-rag-and-memory/README.md)（核对日期 2026-09-10）。内存后端和 PostgreSQL 后端的差异来自 BM25 与 `ts_rank` 的实现、向量排序的浮点精度。

    | 检索器 | 内存后端 R@1 / R@3 / R@5 | PostgreSQL 后端 R@1 / R@3 / R@5 |
    |---|---|---|
    | text（BM25 / tsvector） | 0.74 / 0.87 / 0.90 | 0.71 / 0.84 / 0.90 |
    | vector（hashing） | 0.42 / 0.74 / 0.81 | 0.45 / 0.74 / 0.84 |
    | hybrid（RRF） | 0.65 / 0.84 / 0.90 | 0.65 / 0.84 / 0.87 |

**这张表是调参时的参照物。换语料、切块策略或 embedding 模型后要重新计算。**

## 每一步会怎样坏

**用弱向量得出「hybrid 更好」的结论。** 上表里 hybrid 的 R@1 比纯 BM25 还低——因为玩具向量把 how、is 这些词也算进相似度，噪音拖累了融合。这不是 RRF 的问题，而是弱检索器参与融合后的结果。换成真实 embedding 模型后排序可能变化，但**你必须重新测**，不能沿用别人的结论。

**切块只看大小不看边界。** 见第一节。

**对着没有文本层的 PDF 调切块参数。** 解析出来就是乱的，块怎么切都不对。「怎么理解它」那张表第一行说的就是这件事：抽样打开解析结果看一眼，比调三天参数快。

**引用校验只检查 id 存在。** 见第五节。

**golden set 里只有能答的问题。** 真实系统必须有几个「来源里没有答案」的用例，看模型是不是老实说不知道。只测能答的问题，等于没测幻觉。

## 召回、成本和可解释性

- **块大小。** 小块检索精确、上下文少；大块上下文全、分数平。经验起点是 300～800 字符加一段重叠，然后用 Recall@k 在自己的语料上调出来。
- **图表和表格：转成文本，还是保留原图。** 转文本便宜、可检索、能给到块级引用，但复杂表格和图示会丢信息；保留原图交给视觉模型信息最全，代价是每次都要重看一遍图（贵且慢），引用只能到页。常见做法是两者都留：文本进索引负责召回，命中之后需要时再把原图一起给模型。
- **BM25 还是向量还是都要。** 只有 BM25，同义改写会漏；只有向量，型号和数字会混。都要就多一套索引和一次融合。语料里精确标识符多的（法规、技术手册）BM25 权重要高。
- **重排的代价。** cross-encoder 把候选数从几十压到几个，可能提升排序质量，但每个候选都要过一次模型。候选取多少是延迟和召回的直接权衡，通常从 20～50 起测。
- **pgvector 还是专用向量库。** pgvector 让一个库同时放业务数据和向量，少一个组件，权限过滤可以用 SQL 的 `WHERE`。到千万级向量、或者需要复杂过滤加近邻组合时，再评估专用库。

## 把检索链变成可验收的流水线
- **每次检索都要留证据**：查了什么、召回了哪些块、融合前后的名次、最终给模型看的是哪几块。回答错了，这份证据决定你去修哪一步。
- **引用校验的结果要落库**，不只是拦截。引用失败率的趋势是模型质量的一个先行指标。
- **权限必须进索引**。检索时用 `WHERE tenant_id = ?` 过滤，不要检索完再在应用层筛——后者会让 top-k 被无权访问的文档占满。
- **Recall@k 进 CI 门禁。** 设一个阈值（比如 R@5 ≥ 0.85），跌破就不合并。切块参数、embedding 模型、检索权重都是会被人「顺手优化」的东西。
- **怎么测：检索和生成分开量。** 检索层看 Recall@k（该召回的召回了几成）和 Hit@k（前 k 条里至少有一条对的吗），这两个数字回答的不是同一个问题，别混用：单文档问答 Hit@5 很好看，多文档汇总就得看 Recall@5。生成层看引用是否真的支撑了那句话。哪一层掉了先修哪一层。

## 框架提供检索，还是只提供接缝

| 本课概念 | LangGraph | OpenAI Agents SDK | Claude Agent SDK |
|---|---|---|---|
| 检索管线 | LangChain 的 retriever + 图节点 | 内置 file search，或自写检索工具 | MCP 检索 server 或自写工具 |
| 混合检索 | `EnsembleRetriever` | 自己写 | 自己写 |
| 引用校验 | 自己写 | 内置 file search 带引用 | 自己写 |

托管的 file search 省事，但切块过程和部分检索细节由供应商控制；即使能把搜索结果带回，也不等于拿到了自己的 chunk 和完整 Recall@k 测量链。数据是核心资产时，这一层建议自己掌控。官方文档：[LangGraph](https://langchain-ai.github.io/langgraph/) · [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) · [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)（核对日期 2026-09-10）。

## 跑一条带引用的问答

参考项目的 Playground 右侧有知识库面板。先启动确定性检索场景：

```bash
AIAPP_DEMO_SCENARIO=rag-citation \
  uv run uvicorn aiapp.api.app:create_app --factory --port 8000
```

在知识库面板填入文档 ID `refund-policy`、版本 `1`，正文写一条退款规则，再点击“导入”和“检索”。这样返回的块才会和演示回答里的 `[refund-policy@v1#0]` 对上。回到左侧线程发送同一个问题，模型会请求 `search_knowledge`，运行结束后事件流会追加 `citations_checked`。这个事件由 [`api/routes/threads.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/routes/threads.py) 从本轮工具结果重建来源，再调用 [`knowledge/citations.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/citations.py) 校验。

要复现坏引用，运行 [引用测试](https://github.com/lance2016/ai-app-engineering-ref/blob/main/tests/project/m4/test_citations.py) 中的 `test_made_up_and_unsupported_citations_are_flagged`。测试故意让回答引用未检索到的编号；回答仍然可以生成，但验收事件会明确标记它没有证据。这是“能回答”和“回答有来源”的区别。

## 参考实现里的引用校验

切分与增量入库在 [`knowledge/ingest.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/ingest.py)，混合检索和 RRF 在 [`hybrid.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/hybrid.py)，两路检索的装配在 [`retriever.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/retriever.py)，引用校验在 [`citations.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/citations.py)。参考项目当前没有 cross-encoder 重排；课程里的重排是接在 RRF 之后的扩展位置。模型写的引用是待核实的声明，指不到本次检索到的块就打回。用例在 [`m4/test_citations.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/tests/project/m4/test_citations.py)，全貌见 [M4 RAG 与 Memory](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m4-rag-and-memory/README.md)。

## 从引用校验继续读 RAG

- [Lewis 等 · Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)（访问日期 2026-09-04）：RAG 一词的出处。读摘要和图 1 就够，理解「检索器和生成器是两个可以分别评测的组件」。
- [Okapi BM25](https://en.wikipedia.org/wiki/Okapi_BM25)（访问日期 2026-09-04）：公式和 `k1`、`b` 两个参数的含义。上面那段代码就是这一页的直译。
- [pgvector](https://github.com/pgvector/pgvector)（访问日期 2026-09-04）：索引类型（HNSW、IVFFlat）和距离函数。
- [docling](https://github.com/docling-project/docling)（访问日期 2026-09-06）与 [marker](https://github.com/datalab-to/marker)（访问日期 2026-09-06）：两个把 PDF 转成结构化 Markdown 的开源项目，拿自己的脏文档各跑一遍，比读任何解析器对比都直接。
- [generative-ai-for-beginners · 15 RAG and Vector Databases](https://github.com/microsoft/generative-ai-for-beginners/blob/main/15-rag-and-vector-databases/README.md)（访问日期 2026-09-04）：通识版的七步，附一个 notebook。
- [ai-agents-for-beginners · 05 Agentic RAG](https://github.com/microsoft/ai-agents-for-beginners/blob/main/05-agentic-rag/README.md)（访问日期 2026-09-04）：多轮检索的动机、失败模式和边界。读完本课再看，你会发现它讨论的所有问题都能落到七步中的某一步。

---

[← 上一课 14](../agent-harness/README.md) · [下一课 16 →](../memory/README.md)
