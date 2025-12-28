import re
import os

from core import OpenAICompatibleClient

from util import get_weather, get_attraction

AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用的工具一步步地解决问题

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点

# 行动格式:
你的回答必须严格遵循以下格式。首先是你的思考过程，然后是你要执行的具体行动，每次回复只输出一对 Thought-Action:
Thought: [这是是你的思考过程和下一步计划]
Action: [这是是你要调用工具，格式为 function_name(arg_name="arg_value")]

# 任务完成:
当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用`finish(answer="....")`来输出最终答案。

请你开始吧！
"""

# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.isfile(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("export "):
                line = line[len("export "):].strip()

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            if key and key not in os.environ:
                os.environ[key] = value



def main():
    load_env_file()
    # --- 1. 配置LLM客户端 ---
    # 请根据您使用的服务，将这里替换成对应的凭证和地址
    API_KEY = os.getenv("API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    MODEL_ID = os.getenv("MODEL_ID")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    missing_keys = [name for name, val in {
        "API_KEY": API_KEY,
        "BASE_URL": BASE_URL,
        "MODEL_ID": MODEL_ID,
        "TAVILY_API_KEY": TAVILY_API_KEY,
    }.items() if not val]
    if missing_keys:
        print(f"缺少环境变量: {', '.join(missing_keys)}")
        print("请在 chap1/.env 中配置，或在系统环境变量中设置。")
        return

    llm = OpenAICompatibleClient(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL
    )

    # --- 2. 初始化 ---
    user_prompt = "你好，请帮我查询一下今天上海的天气，然后根据天气推荐一个合适的旅游景点。"
    prompt_history = [f"用户请求: {user_prompt}"]

    print(f"用户输入: {user_prompt}\n" + "="*40)

    # --- 3. 运行主循环 ---
    for i in range(5): # 设置最大循环次数
        print(f"--- 循环 {i+1} ---\n")
        
        # 3.1. 构建Prompt
        full_prompt = "\n".join(prompt_history)
        
        # 3.2. 调用LLM进行思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        # 模型可能会输出多余的Thought-Action，需要截断
        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print("已截断多余的 Thought-Action 对")
        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)
        
        # 3.3. 解析并执行行动
        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            print("解析错误:模型输出中未找到 Action。")
            break
        action_str = action_match.group(1).strip()

        if action_str.startswith("finish"):
            final_answer = re.search(r'finish\(answer="(.*)"\)', action_str).group(1)
            print(f"任务完成，最终答案: {final_answer}")
            break
        
        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误:未定义的工具 '{tool_name}'"

        # 3.4. 记录观察结果
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "="*40)
        prompt_history.append(observation_str)


if __name__ == "__main__":
    main()
