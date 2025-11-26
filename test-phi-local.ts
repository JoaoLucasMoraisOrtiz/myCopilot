#!/usr/bin/env bun
import { Provider } from "./packages/opencode/src/provider/provider"
import { Instance } from "./packages/opencode/src/project/instance"

async function main() {
  console.log("🔍 Listando providers disponíveis...\n")
  
  // Timeout de segurança
  const timeout = setTimeout(() => {
    console.error("❌ Timeout: O carregamento dos providers demorou mais de 30 segundos")
    process.exit(1)
  }, 30000)
  
  try {
    // Inicializar contexto do projeto
    await Instance.provide({
      directory: process.cwd(),
      fn: async () => {
        console.log("📦 Carregando providers...")
        const providers = await Provider.list()
        const providerNames = Object.keys(providers)
  
  console.log(`Total de providers carregados: ${providerNames.length}`)
  console.log("Providers:", providerNames.join(", "))
  console.log()
  
  // Verificar se phi-local foi carregado
  if (providers["phi-local"]) {
    console.log("✅ Provider 'phi-local' encontrado!")
    console.log("   Nome:", providers["phi-local"].info.name)
    console.log("   API:", providers["phi-local"].info.api)
    console.log("   NPM:", providers["phi-local"].info.npm)
    console.log("   Source:", providers["phi-local"].source)
    console.log("\n📋 Modelos disponíveis:")
    
    for (const [modelID, model] of Object.entries(providers["phi-local"].info.models)) {
      console.log(`   - ${modelID}`)
      console.log(`     Nome: ${model.name}`)
      console.log(`     Reasoning: ${model.reasoning}`)
      console.log(`     Context limit: ${model.limit.context}`)
    }
    
    // Tentar carregar o modelo
    console.log("\n🔧 Testando getModel()...")
    try {
      const model = await Provider.getModel("phi-local", "Phi-3-mini-128k-instruct-qnn-npu:1")
      console.log("✅ Modelo carregado com sucesso!")
      console.log("   Provider ID:", model.providerID)
      console.log("   Model ID:", model.modelID)
      console.log("   Language Model:", typeof model.language)
    } catch (error) {
      console.error("❌ Erro ao carregar modelo:", error)
    }
  } else {
    console.log("❌ Provider 'phi-local' NÃO foi encontrado")
    console.log("\n💡 Certifique-se de que:")
    console.log("   1. A variável MODELS_DEV_API_JSON está setada")
    console.log("   2. O caminho aponta para local-model-config.json")
    console.log("   3. A variável PHI_LOCAL_API_KEY está definida (pode ser 'unused')")
  }
      },
    })
  
    clearTimeout(timeout)
    console.log("\n✅ Teste concluído!")
  } catch (error) {
    clearTimeout(timeout)
    console.error("❌ Erro durante o teste:", error)
    throw error
  }
}

main().catch(console.error)
