import * as dotenv from 'dotenv';
import { OpenAICompletionClient } from './completion_client';
import { AGENT_SYSTEM_PROMPT } from './const';
import { get_weather } from './utils';

dotenv.config();

export const requireEnv = (name: string) => {
  const value = process.env[name];
  if (value === undefined || value.trim() === '') {
    throw new Error(`${name} is not set`);
  }
  return value;
};

const available_tools = {
  get_weather: get_weather,
};

async function main() {
  const API_KEY = requireEnv('API_KEY');
  const BASE_URL = requireEnv('BASE_URL');
  const MODEL_ID = requireEnv('MODEL_ID');
  const TAVILY_API_KEY = requireEnv('TAVILY_API_KEY');

  console.log(`=========初始化 OpenAI ====`);
  const llm = await new OpenAICompletionClient(API_KEY, BASE_URL, MODEL_ID);

  const prompt = `你好，请帮我查询一下今天上海的天气，然后根据天气推荐一个合适的旅游景点。`;
  const promptHistory = [`用户请求: ${prompt}`];

  const maxRange = 5;

  for (let index = 0; index < maxRange; index++) {
    console.log(`循环 ${index + 1} 次`);

    const fullPrompt = promptHistory.join('\n');

    const output = await llm.generate(fullPrompt, AGENT_SYSTEM_PROMPT);

    console.log(output);
  }
}

get_weather('上海');
