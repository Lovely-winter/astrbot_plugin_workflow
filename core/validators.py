"""
工作流验证器
提供 Schema 验证、业务逻辑验证、运行时参数验证
"""
from typing import Dict, List, Any, Set, Optional
import jsonschema
from jsonschema import ValidationError as JsonSchemaValidationError
from .workflow_definition import WorkflowDefinition, TriggerType, ActionConfig
from .exceptions import ConfigValidationError, ActionParameterError


# JSON Schema 定义
WORKFLOW_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "trigger", "actions"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "enabled": {"type": "boolean"},
        "priority": {"type": "integer"},
        "variables": {"type": "object"},
        "rate_limit": {
            "type": "object",
            "properties": {
                "max_calls": {"type": "integer", "minimum": 1},
                "time_window": {"type": "number", "minimum": 1}
            }
        },
        "trigger": {
            "type": "object",
            "required": ["type", "value"],
            "properties": {
                "type": {"type": "string", "enum": ["command", "keyword", "event", "regex"]},
                "value": {"type": "string", "minLength": 1},
                "alias": {"type": "array", "items": {"type": "string"}},
                "filters": {"type": "object"}
            }
        },
        "actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["action_id"],
                "properties": {
                    "action_id": {"type": "string", "minLength": 1},
                    "params": {"type": "object"},
                    "flow_control": {
                        "type": "object",
                        "properties": {
                            "next": {"type": ["integer", "null"]},
                            "on_success": {"type": ["integer", "null"]},
                            "on_failure": {"type": ["integer", "null"]}
                        }
                    },
                    "error_handling": {
                        "type": "string",
                        "enum": ["stop", "continue", "retry", "jump"]
                    },
                    "retry_count": {"type": "integer", "minimum": 0, "maximum": 10},
                    "timeout": {"type": ["number", "null"], "minimum": 0},
                    "condition": {"type": ["string", "null"]}
                }
            }
        },
        "session": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "timeout": {"type": "number", "minimum": 1},
                "strategy": {"type": "string", "enum": ["per_user", "per_group", "global"]},
                "record_history": {"type": "boolean"},
                "max_history": {"type": "integer", "minimum": 1, "maximum": 1000}
            }
        }
    }
}


def validate_schema(data: Dict[str, Any]) -> List[str]:
    """
    验证 JSON Schema
    
    Args:
        data: 待验证的配置数据
        
    Returns:
        错误列表，空列表表示验证通过
    """
    errors = []
    try:
        jsonschema.validate(instance=data, schema=WORKFLOW_SCHEMA)
    except JsonSchemaValidationError as e:
        errors.append(f"Schema 验证失败: {e.message} (路径: {'.'.join(map(str, e.path))})")
    except Exception as e:
        errors.append(f"Schema 验证异常: {str(e)}")
    
    return errors


def validate_business_logic(
    workflow_def: WorkflowDefinition,
    registered_action_ids: Set[str]
) -> List[str]:
    """
    验证业务逻辑
    
    Args:
        workflow_def: 工作流定义
        registered_action_ids: 已注册的 action_id 集合
        
    Returns:
        错误列表，空列表表示验证通过
    """
    errors = []
    
    # 1. 验证 action_id 存在性
    for idx, action in enumerate(workflow_def.actions):
        if action.action_id not in registered_action_ids:
            errors.append(
                f"Action #{idx} 的 action_id '{action.action_id}' 未注册"
            )
    
    # 2. 验证 flow_control 索引合法性
    action_count = len(workflow_def.actions)
    for idx, action in enumerate(workflow_def.actions):
        fc = action.flow_control
        
        # 检查 next
        if fc.next is not None:
            if fc.next < 0 or fc.next >= action_count:
                errors.append(
                    f"Action #{idx} 的 next 索引 {fc.next} 越界 (总数: {action_count})"
                )
        
        # 检查 on_success
        if fc.on_success is not None:
            if fc.on_success < 0 or fc.on_success >= action_count:
                errors.append(
                    f"Action #{idx} 的 on_success 索引 {fc.on_success} 越界 (总数: {action_count})"
                )
        
        # 检查 on_failure
        if fc.on_failure is not None:
            if fc.on_failure < 0 or fc.on_failure >= action_count:
                errors.append(
                    f"Action #{idx} 的 on_failure 索引 {fc.on_failure} 越界 (总数: {action_count})"
                )
    
    # 3. 检查循环依赖
    cycle_errors = detect_cycles(workflow_def.actions)
    errors.extend(cycle_errors)
    
    # 4. 验证触发器
    if workflow_def.trigger:
        if not workflow_def.trigger.value.strip():
            errors.append("触发器 value 不能为空")
    
    return errors


def detect_cycles(actions: List[ActionConfig]) -> List[str]:
    """
    检测动作流程中的循环依赖
    使用 DFS 算法检测有向图中的环
    
    Args:
        actions: 动作列表
        
    Returns:
        错误列表
    """
    errors = []
    n = len(actions)
    
    # 构建邻接表
    graph: Dict[int, List[int]] = {i: [] for i in range(n)}
    
    for idx, action in enumerate(actions):
        fc = action.flow_control
        
        # 添加边
        targets = []
        if fc.next is not None and 0 <= fc.next < n:
            targets.append(fc.next)
        if fc.on_success is not None and 0 <= fc.on_success < n:
            targets.append(fc.on_success)
        if fc.on_failure is not None and 0 <= fc.on_failure < n:
            targets.append(fc.on_failure)
        
        graph[idx] = targets
    
    # DFS 检测环
    visited = set()
    rec_stack = set()
    
    def dfs(node: int, path: List[int]) -> Optional[List[int]]:
        """DFS 遍历，返回环路径"""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                cycle = dfs(neighbor, path[:])
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # 发现环
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        rec_stack.remove(node)
        return None
    
    for start_node in range(n):
        if start_node not in visited:
            cycle_path = dfs(start_node, [])
            if cycle_path:
                cycle_str = " -> ".join(f"#{idx}" for idx in cycle_path)
                errors.append(f"检测到循环依赖: {cycle_str}")
                break  # 只报告第一个环
    
    return errors


def validate_runtime_params(
    action_config: ActionConfig,
    context_variables: Dict[str, Any],
    required_params: List[str]
) -> Dict[str, Any]:
    """
    运行时参数验证和转换
    
    Args:
        action_config: 动作配置
        context_variables: 上下文变量
        required_params: 必填参数列表
        
    Returns:
        转换后的参数字典
        
    Raises:
        ActionParameterError: 参数验证失败
    """
    params = action_config.params.copy()
    
    # 1. 检查必填参数
    for param_name in required_params:
        if param_name not in params:
            raise ActionParameterError(
                action_config.action_id,
                param_name,
                "缺少必填参数"
            )
    
    # 2. 解析变量插值（在 execution_context 中处理）
    # 这里只做基本验证
    
    # 3. 类型转换（简单实现，可扩展）
    # 可以根据 action 的元数据进行更严格的类型检查
    
    return params


def validate_condition(condition: str, variables: Dict[str, Any]) -> bool:
    """
    验证执行条件表达式
    
    Args:
        condition: 条件表达式字符串，如 "{score} > 60"
        variables: 上下文变量
        
    Returns:
        条件是否满足
    """
    if not condition:
        return True
    
    try:
        # 简单的变量替换
        expr = condition
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in expr:
                # 安全替换（避免注入）
                if isinstance(var_value, (int, float)):
                    expr = expr.replace(placeholder, str(var_value))
                elif isinstance(var_value, bool):
                    expr = expr.replace(placeholder, str(var_value))
                elif isinstance(var_value, str):
                    expr = expr.replace(placeholder, f"'{var_value}'")
        
        # 使用 eval（受限环境）
        # 注意：生产环境应使用更安全的表达式解析器
        result = eval(expr, {"__builtins__": {}}, {})
        return bool(result)
    except Exception as e:
        # 条件表达式错误，默认不执行
        return False


def validate_full_workflow(
    data: Dict[str, Any],
    registered_action_ids: Set[str]
) -> tuple[Optional[WorkflowDefinition], List[str]]:
    """
    完整验证工作流配置
    
    Args:
        data: 配置数据字典
        registered_action_ids: 已注册的 action_id 集合
        
    Returns:
        (WorkflowDefinition 对象, 错误列表)
    """
    errors = []
    
    # 1. Schema 验证
    schema_errors = validate_schema(data)
    errors.extend(schema_errors)
    
    if schema_errors:
        # Schema 验证失败，无法继续
        return None, errors
    
    # 2. 转换为对象
    try:
        workflow_def = WorkflowDefinition.from_dict(data)
    except Exception as e:
        errors.append(f"配置解析失败: {str(e)}")
        return None, errors
    
    # 3. 业务逻辑验证
    business_errors = validate_business_logic(workflow_def, registered_action_ids)
    errors.extend(business_errors)
    
    if errors:
        return None, errors
    
    return workflow_def, []
