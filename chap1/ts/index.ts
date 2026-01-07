import * as dotenv from 'dotenv';
import { OpenAICompletionClient } from './completion_client';
import { AGENT_SYSTEM_PROMPT } from './const';
import { get_attraction, get_weather } from './utils';

dotenv.config();

export const requireEnv = (name: string) => {
  const value = process.env[name];
  if (value === undefined || value.trim() === '') {
    throw new Error(`${name} is not set`);
  }
  return value;
};

const available_tools = {
  get_weather: (args: any) => get_weather(args.city),
  get_attraction: (args: any) => get_attraction(args.city, args.weather),
};

async function main() {
  const API_KEY = requireEnv('API_KEY');
  const BASE_URL = requireEnv('BASE_URL');
  const MODEL_ID = requireEnv('MODEL_ID');

  console.log(`========= 初始化 OpenAI =========`);
  const llm = await new OpenAICompletionClient(API_KEY, BASE_URL, MODEL_ID);

  const prompt = `你好，请帮我查询一下今天上海的天气，然后根据天气推荐一个合适的旅游景点。`;
  const promptHistory = [`用户请求: ${prompt}`];

  const maxRange = 5;

  for (let index = 0; index < maxRange; index++) {
    console.log(`--- 循环  ${index + 1} 次 ---\n`);
    const fullPrompt = promptHistory.join('\n');
    let output = await llm.generate(fullPrompt, AGENT_SYSTEM_PROMPT);

    let outputMatch = output?.match(
      new RegExp(
        '(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
      ),
    );
    if (outputMatch) {
      let truncated = outputMatch[0].trim();
      if (truncated) {
        output = truncated;
        console.log('已截断多余的 Thought-Action 对');
      }
    }
    if (!output) {
      break;
    }

    console.log(`模型输出:\n${output}\n`);

    promptHistory.push(output);

    // 解析行动
    const action_match = output?.match(/Action: (.*)/);

    if (!action_match) {
      console.log('解析错误:模型输出中未找到 Action。');
      break;
    }
    const action_str = action_match![1]!;
    console.log(`action_str: ${action_str}` + '\n');
    if (action_str.startsWith('finish')) {
      const final_answer = action_str.match(/finish\(answer="(.*)"\)/)?.[1];
      if (final_answer) {
        console.log(`任务完成，最终答案: ${final_answer}`);
        break;
      }
    }

    const tool_name = action_str.match(/(\w+)\(/)?.[1];
    const args = action_str.match(/\((.*)\)/)?.[1];

    const kwargs: Record<string, string> = {};
    if (args) {
      const argMatches = args.matchAll(/(\w+)="([^"]*)"/g);
      for (const m of argMatches) {
        const k = m[1]!;
        kwargs[k] = m[2]!;
      }
    }

    let observation: string | undefined;
    if (tool_name && tool_name in available_tools) {
      observation =
        await available_tools[tool_name as keyof typeof available_tools](
          kwargs,
        );
    } else {
      observation = `错误:未定义的工具 '${tool_name}'`;
    }

    const observation_str = `Observation: ${observation}`;
    promptHistory.push(observation_str);
  }
}

// get_weather('上海');
main();
