import { getJson } from 'serpapi';
import { requireEnv } from './utils';

/**
 * 基于 SerApi实现的网页搜索工具
 * @param query
 */
export async function search(query: string): Promise<string> {
  try {
    const apiKey = requireEnv('SERPAPI_API_KEY');
    if (!apiKey) {
      return '错误：SERPAPI_API_KEY没有定义在.env 文件中';
    }
    
    const params = {
      engine: 'google',
      q: query,
      api_key: apiKey,
      gl: 'cn',
      hl: 'zh-cn',
    };

    const results: any = await getJson(params);

    if (Array.isArray(results['answer_box_list'])) {
      return results['answer_box_list'].join('\n');
    }

    if (results['answer_box'] && results['answer_box']['answer']) {
      return results['answer_box']['answer'];
    }

    if (
      results['knowledge_graph'] &&
      results['knowledge_graph']['description']
    ) {
      return results['knowledge_graph']['description'];
    }

    if (
      Array.isArray(results['organic_results']) &&
      results['organic_results'].length > 0
    ) {
      // 如果没有直接答案，则返回前三个有机结果的摘要
      const snippets = results['organic_results']
        .slice(0, 3)
        .map((res: any, i: number) => {
          return `[${i + 1}] ${res.title || ''}\n${res.snippet || ''}`;
        });
      return snippets.join('\n\n');
    }

    return `对不起，没有找到关于 '${query}' 的信息。`;
  } catch (error) {
    return `发生错误: ${error}`;
  }
}
