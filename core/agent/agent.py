import os
import sys
import json
from pathlib import Path

# Importa as ferramentas do analisador e do protocolo handler
sys.path.append(str(Path(__file__).parent.parent / 'analyzers'))
sys.path.append(str(Path(__file__).parent / 'agent'))
sys.path.append(str(Path(__file__).parent / 'llm'))


from analyzers.java_analyzer import build_symbol_table, generate_report, resolve_type
from callInfoFromDict import get_source_code_for_member, read_full_file
from callInfoFromDict import process_llm_request
from core.llm.llm_client import LLMClient
from core.agent.agent_prompts import SYSTEM_PROMPT_TEMPLATE, USER_START_PROMPT, TOOL_OBSERVATION_PROMPT

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
def call_llm(messages):
    # Usa o LLMClient para enviar o prompt e receber a resposta
    prompt = '\n'.join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
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

def run_agent(user_goal, project_path, max_turns=10):
    symbol_table = build_symbol_table_with_relations(project_path)
    system_prompt = get_system_prompt(user_goal)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": USER_START_PROMPT}
    ]
    print("INFO: Agente iniciado. Objetivo:", user_goal)
    print("="*50)
    for turn in range(max_turns):
        print(f"\n--- TURNO {turn + 1} ---")
        llm_response_content = call_llm(messages)
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
        print("Uso: python agent.py <caminho_do_projeto_java> \"<seu_objetivo>\"")
        sys.exit(1)
    project_path = sys.argv[1]
    user_goal = sys.argv[2]
    run_agent(user_goal, project_path)
