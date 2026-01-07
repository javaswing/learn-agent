import OpenAI from 'openai';

export class OpenAICompletionClient {
  model: string;
  client: OpenAI;

  constructor(API_KEY: string, BASE_URL: string, MODEL_ID: string) {
    this.model = MODEL_ID;
    this.client = new OpenAI({
      apiKey: API_KEY,
      baseURL: BASE_URL,
    });
  }

  async generate(prompt: string, systemPrompt: string) {
    try {
      console.log(`开始调用大模型`);

      const messages: OpenAI.ChatCompletionMessageParam[] = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt },
      ];

      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: messages,
        stream: false,
      });

      const answer = response.choices[0]?.message.content;
      return answer;
    } catch (error) {
      return `执行大模型出错：${error}`;
    }
  }
}
