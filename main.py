"""
AstrBot Workflow Plugin
可视化工作流插件主入口
"""
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger
from typing import Dict, Any

# 导入核心模块
from .core.workflow_definition import WorkflowDefinition
from .core.workflow_registry import WorkflowRegistry
from .core.workflow_factory import WorkflowHandlerFactory
from .core.session_manager import SessionManager
from .core.exceptions import format_error_for_user
from .utils.config_parser import ConfigParser

# 确保所有 actions 被注册
import actions


@register(
    "astrbot_plugin_workflow",
    "Sky-Winter",
    "可视化工作流插件 - 通过 JSON 配置创建复杂消息处理流程",
    "1.0.0",
    "https://github.com/sky-winter/astrbot_plugin_workflow"
)
class WorkflowPlugin(Star):
    """工作流插件主类"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 插件配置
        self.plugin_config = context.get_config()
        self.debug_mode = self.plugin_config.get('debug_mode', False)
        
        # 核心组件
        self.registry = WorkflowRegistry()
        self.factory = WorkflowHandlerFactory(debug_mode=self.debug_mode)
        self.session_manager = SessionManager()
        
        # 初始化
        try:
            self._load_workflows()
            logger.info(f"✅ 工作流插件加载完成，共加载 {len(self.registry.workflows)} 个工作流")
        except Exception as e:
            logger.error(f"❌ 工作流插件初始化失败: {str(e)}")
            # 不中断加载，使用空配置
    
    def _load_workflows(self):
        """加载工作流配置"""
        # 从配置读取 workflow_templates
        template_list = self.plugin_config.get('workflow_templates', [])
        
        if not template_list:
            logger.warning("⚠️  未配置任何工作流模板")
            return
        
        # 解析配置
        workflows = ConfigParser.parse_templates(template_list, self.debug_mode)
        
        # 注册工作流
        for workflow in workflows:
            try:
                # 注册到注册表
                self.registry.register(workflow, allow_override=True)
                
                # 创建 handler
                handler = self.factory.create_handler(workflow, self.context)
                
                # 应用装饰器
                decorated_handler = self.factory.apply_decorators(handler, workflow)
                
                # 动态绑定到插件实例
                handler_name = f"_wf_{workflow.id}"
                setattr(self, handler_name, decorated_handler)
                
                if self.debug_mode:
                    logger.info(f"  ↳ 已注册 handler: {handler_name}")
            
            except Exception as e:
                logger.error(f"❌ 注册 workflow '{workflow.id}' 失败: {str(e)}")
                continue
    
    async def terminate(self):
        """插件卸载时的清理工作"""
        try:
            # 清理会话
            if hasattr(self, 'session_manager'):
                await self.session_manager.stop()
                self.session_manager.clear_all_sessions()
            
            # 清理注册表
            if hasattr(self, 'registry'):
                self.registry.clear()
            
            logger.info("🔄 工作流插件已卸载")
        except Exception as e:
            logger.error(f"插件卸载时发生错误: {str(e)}")
    
    # ==================== 管理指令 ====================
    
    @filter.command("workflow", alias={'wf'})
    async def workflow_command_group(self):
        """工作流管理指令组"""
        pass
    
    @workflow_command_group.command("reload")
    async def reload_workflows(self, event: AstrMessageEvent):
        """重载所有工作流配置"""
        try:
            # 清理现有工作流
            self.registry.clear()
            
            # 重新加载
            self._load_workflows()
            
            summary = self.registry.get_summary()
            yield event.plain_result(
                f"✅ 工作流配置已重载\n"
                f"📊 总数: {summary['total_workflows']} | "
                f"启用: {summary['enabled_workflows']} | "
                f"禁用: {summary['disabled_workflows']}"
            )
        
        except Exception as e:
            yield event.plain_result(f"❌ 重载失败: {format_error_for_user(e)}")
    
    @workflow_command_group.command("status")
    async def show_status(self, event: AstrMessageEvent):
        """显示工作流统计信息"""
        try:
            summary = self.registry.get_summary()
            stats = self.registry.get_stats()
            
            # 构建状态消息
            lines = [
                "📊 工作流插件状态",
                f"━━━━━━━━━━━━━━━━",
                f"总工作流数: {summary['total_workflows']}",
                f"已启用: {summary['enabled_workflows']}",
                f"总执行次数: {summary['total_executions']}",
                f"成功次数: {summary['total_successes']}",
                f"整体成功率: {summary['overall_success_rate'] * 100:.1f}%",
                ""
            ]
            
            # 显示各个工作流的统计
            if stats:
                lines.append("📈 各工作流统计:")
                for wf_id, stat_dict in stats.items():
                    wf = self.registry.get(wf_id)
                    if wf:
                        lines.append(
                            f"  • {wf.name}: "
                            f"{stat_dict['total_executions']}次 | "
                            f"成功率 {stat_dict['success_rate'] * 100:.1f}%"
                        )
            
            yield event.plain_result("\n".join(lines))
        
        except Exception as e:
            yield event.plain_result(f"❌ 获取状态失败: {format_error_for_user(e)}")
    
    @workflow_command_group.command("debug")
    async def toggle_debug(self, event: AstrMessageEvent):
        """切换调试模式"""
        self.debug_mode = not self.debug_mode
        self.factory.debug_mode = self.debug_mode
        
        status = "已开启" if self.debug_mode else "已关闭"
        yield event.plain_result(f"🔧 调试模式{status}")
    
    @workflow_command_group.command("list")
    async def list_workflows(self, event: AstrMessageEvent):
        """列出所有工作流"""
        try:
            workflows = self.registry.get_all()
            
            if not workflows:
                yield event.plain_result("📭 当前没有已注册的工作流")
                return
            
            lines = ["📋 已注册的工作流:", "━━━━━━━━━━━━━━━━"]
            
            for wf in workflows:
                status_icon = "✅" if wf.enabled else "❌"
                trigger_info = ""
                if wf.trigger:
                    trigger_info = f" | 触发: {wf.trigger.type.value}({wf.trigger.value})"
                
                lines.append(
                    f"{status_icon} {wf.name}\n"
                    f"   ID: {wf.id}{trigger_info}\n"
                    f"   动作数: {len(wf.actions)}"
                )
            
            yield event.plain_result("\n".join(lines))
        
        except Exception as e:
            yield event.plain_result(f"❌ 获取列表失败: {format_error_for_user(e)}")
    
    @workflow_command_group.command("sessions")
    async def show_sessions(self, event: AstrMessageEvent):
        """显示活跃会话"""
        try:
            sessions = self.session_manager.get_active_sessions()
            stats = self.session_manager.get_stats()
            
            lines = [
                f"🔄 活跃会话统计",
                f"━━━━━━━━━━━━━━━━",
                f"总会话数: {stats['total_sessions']}",
                f"活跃会话: {stats['active_sessions']}",
                f"过期会话: {stats['expired_sessions']}",
                ""
            ]
            
            if sessions:
                lines.append("📌 当前活跃会话:")
                for sess in sessions[:10]:  # 最多显示 10 个
                    lines.append(
                        f"  • {sess['workflow_id']} | "
                        f"用户: {sess['user_id'][:8]}... | "
                        f"年龄: {int(sess['age_seconds'])}秒"
                    )
                
                if len(sessions) > 10:
                    lines.append(f"  ... 还有 {len(sessions) - 10} 个")
            else:
                lines.append("当前没有活跃会话")
            
            yield event.plain_result("\n".join(lines))
        
        except Exception as e:
            yield event.plain_result(f"❌ 获取会话信息失败: {format_error_for_user(e)}")
    
    @workflow_command_group.command("help")
    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = """
📖 工作流插件帮助

可用指令：
  /workflow list - 列出所有工作流
  /workflow status - 显示统计信息
  /workflow reload - 重载配置
  /workflow debug - 切换调试模式
  /workflow sessions - 查看活跃会话
  /workflow help - 显示此帮助

配置方式：
1. 在 AstrBot WebUI 的插件配置中添加模板
2. 使用 GitHub Pages 可视化工具生成 JSON 配置
3. 保存配置后自动加载或使用 /workflow reload 重载

更多文档：https://github.com/sky-winter/astrbot_plugin_workflow
        """
        yield event.plain_result(help_text.strip())
