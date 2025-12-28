import os
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

class HelloAgentsLLM:
    """
    Hello Agents 定制的 LLM 客户端
    它用于调用任何妆容 OpenAI 接口的服务，并默认使用流式响应
    """
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, timeout: int = None):
        """
        初始化客户端，优先使用传入的参数，如果未提供，则从环境变量加载
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        api_key = api_key or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        if not all([self.model, api_key, base_url]):
            raise ValueError("模型 ID、API 密钥和服务地址必须被提供或在.env 文件中定义")

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def think(self, messages:  List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回响应
        """
        print(f"正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

            print("大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            # 流式输出结束之后换行
            print()
            return "".join(collected_content)
        except Exception as e:
            print(f"调用 LLM API时发生错误: {e}")
            return None
        

if __name__ == "__main__":
    try:
        llmClient = HelloAgentsLLM()
        
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code"},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        print("------------调用LLM----------")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n---- 完整的模型响应 -----")
            print(responseText)

    except ValueError as e:
        print(e)