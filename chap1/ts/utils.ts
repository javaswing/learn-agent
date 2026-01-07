import axios from 'axios';
import { requireEnv } from './index';
import { tavily } from '@tavily/core';

export const get_weather = async (city: string) => {
  const url = `https://wttr.in/${city}?format=j1`;

  try {
    const response = await axios.get(url);
    const data = response.data;
    const currentCondition = data['current_condition'][0];
    const weatherDesc = currentCondition['weatherDesc'][0]['value'];
    const tempC = currentCondition['temp_C'];
    const r = `${city}当前天气：${weatherDesc}, 温度${tempC}摄氏度`;
    console.log('查询天气结果: ' + r + '\n');
    return r;
  } catch (error) {}
};

export const get_attraction = async (city: string, weather: string) => {
  const apiKey = requireEnv('TAVILY_API_KEY');

  if (!apiKey) {
    throw new Error('错误：未配置TAVILY_API_KEY环境变量');
  }

  const tavily_client = tavily({ apiKey: apiKey });

  const query = `'${city}' 在 '${weather}'天气下最值得去旅游景点推荐及理由`;

  try {
    const response = await tavily_client.search(query, {
      searchDepth: 'basic',
      includeAnswer: true,
    });

    if (response.answer) {
      return response.answer;
    }

    const format_results = [];

    for (const r of response.results) {
      const t = `- ${r.title}：${r.content}`;
      format_results.push(t);
    }

    if (format_results.length == 0) {
      return '抱歉，没有找到相关的旅游景点推荐';
    }

    return '根据搜索，为您找到以下的信息： \n' + format_results.join('\n');
  } catch (error) {
    return `错误：执行 Tavily 搜索时出现问题 - ${error}`;
  }
};
