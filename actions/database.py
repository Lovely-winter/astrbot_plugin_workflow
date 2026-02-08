实现数据库操作 action。

SaveToDbAction：保存数据到数据库或 KV 存储，参数为 table 和 data。

QueryDbAction：查询数据库，参数为 table 和 condition，结果存入上下文变量。

根据需求可集成 SQLAlchemy 或使用 AstrBot 提供的存储接口。