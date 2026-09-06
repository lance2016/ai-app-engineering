# 20 可靠性、成本、部署与 LLMOps｜练习

## 练习 1：尊重 Retry-After

正文的重试对 429 用的是和超时一样的退避。真实的 429 响应通常带 `Retry-After` 头。给 `RateLimited` 加一个 `retry_after: float | None` 字段，有值时直接等这个时间，没有才用抖动退避。

验收：把 `FlakyModel` 的 429 改成带 `retry_after=0.03`，输出里那一次的等待时间正好是 0.03 秒而不是随机值。

<details><summary>答案</summary>

```python
class RateLimited(Exception):
    def __init__(self, msg: str, retry_after: float | None = None):
        super().__init__(msg); self.retry_after = retry_after

# in call_with_retry:
delay = exc.retry_after if isinstance(exc, RateLimited) and exc.retry_after else backoff(...)
```

供应商告诉你什么时候再来，就听它的。自己算的退避是没有这个信息时的兜底。

</details>

## 练习 2：令牌桶容量与滑动窗口

把正文令牌桶的 `capacity` 从 1 改成 5。解释为什么会出现 429，以及在什么样的下游限流形态下 `capacity=5` 才是安全的。

<details><summary>答案</summary>

桶开始是满的，5 个请求瞬间通过；紧接着桶以每秒 5 个的速度补充，第 6 个请求几毫秒后就拿到令牌。但下游的滑动窗口在同一秒内已经记了 5 个，于是拒绝。突发加稳态在窗口内叠加成 10 个。

如果下游是固定窗口（每个整秒清零）或按并发数限制，`capacity=5` 可能没问题。所以令牌桶参数要按下游的限流形态定，不是抄一个默认值。读一遍你用的供应商的限流文档，看它是 RPM、TPM 还是并发数。

</details>

## 练习 3：按租户限流

`02` 的桶是全局的。改成每个租户一个桶，全局再套一个总桶。构造一个场景：租户 A 发 20 个请求，租户 B 发 2 个，B 的两个请求不应该因为 A 而等待。

验收：B 的请求时间戳都在开头，A 的请求被 A 自己的桶排开。

<details><summary>提示</summary>

`dict[str, TokenBucket]`，按 `tenant_id` 取；`acquire` 时先拿租户桶再拿全局桶。顺序反了会让 A 占住全局令牌再在自己的桶前排队，B 还是会被挤。

</details>

## 练习 4：把预算检查挪到步后

正文的预算在每步开始前检查，所以会超出一步。改成每步计费后立刻检查，超了就停止并且**不把这一步的结果交给用户**。然后回答：哪种更合理？

<details><summary>答案</summary>

步后检查不会超支，但会浪费最后那一步的调用（钱花了，结果不用）。步前检查会超支最多一步，但每一步的结果都用上了。

对成本预算，步前检查加上"留出单步最大花费的余量"通常更合理，因为超支一小步比丢掉一次有效调用便宜。对硬性上限（比如合规要求的绝对封顶），步后检查加拒绝交付才是对的。区别在于预算是软目标还是硬约束。

</details>

## 练习 5：写一条 SLO 和它的告警

为一个客服 Agent 写一条延迟 SLO 和对应的告警规则。要求：SLO 用用户能感知的指标；告警不会因为单次抖动触发。

<details><summary>参考答案</summary>

SLO：30 天内 95% 的请求首 token 延迟低于 2 秒。

对应的错误预算是 5% 的请求可以超过 2 秒。告警不看瞬时 p95，看错误预算消耗速度：如果过去 1 小时超过 2 秒的请求比例超过 5% 的 14.4 倍（也就是按这个速度一天就烧完一个月的预算），触发紧急告警；如果过去 6 小时超过 6 倍，触发工单级告警。

这套倍数的推导在 Google SRE 手册里，本课延伸阅读有链接。重点是告警的单位是"预算消耗速度"，不是"指标越线"。

</details>
