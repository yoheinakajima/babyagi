
import { OpenAIEmbeddings } from "langchain/embeddings/openai"
import { OpenAI } from "langchain/llms/openai"
import {ChromaClient} from "chromadb"
import prompt from "prompt-sync"
import assert from "assert"
import * as dotenv from 'dotenv'
dotenv.config()

// const client = new ChromaClient("http://localhost:8000")

// API Keys
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || ""
assert(OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env")

const OPENAI_API_MODEL = process.env.OPENAI_API_MODEL || "gpt-3.5-turbo"

// Table config
const TABLE_NAME = process.env.TABLE_NAME || ""
assert(TABLE_NAME, "TABLE_NAME environment variable is missing from .env")

// Run config
const BABY_NAME = process.env.BABY_NAME || "BabyAGI"

// Goal config
const p = prompt()
const OBJECTIVE = p("What is BabyAGI's objective? ")
const INITIAL_TASK = p("What is the initial task to complete the objective? ")
assert(OBJECTIVE, "No objective provided.")
assert (INITIAL_TASK, "No initial task provided.")

console.log('\x1b[95m\x1b[1m\n*****CONFIGURATION*****\n\x1b[0m\x1b[0m');
console.log(`Name: ${BABY_NAME}`);
console.log(`LLM: ${OPENAI_API_MODEL}`);

if (OPENAI_API_MODEL.toLowerCase().includes("gpt-4")){
    console.log("\x1b[91m\x1b[1m\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****\x1b[0m\x1b[0m");
}

console.log("\x1b[94m\x1b[1m" + "\n*****OBJECTIVE*****\n" + "\x1b[0m\x1b[0m");
console.log(`${OBJECTIVE}`);

console.log(`\x1b[93m\x1b[1m \nInitial task: \x1b[0m\x1b[0m ${INITIAL_TASK}`);

// Define OpenAI embedding function using LangChain 
const embedding_function = new OpenAIEmbeddings()

// Create OpenAI model using LangChain
const openai = new OpenAI({
    modelName: OPENAI_API_MODEL,
    maxTokens: 100,
    temperature: 0.5,
    topP: 1,
    frquencyPenalty: 0,
    presencePenalty: 0,
    openAIApiKey: OPENAI_API_KEY
});

// Connect to chromadb and create/get collection
const chromaConnect = async ()=>{
    const chroma = new ChromaClient("http://localhost:8000");
    const metric = "cosine"
    const collections = await chroma.listCollections()
    const collectionNames = collections.map((c)=>c.name)
    var collection 
    if(collectionNames.includes(TABLE_NAME)){
        collection = await chroma.getCollection(TABLE_NAME, embedding_function)
    }
    else{
        collection = await chroma.createCollection(
            TABLE_NAME,
            {
                "hnsw:space": metric
            }, 
            embedding_function
        )
    }
    return collection
}

//Task List
const task_list = []

const add_task = (task)=>{ task_list.push(task) } 

const get_ada_embedding = async (text)=>{
    text = text.replace("\n", " ")
    const embedding = await embedding_function.embedQuery(filteredPosts[i].content)
    return embedding
}

const task_creation_agent = async (objective, result, task_description, task_list)=>{
    const prompt = `You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: ${objective}, The last completed task has the result: ${result}. This result was based on this task description: ${task_description}. These are incomplete tasks: ${task_list.join(', ')}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array.`
    const response = await openai.call(prompt)
    console.log(response)
    //new_tasks = response.choices[0].text.strip().split('\n')
    console.log(response)
    //return [{"task_name": task_name} for task_name in new_tasks]
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

(async()=>{
    const initial_task = {
        "task_id": 1,
        "task_name": INITIAL_TASK
    }
    add_task(initial_task)
    const task_id_counter = 1
    console.log(task_list)

    while (true){
        await sleep(3000)
        console.log("im back")
    }
})()
 
