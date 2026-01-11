from typing import List, Dict, Any, Optional

from core import HelloAgentsLLM

# 记忆模块
class Memory:
    """
    一个简单的记忆模块，用户记录智能体的行动与反思轨迹
    """

    def __init__(self):
        """
        初始化一个空列表来存储所有记录
        """
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type:str, content: str) -> None:
        """
        添加一条新的记忆
        """
        record = {"type": record_type, "content": content}
        self.records.append(record)

        print(f"记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        """
        将所有记忆转换为一个字符串文本，用于构建提示词
        """

        trajectory_parts = []
        for record in self.records:
            if record["type"] == "execution":
                trajectory_parts.append(f"----上一轮尝试（代码）---\n {record['content']}")
            elif record["type"] == "reflection":
                trajectory_parts.append(f"----上一轮反思---\n {record['content']}")
        return "\n\n".join(trajectory_parts)
    
    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次的执行代码
        """
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None
    

INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python 程序员。请根据以下要求，编写一个 Python 函数。
你的代码必须包含完整的函数签名、文档字符串、并遵循 PEP8编码规范。

要求：{task}

请直接输出代码，不要包含任何额外的解释
"""


REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资料算法工程师，对代码的性能有极致的要求。
你的任务是审查以下 Python 代码，并专注找出其中<strong>算法效率</strong>上的主要瓶颈。

# 原始任务
{task}

# 待审查代码
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
如果存在，请清晰的指出当前算法的不足，并提出具体的、可行的改进算法的建议（例如：使用筛法替代试除法）
如果代码在算法层面已经达到最优，才能回答“无需改进“

请直接输出你的反馈，不要包含额外的解释
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python 程序员。你正在根据一位代码评审专家的反馈，来优化你的代码。

# 原始任务
{task}

# 你上一轮尝试的代码：
{last_code_attempt}

评审员的反馈
{feedback}

请你根据评审员的反馈，生成一个优化后的代码。
你的代码必须包含完整的函数签名、文档字符串、并遵循 PEP8编码规范。
请直接优化后的代码，不要包含额外的解释
"""


class ReflectionAgent:
    def __init__(self, llm: HelloAgentsLLM, max_iterations:int = 3) -> None:
        self.llm_client = llm
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task:str):
        print(f"---开始处理任务 ---")

        print(f"---尝试初次执行---")

        init_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        init_code = self._get_llm_response(init_prompt)
        self.memory.add_record(record_type="execution", content=init_code)

        for i in range(self.max_iterations):
            print(f"\n--- 正在进行{i+1}/{self.max_iterations} 轮优化 ---")

            print(f"\n--- 正在进行反思 ---")

            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task,code= last_code)

            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record(record_type="reflection", content=feedback)

            if "无需改进" in feedback:
                print("\n代码已经无需改进")
                break

            print(f"\n-> 正在进行优化...")

            refine_prompt = REFINE_PROMPT_TEMPLATE.format(task= task, last_code_attempt = last_code, feedback= feedback)
            response_txt = self._get_llm_response(refine_prompt)

            self.memory.add_record(record_type="execution", content=response_txt)

        final_code = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终生成的代码:\n \n{final_code}\n")
        return final_code


    def _get_llm_response(self, prompt:str) ->str:
        messages = [{"role": "user", "content": prompt}]
        response_txt = self.llm_client.think(messages=messages)
        return response_txt
    


if __name__ == "__main__":
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)"
    llm = HelloAgentsLLM()
    agent = ReflectionAgent(llm=llm)

    agent.run(task)