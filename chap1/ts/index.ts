import * as dotenv from 'dotenv'
import OpenAI from 'openai'
import { AGENT_SYSTEM_PROMPT } from './const'

dotenv.config()

const requireEnv = (name: string) => {
        const value = process.env[name]
        if (value === undefined || value.trim() === '') {
            throw new Error(`${name} is not set`)
        }
        return value
    }


async function initLLMClient(API_KEY: string, BASE_URL: string, MODEL_ID: string) {
    const client = new OpenAI({
        apiKey: API_KEY,
        baseURL: BASE_URL
    })

    const prompt = `你好，请帮我查询一下今天上海的天气，然后根据天气推荐一个合适的旅游景点。`

    const messages: OpenAI.ChatCompletionMessageParam[] = [
        { role: 'system', content: AGENT_SYSTEM_PROMPT },
        { role: 'user', content: prompt }
    ]

    const response = await client.chat.completions.create(
        {
            model: MODEL_ID,
            messages: messages,
            stream: false
        }
    )

    const answer = response.choices[0]?.message.content
    return answer
}

async function main() {    
    const API_KEY = requireEnv('API_KEY')
    const BASE_URL = requireEnv('BASE_URL')
    const MODEL_ID = requireEnv('MODEL_ID')
    const TAVILY_API_KEY = requireEnv('TAVILY_API_KEY')

    console.log(`=========初始化 OpenAI ====`)
    await initLLMClient(API_KEY, BASE_URL, MODEL_ID)
}

main()


