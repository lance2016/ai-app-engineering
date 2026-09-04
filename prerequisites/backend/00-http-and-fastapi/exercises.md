# B00 HTTP 与 FastAPI｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：加一个 DELETE 接口

在 `03_request_body_and_errors.py` 里加 `@app.delete("/items/{item_id}", status_code=204)`，从 `DB` 里删掉对应项；不存在时 404。在文件末尾用 `TestClient` 调一次。

验收：先 POST 创建一个，DELETE 它得到 204，再 GET 它得到 404。

<details><summary>答案</summary>

```python
@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    if item_id not in DB:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")
    del DB[item_id]
```

204 表示"成功，没有内容可返回"，所以函数返回 `None`。

</details>

## 练习 2：按角色放行

把 `04_dependency_injection.py` 里的 `TOKENS` 改成 `{"secret": ("ada", "admin"), "guest": ("bob", "viewer")}`，再写一个依赖 `require_admin`，它自己依赖 `current_user`，非 admin 时抛 403。给 `/orders` 换上它。

验收：`Bearer guest` 访问 `/me` 是 200，访问 `/orders` 是 403；`Bearer secret` 两个都是 200。

<details><summary>答案</summary>

```python
def require_admin(user: tuple = Depends(current_user)) -> str:
    name, role = user
    if role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return name
```

依赖可以依赖别的依赖，FastAPI 会按顺序解析。401 是"不知道你是谁"，403 是"知道你是谁但你不能做这个"，别混用。

</details>

## 练习 3：把流式接口的每一块变成 JSON

`05_sse_streaming.py` 现在每行是 `data: Hello`。改成 `data: {"token": "Hello", "index": 0}`，客户端读到后用 `json.loads` 解析并打印 `index`。

验收：客户端打印出 0 到 4，`[DONE]` 那一块 `index` 是 4。

<details><summary>提示</summary>

`yield f"data: {json.dumps({'token': word, 'index': i})}\n\n"`。客户端拿到的 `line` 以 `data: ` 开头，`json.loads(line[6:])`。真实的聊天接口都是这么发的，因为除了文本还要带上"这是第几块""是不是结束了"这类信息。

</details>

## 练习 4：读状态码判断该改谁

三个响应，分别说出问题在客户端还是服务端，以及你会先查什么：

1. `POST /chat` 返回 `422 {"detail": [{"loc": ["body", "session_id"], "msg": "Field required"}]}`
2. `GET /chat/abc` 返回 `500 Internal Server Error`
3. `POST /chat` 返回 `401 {"detail": "invalid token"}`

<details><summary>答案</summary>

1. 客户端。请求体少了 `session_id`，查前端发请求的代码。
2. 服务端。代码在处理时抛了未捕获的异常，查服务端日志和 traceback。一个健壮的服务不该让 500 裸露出去，应该 catch 后返回结构化错误。
3. 客户端，但可能是配置问题。token 没带或者过期，查请求头和 token 的来源。

看第一位数字先分清是谁的责任，能省掉大量互相扯皮的时间。

</details>
