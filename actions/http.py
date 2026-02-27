"""
HTTP 请求 Action
实现 HTTP 请求、网页爬取等功能
"""
from typing import Dict, Any, List
import aiohttp
import asyncio
from .base import BaseAction
from ..core.action_registry import register_action
from ..core.exceptions import ActionExecutionError


@register_action("http_request")
class HttpRequestAction(BaseAction):
    """通用 HTTP 请求"""
    
    description = "发送 HTTP 请求"
    
    def get_required_params(self) -> List[str]:
        return ['url']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - url: 请求 URL
        - method: 请求方法（GET/POST/PUT/DELETE，默认 GET）
        - headers: 请求头字典（可选）
        - params: URL 参数字典（可选）
        - data: 请求体数据（可选）
        - json: JSON 请求体（可选）
        - timeout: 超时时间（默认 10秒）
        - retry: 重试次数（默认 3）
        - result_variable: 结果存储的变量名（默认 'http_response'）
        """
        params = self.resolve_params()
        url = params.get('url')
        method = params.get('method', 'GET').upper()
        headers = params.get('headers', {})
        url_params = params.get('params', {})
        data = params.get('data')
        json_data = params.get('json')
        timeout = params.get('timeout', 10.0)
        retry_count = params.get('retry', 3)
        result_var = params.get('result_variable', 'http_response')
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=url_params,
                        data=data,
                        json=json_data,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        status = response.status
                        text = await response.text()
                        
                        # 尝试解析为 JSON
                        try:
                            json_result = await response.json()
                        except:
                            json_result = None
                        
                        result = {
                            'status': status,
                            'text': text,
                            'json': json_result,
                            'headers': dict(response.headers),
                            'url': str(response.url)
                        }
                        
                        # 存储结果到上下文
                        self.set_result(result_var, result)
                        
                        # 检查 HTTP 状态码
                        if 400 <= status < 600:
                            return {
                                'success': False,
                                'message': f'HTTP 错误: {status}',
                                'status': status,
                                'response': text[:200]  # 截断长文本
                            }
                        
                        return {
                            'success': True,
                            'message': 'HTTP 请求成功',
                            'status': status,
                            'data': json_result if json_result else text[:200]
                        }
            
            except asyncio.TimeoutError:
                last_error = f"请求超时 ({timeout}秒)"
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            except aiohttp.ClientError as e:
                last_error = f"网络错误: {str(e)}"
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                break  # 其他错误不重试
        
        # 重试耗尽
        raise ActionExecutionError(
            self.action_id,
            f"HTTP 请求失败: {last_error}"
        )


@register_action("web_scrape")
class WebScrapeAction(BaseAction):
    """网页爬取（简单 HTML 解析）"""
    
    description = "爬取网页内容"
    
    def get_required_params(self) -> List[str]:
        return ['url']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - url: 目标网页 URL
        - selector: CSS 选择器（可选，需要 BeautifulSoup）
        - timeout: 超时时间
        - result_variable: 结果存储的变量名
        """
        params = self.resolve_params()
        url = params.get('url')
        timeout = params.get('timeout', 10.0)
        result_var = params.get('result_variable', 'scrape_result')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        raise ActionExecutionError(
                            self.action_id,
                            f"HTTP 错误: {response.status}"
                        )
                    
                    html = await response.text()
                    
                    # 简单地返回 HTML，如需解析可使用 BeautifulSoup
                    # 这里只是基本实现
                    result = {
                        'html': html,
                        'length': len(html),
                        'url': url
                    }
                    
                    self.set_result(result_var, result)
                    
                    return {
                        'success': True,
                        'message': '爬取成功',
                        'length': len(html)
                    }
        
        except asyncio.TimeoutError:
            raise ActionExecutionError(
                self.action_id,
                f"请求超时 ({timeout}秒)"
            )
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"爬取失败: {str(e)}",
                original_error=e
            )