import { type ChatCompletionMessageParam } from 'openai/resources';
import { HelloAgentsLLM } from './hello-agent-llm';
import { formatPrompt, REACT_PROMPT_TEMPLATE } from './prompt';
import { ToolsExecutor } from './tools-executor';

export class ReActAgent {
  llmClient: HelloAgentsLLM;
  toolsExecutor: ToolsExecutor;
  maxStep: number;
  history: string[];

  constructor(
    llmClient: HelloAgentsLLM,
    toolsExecutor: ToolsExecutor,
    maxStep = 5,
  ) {
    this.llmClient = llmClient;
    this.toolsExecutor = toolsExecutor;
    this.maxStep = maxStep;
    this.history = [];
  }

  async run(question: string) {
    this.history = [];
    let currentStep = 0;

    while (currentStep <= this.maxStep) {
      currentStep += 1;

      console.log(`--- 执行第 ${currentStep} 步 ---`);

      const toolsDesc = this.toolsExecutor.getAvailableTools();
      let historyStr = this.history.join('\n');

      const prompt = formatPrompt(REACT_PROMPT_TEMPLATE, {
        tools: toolsDesc,
        question: question,
        history: historyStr,
      });



      let messages: Array<ChatCompletionMessageParam> = [
        {
          role: 'user',
          content: prompt,
        },
      ];

      // console.log(messages)

      const responseTxt = await this.llmClient.think(messages);

      if (!responseTxt) {
        console.error(`错误：大模型返回异常`);
        break;
      }

      console.info(responseTxt)
      const {thought, action} = this._parseOutput(responseTxt);

      if(thought) {
        console.info(`思考：${thought} \n`)
      }

      if(!action) {
        console.log('没有下一步Action, 流程终止')
        break;
      }
      
      if(action.startsWith('`Finish')) {
        const finalAnswer = this._parseActionInput(action)
        console.log(`最终答案：${finalAnswer} \n`)
        return finalAnswer;
      }

      const [toolName, toolInput] = this._parseAction(action);
      if(!toolInput || !toolName) {
        continue;
      }

      console.log(`行动: ${toolName} ${toolInput}\n`)

      const toolFun = this.toolsExecutor.getTool(toolName)
      let observation = `错误： 未找到名为 '${toolName}' 的工具`
      if(toolFun) {
        observation = await toolFun.call(null, toolInput)
      }

      console.log(`观察 ${observation} \n\n`)
      this.history.push(`Action: ${action}`)
      this.history.push(`Observation: ${observation}`)
    }

    console.log(`达到最大步数`)
    return
  }


  /**
   * 解析 LLM 输出，提取 Thought 和 Action
   */
  private _parseOutput(text: string): { thought: string | null; action: string | null } {
    const thoughtMatch = text.match(/Thought: (.*)/);
    const actionMatch = text.match(/Action: (.*)/);
    const thought = thoughtMatch?.[1]?.trim() ?? null;
    const action = actionMatch?.[1]?.trim() ?? null;
    return { thought, action };
  }

  /**
   * 解析 Action 字符串，提取工具名称和输入
   */
  private _parseAction(actionText: string): [string | null, string | null] {
    const match = actionText.match(/(\w+)\[(.*)\]/);
    if (match) {
      return [match[1] ?? null, match[2] ?? null];
    }
    return [null, null];
  }

  /**
   * 解析 Action 输入，提取参数
   */
  private _parseActionInput(text: string): string | null {
    const inputMatch = text.match(/\w+\[(.*)\]/);
    console.log(inputMatch)
    return inputMatch && typeof inputMatch[1] === 'string' ? inputMatch[1] : null;
  }
}
