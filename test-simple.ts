#!/usr/bin/env bun
import { createOpenAICompatible } from "@ai-sdk/openai-compatible"
import { generateText } from "ai"

async function main() {
  console.log("🧪 Testando conexão direta com o modelo local...\n")
  
  const provider = createOpenAICompatible({
    name: "phi-local",
    baseURL: "http://localhost:8000/v1",
    apiKey: "unused",
    fetch: async (url: string, options: any) => {
      if (options?.body) {
        try {
          const body = JSON.parse(options.body)
          if (body.messages && Array.isArray(body.messages)) {
            body.messages = body.messages.map((msg: any) => {
              if (Array.isArray(msg.content)) {
                const allText = msg.content.every((part: any) => 
                  part.type === "text" || !part.type
                )
                if (allText) {
                  msg.content = msg.content
                    .filter((part: any) => part.type === "text" || part.text)
                    .map((part: any) => part.text)
                    .join("\n")
                }
              }
              return msg
            })
            options.body = JSON.stringify(body)
          }
        } catch (e) {
          // If parsing fails, proceed with original body
        }
      }
      return fetch(url, options)
    },
  })

  const model = provider("Phi-4-mini-reasoning-qnn-npu:1")

  console.log("📤 Enviando prompt: 'Quanto é 2+2? Responda apenas o número.'\n")

  try {
    const { text } = await generateText({
      model,
      prompt: "Quanto é 2+2? Responda apenas o número.",
      maxTokens: 50,
      temperature: 0.1,
    })

    console.log("📥 Resposta do modelo:")
    console.log(text)
    console.log("\n✅ Teste concluído com sucesso!")
  } catch (error) {
    console.error("❌ Erro:", error)
  }
}

main().catch(console.error)
