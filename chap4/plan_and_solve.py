import ast
from core import HelloAgentsLLM


PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的 AI 专家。你的任务是根据用户提出的问题，分解成由一个或者多个简单步骤组成的计划。
请确保计划中的每一个步骤都是独立的、可执行的子任务，并严格按照逻辑顺序排列。
你的输出必须是一个 Python 列表，每个元素都是描述子任务的字符串。

问题：{question}

请严格按照以下格式输出计划，```python 与```作为前后缀是必须的：

```python
["步骤 1", "步骤 2"]
```
"""

class Planner:



    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client


    def plan(self, question: str) -> list[str]:
        """
        根据用户的问题生成计划列表
        """

        prompt = PLANNER_PROMPT_TEMPLATE.format(question = question)

        messages = [{"role": "user", "content": prompt}]

        print("-----正在生成计划-------")

        response_txt = self.llm_client.think(messages=messages) or ""

        print(f"计划已经生成：\n {response_txt}")

        try:
            plan_str = response_txt.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except(ValueError, SyntaxError, IndexError) as e:
            print(f"解析计划时出错 {e}")
            print(f"原始响应: {response_txt}")
            return []
        except Exception as e:
            print(f"执行拆解计划发生未知错误：{e}")
            return []

EXECUTOR_PROMPT_TEMPLATE = """
你是一个顶级的 AI 专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止完成的步骤和结果。
请你专注于解决“当前步骤“，并仅输出该步骤的答案，不要输出任何外的解释或对话。

# 原始问题
{question}

# 完整计划
{plan}

# 历史步骤与结果
{history}

# 当前步骤
{current_step}

请仅输出针对“当前步骤“的回答：
"""

class Executor:
    def __init__(self, llm: HelloAgentsLLM) -> None:
        self.llm_client = llm

    def execute(self, question:str, plan: list[str]) -> str:
        """
        根据计划，逐步执行并解决问题
        """    

        history = ""

        print("---------正在执行计划-----------")

        for i, step in enumerate(plan):
            print( f"---------正在执行步骤{i+1}/{len(plan)}: {step}-----------")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question= question,
                plan=plan,
                current_step=step,
                history=history
            )

            messages = [{"role": "user", "content": prompt}]

            response_txt = self.llm_client.think(messages=messages) or ""

            history += f"步骤{i+1}: {step}\n 结果：{response_txt}"
            print( f"步骤 {i+1} 已完成，结果: {response_txt}")
        
        final_answer = response_txt
        return final_answer
    


class PlanAndSolveAgent:
    def __init__(self, llm: HelloAgentsLLM) -> None:
        self.llm_client = llm
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question:str):
        print( f"开始处理问题 {question}")

        plan = self.planner.plan(question)

        if not plan:
            print("未能生成有效的计划，无法继续执行。")
            return None
        
        final_answer = self.executor.execute(question, plan)

        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")


if __name__ == "__main__":
    try:
        llmClient = HelloAgentsLLM()
        
        agent = PlanAndSolveAgent(llmClient)

        user_question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"

        agent.run(user_question)

    except ValueError as e:
        print(e)

