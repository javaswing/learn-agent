### ReAct 提示词
import re
from core import HelloAgentsLLM
from tool_executor import ToolExecutor
from tools_fun import search


REACT_PROMPT_TEMPLATE = """
请注意， 你是一个有能力调用外部工具的智能助手

可用工具如下：
{tools}

请严格按以下格式回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动
Action: 你采取的行动必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具
- `Finish[最终答案]`: 当你认为已经获取最终答案时


现在请开始解决以下问题：
Question: {question}
History: {history}
"""


class ReActAgent:
    
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    
    def run(self, question:str):
        """
        运行 ReAct Agent智能体来回答一个问题
        """
        self.history = []
        current_step = 0

        while current_step <= self.max_steps:
            current_step += 1
            print(f"--- 第{current_step}步 ---")

            # 格式化提示词
            tools_desc = self.tool_executor.get_available_tools()
            history_str = "\n".join(self.history)

            prompt = REACT_PROMPT_TEMPLATE.format(tools = tools_desc, question = question, history = history_str)

            # 调用 llm_client 进行思考
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("错误：LLM 未能返回有效的响应")
                break

            # 解析 LLM 输出
            thought, action = self._parse_output(response_text)

            if thought:
                print(f"思考：{thought}")

            if not action:
                print(f"警告：未能解析出有效的 Action，流程终止")
                break

            if action.startswith("Finish"):
                # 如果是 Finish 指令，提取最终答案并结束
                final_answer = self._parse_action_input(action)
                print(f"最终答案： {final_answer}")
                return final_answer
            
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                continue

            print(f"行动 {tool_name} [{tool_input}]")

            tool_function = self.tool_executor.get_tool(tool_name)
            observation = f"错误： 未找到名为 '{tool_name}' 的工具"  if not tool_function else tool_function(tool_input)            

            print(f"观察 {observation}")

            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("达到最大步数，流程终止")
        return None


    def _parse_output(self, text: str):
        """
        解析 LLM 输出，提取 Thought 和 Action
        """
        thought_match = re.search(r"Thought:(.*)", text)
        action_match = re.search(r"Action:(.*)", text)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action
    
    def _parse_action(self, action_text:str):
        """
        解析 Action 字符串，提取工具名称和输入
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _parse_action_input(self, text: str):
        """
        解析 Action 输入，提取参数
        """
        input_match = re.match(r'\w+\[(.*)\]', text)
        return input_match.group(1) if input_match else None
    


if __name__ == "__main__":
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "搜索工具，可以根据关键词搜索信息"
    tool_executor.register_tool("Search", search_desc, search)

    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "一加最新的手机是哪一款？它的卖点是什么?"

    agent.run(question=question)