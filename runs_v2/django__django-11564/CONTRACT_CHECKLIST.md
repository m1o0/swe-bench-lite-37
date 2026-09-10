# django__django-11564 — 输出契约检查表（M1：取值/格式）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/2，
> 断言形如 `settings.STATIC_URL == '/somesubpath/path/'`，v1 得到 `'path/'`（前缀未生效）。
> 填写纪律：不读 `test_patch`。

## 必须确定的拼接契约

| 项 | 问题 | 依据来源 | 结论 |
|---|---|---|---|
| 前缀来源 | `SCRIPT_NAME` 从哪取（`settings.FORCE_SCRIPT_NAME` / `os.environ` / WSGI 请求）？ | ticket、`django/conf` 既有实现 | |
| 前导斜杠 | 拼接后是否保证以 `/` 开头？相对值与绝对值的差异 | 文档 + 既有测试 | |
| 尾随斜杠 | `SCRIPT_NAME=''`、`'/'`、`'/sub/'` 三种输入的输出 | 自建用例 | |
| 求值时机 | settings 加载期求值，还是访问时惰性求值？ | ticket | |
| 作用范围 | 只影响 `STATIC_URL`/`MEDIA_URL`，还是也影响 `STATIC_ROOT` 等？ | ticket + 文档 | |

## 必做验证

1. 参数化用例：`SCRIPT_NAME` × {空, `/`, `/somesubpath`} × URL 值 {`path/`, `/path/`, `http://cdn/x/`}，
   逐格断言输出。
2. 断言取的是**最终 settings 值**，而不是中间变量。
3. 回归：`settings_tests` 模块跑通。
4. 命令与原始输出写入 `verify_output.txt`。

## 已知不确定性

- 对外部 URL（`http://...`）是否加前缀，若无仓库内证据必须标注为不确定。
