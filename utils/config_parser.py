"""
配置解析器
解析插件配置中的 workflow templates
"""
import json
from typing import List, Dict, Any
from astrbot.api import logger

from ..core.workflow_definition import WorkflowDefinition
from ..core.validators import validate_full_workflow
from ..core.action_registry import get_registered_action_ids
from ..core.exceptions import ConfigFormatError, ConfigValidationError


class ConfigParser:
    """配置解析器"""
    
    @staticmethod
    def parse_templates(
        template_list: List[Dict[str, Any]],
        debug_mode: bool = False
    ) -> List[WorkflowDefinition]:
        """
        解析 template_list 配置
        
        Args:
            template_list: 模板列表
            debug_mode: 调试模式
            
        Returns:
            成功解析的 WorkflowDefinition 列表
        """
        workflows = []
        registered_action_ids = get_registered_action_ids()
        
        for idx, template in enumerate(template_list):
            try:
                # 1. 检查 enabled 字段
                if not template.get('enabled', False):
                    if debug_mode:
                        logger.info(f"跳过未启用的模板 #{idx}: {template.get('name', 'unnamed')}")
                    continue
                
                # 2. 解析 config_code (JSON 字符串)
                config_code = template.get('config_code', '')
                if not config_code:
                    logger.error(f"模板 #{idx} 的 config_code 为空")
                    continue
                
                try:
                    config_data = json.loads(config_code)
                except json.JSONDecodeError as e:
                    logger.error(f"模板 #{idx} 的 config_code JSON 解析失败: {str(e)}")
                    continue
                
                # 3. 验证并转换
                workflow_def, errors = validate_full_workflow(
                    config_data,
                    registered_action_ids
                )
                
                if errors:
                    logger.error(
                        f"模板 #{idx} 验证失败:\n" +
                        "\n".join(f"  - {err}" for err in errors)
                    )
                    continue
                
                workflows.append(workflow_def)
                logger.info(f"✅ 成功加载 workflow: {workflow_def.name} (id: {workflow_def.id})")
            
            except Exception as e:
                logger.error(f"解析模板 #{idx} 时发生错误: {str(e)}")
                continue
        
        return workflows
    
    @staticmethod
    def load_from_file(file_path: str) -> List[WorkflowDefinition]:
        """
        从文件加载配置
        
        Args:
            file_path: JSON 配置文件路径
            
        Returns:
            WorkflowDefinition 列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # 直接是 workflow 定义列表
                workflows = []
                registered_action_ids = get_registered_action_ids()
                
                for config in data:
                    workflow_def, errors = validate_full_workflow(
                        config,
                        registered_action_ids
                    )
                    if not errors:
                        workflows.append(workflow_def)
                    else:
                        logger.error(f"验证失败: {errors}")
                
                return workflows
            else:
                logger.error("配置文件格式错误，应为列表")
                return []
        
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 解析失败: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return []
