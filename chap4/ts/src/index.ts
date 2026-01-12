import { HelloAgentsLLM } from "./hello-agent-llm"
import { ReActAgent } from "./react-agent"
import { search } from "./tools"
import { ToolsExecutor } from "./tools-executor"

import * as dotenv from 'dotenv';
dotenv.config();
// console.log('LLM_MODEL_ID:', process.env.LLM_MODEL_ID);

function main() {
    const llm = new HelloAgentsLLM()
    const toolsExecutor = new ToolsExecutor()

    const searchDesc = "搜索工具，可以根据关键词搜索信息"
    toolsExecutor.registerTool("Search", searchDesc, search)    

    const reActAgent = new ReActAgent(llm, toolsExecutor);
    const question = "小米最新的手机是哪一款？它的卖点是什么?"

    reActAgent.run(question)

}


main()