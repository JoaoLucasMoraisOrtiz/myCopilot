import os
import sys
import json
from pathlib import Path

# Importa as ferramentas do analisador e do protocolo handler
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from analyzers.java_analyzer import build_symbol_table, generate_report, resolve_type
from callInfoFromDict import get_source_code_for_member, read_full_file
from callInfoFromDict import process_llm_request
from core.llm.llm_client import LLMClient
from devtools.gemini_client import GeminiLLMInterface
from core.agent.agent_prompts import (
    SYSTEM_PROMPT_TEMPLATE, USER_START_PROMPT, TOOL_OBSERVATION_PROMPT,
    SYSTEM_PROMPT_CONTINUATION_TEMPLATE, SYSTEM_PROMPT_NEW_MODE_CONTINUATION_TEMPLATE
)

# ===================== Ferramentas do agente =====================
def build_symbol_table_with_relations(root_dir):
    return build_symbol_table(root_dir)

def get_class_metadata(symbol_table, class_name):
    entry = symbol_table.get(class_name)
    if not entry:
        return f"Classe '{class_name}' não encontrada."
    # Resumo estruturado
    return json.dumps({
        'file_path': entry['file_path'],
        'type': entry['type'],
        'extends': entry['extends'],
        'implements': entry['implements'],
        'fields': entry['fields'],
        'constructors': entry['constructors'],
        'methods': entry['methods'],
        'relationships': entry['relationships']
    }, indent=2, ensure_ascii=False)

def get_code(symbol_table, class_name, method_name=None):
    return get_source_code_for_member(symbol_table, class_name, method_name)

def list_classes(symbol_table):
    return '\n- '.join(symbol_table.keys())

def read_file(filepath):
    return read_full_file(filepath)

# ===================== LLM Client =====================
def call_llm(messages, llm_type="vscode", websocket_url="ws://127.0.0.1:9222"):
    """
    Chama o LLM usando a interface especificada.
    
    Args:
        messages: Lista de mensagens da conversa
        llm_type: Tipo de LLM ("vscode", "gemini", "gemini_api" ou "codestral")
        websocket_url: URL do WebSocket para Gemini
    """
    prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
    
    if llm_type == "gemini":
        try:
            gemini_interface = GeminiLLMInterface(websocket_url)
            response = gemini_interface.send_message(prompt)
            return response
        except Exception as e:
            print(f"⚠️ Erro no Gemini Chrome, fallback para VS Code: {e}")
            # Fallback para VS Code
    elif llm_type == "gemini_api":
        try:
            from devtools.gemini_api_client import GeminiAPILLMInterface
            gemini_api_interface = GeminiAPILLMInterface()
            response = gemini_api_interface.call_llm(messages)
            return response
        except Exception as e:
            print(f"⚠️ Erro no Gemini API, fallback para VS Code: {e}")
            # Fallback para VS Code
    elif llm_type == "codestral":
        try:
            from devtools.codestral_api_client import CodestralLLMInterface
            codestral_interface = CodestralLLMInterface()
            response = codestral_interface.call_llm(messages)
            return response
        except Exception as e:
            print(f"⚠️ Erro no Codestral API, fallback para VS Code: {e}")
            # Fallback para VS Code
    
    # Interface padrão VS Code
    client = LLMClient()
    client.connect()
    response = client.send_prompt(prompt)
    client.close()
    return response

def parse_action_from_response(response_content):
    try:
        json_str = response_content[response_content.find('{'):response_content.rfind('}')+1]
        return json.loads(json_str)
    except Exception:
        print("AVISO: Não foi possível parsear o JSON da resposta do LLM.")
        return {"command": "error", "args": ["JSON mal formatado na resposta."]}

def execute_tool(action_json, symbol_table):
    command = action_json.get("command")
    args = action_json.get("args", [])
    if command == "list_classes":
        return list_classes(symbol_table)
    elif command == "get_class_metadata":
        return get_class_metadata(symbol_table, *args)
    elif command == "get_code":
        return get_code(symbol_table, *args)
    elif command == "read_file":
        return read_file(*args)
    elif command == "final_answer":
        return args[0] if args else "[final_answer sem conteúdo]"
    else:
        return f"Erro: Comando '{command}' desconhecido."

def get_system_prompt(user_goal):
    return SYSTEM_PROMPT_TEMPLATE.format(user_goal=user_goal)

def run_agent(user_goal, project_path, max_turns=10, llm_type="vscode", websocket_url="ws://127.0.0.1:9222"):

    """ 
    Esta função inicia o agente com o objetivo do usuário e o caminho do projeto.
    O agente interage com o LLM, executa ações e coleta informações do projeto.
    O agente continuará até atingir o número máximo de turnos ou receber uma resposta final.
    O LLM pode ser configurado para usar diferentes interfaces (vscode, gemini, gemini_api, codestral).
    O agente também pode alternar para um modo de prompt reduzido após o primeiro turno.
    Se o LLM falhar, ele tentará usar uma interface alternativa.
    O agente imprime informações sobre o progresso e as respostas finais.
    O agente utiliza um símbolo de tabela para resolver referências e executar ações.
    O agente também pode ler arquivos e obter metadados de classes.
    O agente é projetado para ser executado a partir da linha de comando com argumentos opcion
    ais para o tipo de LLM e a URL do WebSocket.
    O agente imprime mensagens de log para informar o usuário sobre o progresso e as ações executadas
    e também para indicar erros ou problemas na execução.
    O agente é configurado para trabalhar com projetos Java, mas pode ser adaptado para outros
    tipos de projetos com modificações nas ferramentas de análise e nos prompts.
    O agente é iniciado com um prompt de sistema que define o contexto e o objetivo do usuário
    e também inclui um prompt de início do usuário para iniciar a conversa.
    O agente utiliza um prompt de observação de ferramenta para relatar os resultados da execução
    de ações e interagir com o LLM.
    O agente é projetado para ser modular e extensível, permitindo a adição de novas
    ferramentas e funcionalidades conforme necessário.
    O agente pode ser executado em um ambiente de desenvolvimento local ou em um servidor remoto,
    dependendo das necessidades do usuário e da configuração do projeto.
    O agente é uma implementação básica de um assistente de desenvolvimento que pode ser
    aprimorada com mais funcionalidades, como suporte a diferentes linguagens de programação,
    integração com sistemas de controle de versão, análise de código estático e dinâmico,
    e outras ferramentas de desenvolvimento.
    """

    symbol_table = build_symbol_table_with_relations(project_path)
    system_prompt = get_system_prompt(user_goal)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": USER_START_PROMPT}
    ]
    print("INFO: Agente iniciado. Objetivo:", user_goal)
    print(f"INFO: Usando LLM: {llm_type}")
    print("="*50)
    for turn in range(max_turns):
        # Troca para prompt reduzido a partir do segundo turno
        if turn == 1:
            if llm_type == "new":
                continuation_prompt = SYSTEM_PROMPT_NEW_MODE_CONTINUATION_TEMPLATE.format(user_goal=user_goal)
            else:
                continuation_prompt = SYSTEM_PROMPT_CONTINUATION_TEMPLATE.format(user_goal=user_goal)
            messages[0]["content"] = continuation_prompt
        print(f"\n--- TURNO {turn + 1} ---")
        llm_response_content = call_llm(messages, llm_type, websocket_url)
        messages.append({"role": "assistant", "content": llm_response_content})
        action_json = parse_action_from_response(llm_response_content)
        if action_json.get("command") == "final_answer":
            print("\n" + "="*20 + " RESPOSTA FINAL DO AGENTE " + "="*20)
            print(action_json["args"][0])
            return
        execution_result = execute_tool(action_json, symbol_table)
        tool_observation_prompt = TOOL_OBSERVATION_PROMPT.format(execution_result=execution_result)
        messages.append({"role": "user", "content": tool_observation_prompt})
    print("INFO: Agente atingiu o número máximo de turnos.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python agent.py <caminho_do_projeto> \"<seu_objetivo>\" [llm_type] [websocket_url]")
        print("  llm_type: 'vscode' (padrão), 'gemini' ou 'gemini_api'")
        print("  websocket_url: URL do WebSocket para Gemini (padrão: ws://127.0.0.1:9222)")
        sys.exit(1)
    
    project_path = sys.argv[1]
    user_goal = sys.argv[2]
    llm_type = sys.argv[3] if len(sys.argv) > 3 else "vscode"
    websocket_url = sys.argv[4] if len(sys.argv) > 4 else "ws://127.0.0.1:9222"
    
    run_agent(user_goal, project_path, llm_type=llm_type, websocket_url=websocket_url)
