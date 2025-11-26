## IMPORTANT

- Try to keep things in one function unless composable or reusable
- DO NOT do unnecessary destructuring of variables
- DO NOT use `else` statements unless necessary
- DO NOT use `try`/`catch` if it can be avoided
- AVOID `try`/`catch` where possible
- AVOID `else` statements
- AVOID using `any` type
- AVOID `let` statements
- PREFER single word variable names where possible
- Use as many bun apis as possible like Bun.file()

## LOCAL MODEL CONTEXT LIMITS

**CRITICAL**: This project uses a local Phi-3 model with **4096 token limit** (input + output).

### Token Management
- Keep responses under 1000 tokens
- Input context limited to ~3000 tokens
- Be EXTREMELY concise in all responses
- Avoid reading large files or multiple files at once
- Use Task tool for context-heavy operations
- DO NOT include long explanations or verbose output

### Response Style for Local Model
- Answer in 1-3 sentences maximum
- Skip preamble and postamble
- Use bullet points for lists
- Omit unnecessary context

## Debugging

- To test opencode in the `packages/opencode` directory you can run `bun dev`

## Tool Calling

- ALWAYS USE PARALLEL TOOLS WHEN APPLICABLE. Here is an example illustrating how to execute 3 parallel file reads in this chat environment:

json
{
"recipient_name": "multi_tool_use.parallel",
"parameters": {
"tool_uses": [
{
"recipient_name": "functions.read",
"parameters": {
"filePath": "path/to/file.tsx"
}
},
{
"recipient_name": "functions.read",
"parameters": {
"filePath": "path/to/file.ts"
}
},
{
"recipient_name": "functions.read",
"parameters": {
"filePath": "path/to/file.md"
}
}
]
}
}
