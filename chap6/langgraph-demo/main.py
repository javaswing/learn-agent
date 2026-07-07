from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
import os
from tavily import TavilyClient
from langgraph.checkpoint.memory import InMemorySaver
import asyncio

load_dotenv()

# 全局状态 State
class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str # 经过 LLM理解后的用户需求总结
    search_query: str # 优化后用户Tavily API的搜索查询
    search_results: str # Tavily API 返回的搜索结果
    final_answer: str # 最终生成的答案
    step: str # 标记当前步骤



llm = ChatOpenAI(
    model = os.getenv("LLM_MODEL_ID"),
    api_key = os.getenv("LLM_API_KEY"),
    base_url = os.getenv("LLM_BASE_URL"),
    timeout = int(os.getenv("LLM_TIMEOUT", 60))
)

tavily_client = TavilyClient(
    api_key = os.getenv("SERPAPI_API_KEY")
)


def understand_query_node(state: SearchState) -> SearchState:
    """
    1. 通过 LLM 理解用户的查询意图
    2. 将理解后的用户查询意图存储在 state 中
    """
    if not state['messages']:
        user_message = ""
    else:
        latest_message = state['messages'][-1]
        if hasattr(latest_message, "content"):
            user_message = latest_message.content
        elif isinstance(latest_message, dict):
            user_message = latest_message.get("content", "")
        else:
            user_message = str(latest_message)

    understand_query_prompt = f""" 分析用户的查询: "{user_message}"
    请完成两个任务：
    1. 简单总结用户想要什么
    2. 生成适合搜索引擎的关键词（中英均可，要精准）

    格式：
    理解：[用户需求总结]
    搜索词：[搜索引擎关键词]
    """

    response = llm.invoke([SystemMessage(content=understand_query_prompt)])
    response_txt = response.content

    # 解析 LLM
    search_query = user_message

    if "搜索词：" in response_txt:
        search_query = response_txt.split("搜索词：")[1].strip()

    return {
        "search_query": search_query,
        "user_query": response_txt,
        "step": "understood",
        "messages": [AIMessage(content=f"我将为你搜索：{search_query}")]
    }

def tavily_search_node(state: SearchState) -> SearchState:
    """
    1. 使用 Tavily API 搜索用户查询
    2. 将搜索结果存储在 state 中
    """
    search_query = state['search_query']
    try:
        response = tavily_client.search(query=search_query, search_depth="basic", max_results=3, include_answer=True)
        search_results = ""
        if response.get("answer"):
            search_results = f"综合答案：\n {response['answer']}\n\n"
        
        if response.get("results"):
            search_results += "相关信息：\n"
            for idx, result in enumerate(response['results'][:3], 1):
                search_results += f"{idx}. {result.get('title', '')}\n {result.get('content', '')}\n 来源：{result.get('link', '')}\n\n"
            
        if not search_results:
            search_results = "抱歉，没有找到相关信息"
        
        return {
            "search_results": search_results,
            "step": "searched",
            "search_query": search_query,
            "messages": [AIMessage(content=f"✅ 搜索完成！找到了相关信息，正在为您整理答案...")]
        }

    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        print(f"❌ {error_msg}")
        return {"search_results": f"搜索失败: {str(e)}", "step": "search_failed", "messages": [AIMessage(content=f"搜索失败: {str(e)}")]}
    

def generate_answer_node(state: SearchState) -> SearchState:
    """
    1. 使用 LLM 生成最终答案
    2. 将最终答案存储在 state 中
    """
    if state['step'] == "search_failed":
        fallback_prompt = f"""搜索API暂时不可用，请基于您的知识回答用户的问题：
        用户问题: "{state['user_query']}"

        请提供一个有用的回答，并说明这是基于已有知识的回答。"""

        response = llm.invoke([SystemMessage(content=fallback_prompt)])
        return {
            "final_answer": response.content,
            "step": "answered",
            "messages": [AIMessage(content=f"✅ 基于 AI自身知识已生成最终答案！{response.content}")]
        }
    
    answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：

用户问题：{state['user_query']}

搜索结果：
{state['search_results']}

请要求：
1. 综合搜索结果，提供准确、有用的回答
2. 如果是技术问题，提供具体的解决方案或代码
3. 引用重要信息的来源
4. 回答要结构清晰、易于理解
5. 如果搜索结果不够完整，请说明并提供补充建议"""
    
    response = llm.invoke([SystemMessage(content=answer_prompt)])

    return {
        "final_answer": response.content,
        "step": "answered",
        "messages": [AIMessage(content=f"✅ 已生成最终答案！{response.content}")]
    }


def create_search_assistant():
    workflow = StateGraph(SearchState)

    # 添加节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    memory = InMemorySaver()

    app = workflow.compile(checkpointer=memory)
    return app

async def main():
    if not os.getenv("SERPAPI_API_KEY"):
        print("❌ 错误：请在.env文件中配置SERPAPI_API_KEY")
        return
    
    app = create_search_assistant()
    print("🔍 智能搜索助手启动！")
    print("我会使用Tavily API为您搜索最新、最准确的信息")
    print("支持各种问题：新闻、技术、知识问答等")
    print("(输入 'quit' 退出)\n")

    session_count = 0

    while True:
        user_input = input("🤔 您想了解什么: ").strip()

        if user_input.lower() in ['quit', 'q', '退出', 'exit']:
            print("感谢使用！再见！👋")
            break
            
        if not user_input:
            continue

        session_count += 1
        config = {"configurable": {"thread_id": f"search-session-{session_count}"}}

        print(f"\n📝 您的查询: {user_input}")
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": "start"
        }

        print("messages:", initial_state["messages"])

        try:
            print("\n" + "="*60)

            # 执行工作流
            async for output in app.astream(initial_state, config=config):
                for node_name, node_output in output.items():
                    if "messages" in node_output and node_output["messages"]:
                        latest_message = node_output["messages"][-1]
                        if isinstance(latest_message, AIMessage):
                            if node_name == "understand":
                                print(f"🧠 理解阶段: {latest_message.content}")
                            elif node_name == "search":
                                print(f"🔍 搜索阶段: {latest_message.content}")
                            elif node_name == "answer":
                                print(f"\n💡 最终回答:\n{latest_message.content}")
            
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")
            continue


if __name__ == "__main__":
    asyncio.run(main())