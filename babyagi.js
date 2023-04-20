
import { Configuration, OpenAIApi } from "openai"
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

// Model configuration
const OPENAI_TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE) || 0.0

console.log('\x1b[95m\x1b[1m\n*****CONFIGURATION*****\n\x1b[0m\x1b[0m');
console.log(`Name: ${BABY_NAME}`);
console.log(`LLM: ${OPENAI_API_MODEL}`);

if (OPENAI_API_MODEL.toLowerCase().includes("gpt-4")){
    console.log("\x1b[91m\x1b[1m\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****\x1b[0m\x1b[0m");
}

console.log("\x1b[94m\x1b[1m" + "\n*****OBJECTIVE*****\n" + "\x1b[0m\x1b[0m");
console.log(`${OBJECTIVE}`);

  