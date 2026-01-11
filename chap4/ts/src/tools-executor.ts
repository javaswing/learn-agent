export type Tools = {
  description: string;
  func: Function;
};

/**
 * 工具执行器，负责管理和执行工具
 */
export class ToolsExecutor {
  tools: Record<string, Tools>;

  constructor() {
    this.tools = {};
  }

  registerTool(name: string, desc: string, func: Function) {
    if (name in Object.keys(this.tools)) {
      console.warn('同名工具已存在，将进行覆盖');
    }

    this.tools[name] = { description: desc, func: func };
    console.info(`工具 ${name} 已注册 \n`);
  }

  getTool(name: string) {    
    if (Object.keys(this.tools).includes(name)) {
      return this.tools[name]?.func;
    }
  }

  getAvailableTools() {
    const allTools = [];
    for (const [name, info] of Object.entries(this.tools)) {
      allTools.push(`- ${name}: ${info?.description}`);
    }

    return allTools.join('\n');
  }
}
