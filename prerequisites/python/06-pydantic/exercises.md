# P06 Pydantic v2｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：给 User 加一个字段

在 `01_define_and_validate.py` 的 `User` 里加一个 `is_admin: bool = False`，然后用 `User(name="Ada", age=36, email="a@b.c", is_admin="yes")` 构造一次。

验收：程序不报错，打印出的 `is_admin` 是 `True`。再把 `"yes"` 改成 `"maybe"`，观察报错。

<details><summary>提示与答案</summary>

Pydantic 默认是"宽松模式"：`"yes"`、`"1"`、`"true"` 都会被转成 `True`；`"maybe"` 不认识，报 `Input should be a valid boolean, unable to interpret input`。想禁止这种自动转换，用 `ConfigDict(strict=True)`。

</details>

## 练习 2：写一个带约束的地址模型

定义 `Address`，字段：`city: str`（至少 1 个字符）、`zipcode: str`（正好 6 位数字，用 `pattern=r"^\d{6}$"`）、`floor: int | None = None`（如果给了必须大于 0）。分别用一组好数据和一组三个字段全错的数据构造。

验收：坏数据一次报出 3 条错误，每条的 `loc` 各不相同。

<details><summary>答案</summary>

```python
class Address(BaseModel):
    city: str = Field(min_length=1)
    zipcode: str = Field(pattern=r"^\d{6}$")
    floor: int | None = Field(default=None, gt=0)
```

`Field(default=None, gt=0)` 表示"可以不给，给了就要大于 0"。`errors()` 会把三条一起返回，这是 Pydantic 和"遇到第一个错就抛"的手写校验最大的区别。

</details>

## 练习 3：把模型返回的 JSON 变成对象

假设模型返回了这段字符串：`'{"order_id": "o_9", "items": [{"sku": "Z1", "qty": 0}]}'`。用 `03_nested_and_dump.py` 里的 `Order` 解析它，并给 `Item.qty` 加上 `gt=0` 的约束。

验收：解析失败，错误的 `loc` 是 `('items', 0, 'qty')`。

<details><summary>答案</summary>

`Order.model_validate_json(text)`。嵌套结构的 `loc` 是一条路径：`items` 列表的第 0 个元素的 `qty`。读懂这个路径，你就能定位模型输出里到底哪个位置错了，这在第 05 课把错误回喂给模型时很有用。

</details>

## 练习 4：看 schema 猜规则

不运行代码，看下面这段 JSON Schema，说出对应的 Pydantic 类怎么写：

```json
{"properties": {"q": {"type": "string", "minLength": 1}, "top_k": {"type": "integer", "default": 5, "maximum": 20}}, "required": ["q"]}
```

<details><summary>答案</summary>

```python
class Search(BaseModel):
    q: str = Field(min_length=1)
    top_k: int = Field(default=5, le=20)
```

`required` 里只有 `q`，所以 `top_k` 必须有默认值。`maximum` 对应 `le`。能双向读写 schema，就能读懂任何一家模型厂商文档里的工具定义。

</details>
