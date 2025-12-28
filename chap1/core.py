from openai import OpenAI

class OpenAICompatibleClient:

    def __init__(self, model:str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        print(f"正在调用大模型")

        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )

            answer = response.choices[0].message.content
            print(f"大模型回复：{answer}")
            return answer
        except Exception as e:
            return f"错误：调用大模型时出现问题 - {e}"