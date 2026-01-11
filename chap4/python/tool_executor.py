
from typing import Any, Dict, Callable

from tools_fun import search
from dotenv import load_dotenv

load_dotenv()

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具
    """
    def __init__(self) -> None:
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, description: str, func: Callable) -> None:
        """
        向工具箱中注册一个新工具
        """

        if name in self.tools:
            print(f"警告：工具 {name} 已存在，将被覆盖")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册")

    def get_tool(self, name: str) -> Callable:
        """
        根据名称获取一个工具的执行函数
        """
        return self.tools.get(name, {}).get("func")

    def get_available_tools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([f"- {name}: {info['description']}" for name, info in self.tools.items()])


if __name__ == "__main__":

    toolExecutor = ToolExecutor()
    search_desc = "一个网页搜索引擎，当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具"
    toolExecutor.register_tool("Search", search_desc, search)

    print("\n--- 可用工具 ---")
    print(toolExecutor.get_available_tools())

    print("\n ---- 执行 Action: Search['OPPO 最新的手机是什么']---")
    tool_name = "Search"
    tool_input = 'OPPO 最新的手机是什么'

    tool_function = toolExecutor.get_tool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print('------- 观察 --------')
        print(observation)
    else:
        print(f"错误 {tool_name}， 没有找到")