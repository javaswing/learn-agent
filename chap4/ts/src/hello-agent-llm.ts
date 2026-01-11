import OpenAI from 'openai';
import { requireEnv } from './utils';
import { type ChatCompletionMessageParam } from 'openai/resources';


/**
 *  Hello Agents 定制的 LLM 客户端
 *  它用于调用任何兼容 OpenAI 接口的服务，并默认使用流式响应
 */
export class HelloAgentsLLM {
  model: string;
  apiKey: string;
  baseUrl: string;
  timeout: number;
  client: OpenAI;

  constructor(
    model?: string,
    apiKey?: string,
    baseUrl?: string,
    timeout: number = 60,
  ) {
    this.model = model || requireEnv('LLM_MODEL_ID');
    this.apiKey = apiKey || requireEnv('LLM_API_KEY');
    this.baseUrl = baseUrl || requireEnv('LLM_BASE_URL');
    this.timeout = requireEnv('LLM_TIMEOUT')
      ? Number(requireEnv('LLM_TIMEOUT'))
      : timeout;

    if (!this.model || !this.baseUrl || !this.apiKey) {
      throw new Error(
        '模型 ID、API 密钥和服务地址必须被提供或在.env 文件中定义',
      );
    }

    // console.log(this.baseUrl)

    this.client = new OpenAI({
      baseURL: this.baseUrl,    
      apiKey: this.apiKey,
      // timeout: this.timeout Error: Request timed out.
    });
  }

  async think(messages: Array<ChatCompletionMessageParam>, temperature = 0) {
    console.log('开始调用大模型');
    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: messages,
        temperature: temperature,
        stream: true,
      });

      console.log('调用大模型成功 \n');

      const collectedContent = [];
      for await (const chunk of response) {
        // 处理每个 chunk        
        const c = chunk.choices[0]?.delta.content || "";
        collectedContent.push(c);
      }
      return collectedContent.join("")
    } catch (e) {
        console.error(`调用 LLM API时发生错误: ${e}`)
        return
    }
  }
}
