
export const REACT_PROMPT_TEMPLATE = `
请注意， 你是一个有能力调用外部工具的智能助手

可用工具如下：
{tools}

请严格按以下格式回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动
Action: 你采取的行动必须是以下格式之一：
- \`{{tool_name}}[{{tool_input}}]\`:调用一个可用工具
- Finish[最终答案]: 当你认为已经获取最终答案时


现在请开始解决以下问题：
Question: {question}
History: {history}
`;

/**
 * 用于格式化 REACT_PROMPT_TEMPLATE 的工具函数
 * @param template 模板字符串
 * @param params 需要替换的占位符对象
 * @returns 格式化后的字符串
 */
export function formatPrompt(template: string, params: Record<string, string>): string {
	return template.replace(/\{(\w+)\}/g, (_, key) => {
		return params[key] ?? `{${key}}`;
	});
}