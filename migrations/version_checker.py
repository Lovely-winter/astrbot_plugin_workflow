实现版本检测工具类。

定义当前插件版本常量。

check_config_version 方法：从配置的 _meta.version 字段检测配置版本，
与当前版本比较，判断是否需要迁移。

返回版本号或 None（无版本信息）。