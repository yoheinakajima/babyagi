import { Configuration, OpenAIApi } from "openai"
import { ChromaClient, OpenAIEmbeddingFunction } from "chromadb"
import prompt from "prompt-sync"
import assert from "assert"
import * as dotenv from "dotenv"
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

console.log('\x1b[95m\x1b[1m\n*****CONFIGURATION*****\n\x1b[0m\x1b[0m')
console.log(`Name: ${BABY_NAME}`)
console.log(`LLM: ${OPENAI_API_MODEL}`)

if (OPENAI_API_MODEL.toLowerCase().includes("gpt-4")){
    console.log("\x1b[91m\x1b[1m\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****\x1b[0m\x1b[0m")
}

console.log("\x1b[94m\x1b[1m" + "\n*****OBJECTIVE*****\n" + "\x1b[0m\x1b[0m")
console.log(`${OBJECTIVE}`)

console.log(`\x1b[93m\x1b[1m \nInitial task: \x1b[0m\x1b[0m ${INITIAL_TASK}`)

// Define OpenAI embedding function using Chroma 
const embeddingFunction = new OpenAIEmbeddingFunction(OPENAI_API_KEY)

// Configure OpenAI
const configuration = new Configuration({
  apiKey: OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

//Task List
var taskList = []

// Connect to chromadb and create/get collection
const chromaConnect = async ()=>{
    const chroma = new ChromaClient("http://localhost:8000")
    const metric = "cosine"
    const collections = await chroma.listCollections()
    const collectionNames = collections.map((c)=>c.name)
    if(collectionNames.includes(TABLE_NAME)){
        const collection = await chroma.getCollection(TABLE_NAME, embeddingFunction)
        return collection
    }
    else{
        const collection = await chroma.createCollection(
            TABLE_NAME,
            {
                "hnsw:space": metric
            }, 
            embeddingFunction
        )
        return collection
    }
}

const add_task = (task)=>{ taskList.push(task) } 

const clear_tasks = ()=>{ taskList = [] }

const get_ada_embedding = async (text)=>{
    text = text.replace("\n", " ")
    const embedding = await embeddingFunction.generate(text)
    return embedding
}

const openai_completion = async (prompt, temperature=0.5, maxTokens=100)=>{
    if(OPENAI_API_MODEL.startsWith("gpt-")){
        const messages = [{"role": "system", "content": prompt}]
        const response = await openai.createChatCompletion({
            model: OPENAI_API_MODEL,
            messages: messages,
            max_tokens: maxTokens,
            temperature: temperature,
            n: 1,
            stop: null
        })
        return response.data.choices[0].message.content.trim()
    }
    else {
        const response = await openai.createCompletion({
            model: OPENAI_API_MODEL,
            prompt: prompt,
            max_tokens: maxTokens,
            temperature: temperature,
            top_p: 1,
            frequency_penalty: 0,
            presence_penalty: 0
        })
        return response.data.choices[0].text.trim()
    }
}

const task_creation_agent = async (objective, result, task_description, taskList)=>{
    const prompt = `
        You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: ${objective}, 
        The last completed task has the result: ${result}. 
        This result was based on this task description: ${task_description}. 
        These are incomplete tasks: ${taskList.map(task=>`${task.taskId}: ${task.taskName}`).join(', ')}. 
        Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. 
        Return the tasks as an array.`
    const response = await openai_completion(prompt)
    const newTasks = response.trim().includes("\n") ? response.trim().split("\n") : [response.trim()];
    return newTasks.map(taskName => ({ taskName: taskName }));    
}



const prioritization_agent = async (taskId)=>{
    const taskNames = taskList.map((task)=>task.taskName)
    const nextTaskId = taskId+1
    const prompt = `
    You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: ${taskNames}. 
    Consider the ultimate objective of your team:${OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number ${nextTaskId}.`
    const response = await openai_completion(prompt)
    const newTasks = response.trim().includes("\n") ? response.trim().split("\n") : [response.trim()];
    clear_tasks()
    newTasks.forEach((newTask)=>{
        const newTaskParts = newTask.trim().split(/\.(?=\s)/)
        if (newTaskParts.length == 2){
            const newTaskId = newTaskParts[0].trim()
            const newTaskName = newTaskParts[1].trim()
            add_task({
                taskId: newTaskId, 
                taskName: newTaskName
            })
        }
    })
}

const execution_agent = async (objective, task, chromaCollection)=>{
    const context = context_agent(objective, 5, chromaCollection)
    const prompt = `
    You are an AI who performs one task based on the following objective: ${objective}\n.
    Take into account these previously completed tasks: ${context}\n.
    Your task: ${task}\nResponse:`
    const response = await openai_completion(prompt, undefined, 2000)
    return response
}

const context_agent = async (query, topResultsNum, chromaCollection)=>{
    const count = await chromaCollection.count()
    if (count == 0){
        return []
    }
    const results = await chromaCollection.query(
        undefined, 
        Math.min(topResultsNum, count), 
        undefined,
        query,
    )
    return results.metadatas[0].map(item=>item.task)
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

(async()=>{
    const initialTask = {
        taskId: 1,
        taskName: INITIAL_TASK
    }
    add_task(initialTask)
    const chromaCollection = await chromaConnect()
    var taskIdCounter = 1
    while (true){
        if(taskList.length>0){
            console.log("\x1b[95m\x1b[1m"+"\n*****TASK LIST*****\n"+"\x1b[0m\x1b[0m")
            taskList.forEach(t => {
                console.log(" • " + t.taskName)
            })

            // Step 1: Pull the first task
            const task = taskList.shift()
            console.log("\x1b[92m\x1b[1m"+"\n*****NEXT TASK*****\n"+"\x1b[0m\x1b[0m")
            console.log(task.taskId + ": " + task.taskName)
            
            // Send to execution function to complete the task based on the context
            const result = await execution_agent(OBJECTIVE, task.taskName, chromaCollection)
            const currTaskId = task.taskId
            console.log("\x1b[93m\x1b[1m"+"\nTASK RESULT\n"+"\x1b[0m\x1b[0m")
            console.log(result)

            // Step 2: Enrich result and store in Chroma
            const enrichedResult = { data : result}  // this is where you should enrich the result if needed
            const resultId = `result_${task.taskId}`
            const vector = enrichedResult.data // extract the actual result from the dictionary
            const collectionLength =  (await chromaCollection.get([resultId])).ids?.length
            if(collectionLength>0){
                await chromaCollection.update(
                    resultId,
                    undefined,
                    {task: task.taskName, result: result},
                    vector
                )
            }
            else{
                await chromaCollection.add(
                    resultId,
                    undefined,
                    {task: task.taskName, result},
                    vector
                )
            }
            
            // Step 3: Create new tasks and reprioritize task list
            const newTasks = await task_creation_agent(OBJECTIVE, enrichedResult, task.taskName, taskList.map(task=>task.taskName))
            newTasks.forEach((task)=>{
                taskIdCounter += 1
                task.taskId = taskIdCounter
                add_task(task)
            })
            await prioritization_agent(currTaskId)
            await sleep(3000)
        }
    }
})()
 
