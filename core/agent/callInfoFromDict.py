import os
import sys
import json
import re
from pathlib import Path

def read_full_file(filepath, project_root=None):
	"""Lê e retorna o conteúdo completo de um arquivo com busca inteligente."""
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			content = f.read()
			# Limita o conteúdo para evitar overflow do contexto
			if len(content) > 13000:  # 8k chars max
				return content[:13000] + "\n\n[... arquivo truncado para evitar overflow de contexto ...]"
			return content
	except FileNotFoundError:
		# Se não encontrar, busca o arquivo em todo o projeto
		if project_root:
			filename = os.path.basename(filepath)
			found_files = find_files_by_name(project_root, filename)
			
			if found_files:
				if len(found_files) == 1:
					# Se encontrou apenas um, tenta ler automaticamente
					try:
						with open(found_files[0], 'r', encoding='utf-8') as f:
							content = f.read()
							if len(content) > 8000:
								content = content[:8000] + "\n\n[... arquivo truncado ...]"
							return f"Arquivo encontrado em: {found_files[0]}\n\n{content}"
					except:
						return f"Arquivo encontrado mas não pôde ser lido: {found_files[0]}"
				else:
					# Se encontrou múltiplos, lista as opções
					options = "\n".join([f"- {path}" for path in found_files[:10]])  # Max 10 opções
					return f"Arquivo '{filename}' não encontrado em '{filepath}', mas encontrados {len(found_files)} arquivo(s) com esse nome:\n\n{options}\n\nPor favor, especifique o caminho completo de um dos arquivos listados."
			else:
				return f"Arquivo '{filename}' não encontrado em '{filepath}' nem em nenhum outro local do projeto."
		else:
			return f"Erro: Arquivo não encontrado em '{filepath}'."
	except Exception as e:
		return f"Erro ao ler o arquivo: {e}"

def find_files_by_name(project_root, filename):
	"""Busca arquivos por nome em todo o projeto."""
	found_files = []
	try:
		for root, dirs, files in os.walk(project_root):
			if filename in files:
				found_files.append(os.path.join(root, filename))
	except Exception:
		pass
	return found_files

def find_member_in_symbol_table(symbol_table, member_name):
	"""Busca por um método ou classe em toda a tabela de símbolos."""
	results = []
	for class_name, details in symbol_table.items():
		# Busca por classe
		if class_name.endswith(f".{member_name}"):
			results.append(class_name)
		# Busca por método/construtor
		for m in details.get('methods', []) + details.get('constructors', []):
			if member_name in m:
				results.append(class_name)
	return results

def extract_class_code_from_file(filepath, class_name):
	"""Extrai o código-fonte da classe (ou interface) do arquivo Java."""
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			code = f.read()
		# Regex para encontrar a declaração da classe/interface
		pattern = rf'(public|protected|private)?\s*(class|interface)\s+{re.escape(class_name.split(".")[-1])}\b[\s\S]*?\n}}'
		matches = re.findall(pattern, code, re.MULTILINE)
		if matches:
			# Retorna o trecho da declaração até o fechamento da classe
			# (simplificado, pode ser melhorado para casos aninhados)
			start = code.find(f'class {class_name.split(".")[-1]}')
			if start == -1:
				start = code.find(f'interface {class_name.split(".")[-1]}')
			if start == -1:
				return f"Classe {class_name} não encontrada no arquivo."
			# Busca o fechamento da classe (contagem de chaves)
			brace_count = 0
			end = start
			for i, c in enumerate(code[start:]):
				if c == '{':
					brace_count += 1
				elif c == '}':
					brace_count -= 1
					if brace_count == 0:
						end = start + i + 1
						break
			return code[start:end]
		else:
			return f"Classe {class_name} não encontrada no arquivo."
	except Exception as e:
		return f"Erro ao extrair código da classe: {e}"

def extract_method_code_from_class(class_code, method_name):
	"""Extrai o código-fonte de um método específico a partir do código da classe."""
	# Regex para encontrar o método (simplificado)
	pattern = rf'(public|protected|private|static|final|synchronized|\s)*\s*\w+\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{[\s\S]*?\n\s*\}}'
	matches = re.findall(pattern, class_code, re.MULTILINE)
	if matches:
		# Retorna o trecho do método
		# (pode ser melhorado para métodos aninhados)
		start = class_code.find(f' {method_name}(')
		if start == -1:
			start = class_code.find(f'{method_name}(')
		if start == -1:
			return f"Método {method_name} não encontrado na classe."
		# Busca o fechamento do método (contagem de chaves)
		brace_count = 0
		end = start
		for i, c in enumerate(class_code[start:]):
			if c == '{':
				brace_count += 1
			elif c == '}':
				brace_count -= 1
				if brace_count == 0:
					end = start + i + 1
					break
		return class_code[start:end]
	else:
		return f"Método {method_name} não encontrado na classe."

def get_source_code_for_member(symbol_table, class_name, method_name=None):
	"""Retorna o código-fonte da classe ou de um método específico."""
	entry = symbol_table.get(class_name)
	if not entry:
		return f"Classe {class_name} não encontrada na tabela de símbolos."
	file_path = entry['file_path']
	class_code = extract_class_code_from_file(file_path, class_name)
	if method_name:
		return extract_method_code_from_class(class_code, method_name)
	return class_code

# Sistema de paginação para controle de contexto
class ContentPaginator:
	def __init__(self):
		self.abstractions = {}  # Armazena o que foi abstraído
		self.page_size = 3000  # Tamanho máximo por página
		
	def abstract_content(self, content, content_id):
		"""Abstrai um conteúdo longo e retorna versão resumida."""
		if len(content) <= self.page_size:
			return content
			
		# Divide o conteúdo em páginas
		pages = []
		for i in range(0, len(content), self.page_size):
			pages.append(content[i:i + self.page_size])
		
		# Armazena as páginas
		self.abstractions[content_id] = pages
		
		# Retorna primeira página + resumo
		preview = pages[0]
		if len(pages) > 1:
			preview += f"\n\n[... CONTEÚDO ABSTRAÍDO - {len(pages)-1} páginas restantes ...]"
			preview += f"\n[Use continue_reading com id='{content_id}' para ver mais]"
		
		return preview
	
	def get_page(self, content_id, page_number=1):
		"""Retorna uma página específica do conteúdo abstraído."""
		if content_id not in self.abstractions:
			return f"Erro: Conteúdo '{content_id}' não encontrado."
		
		pages = self.abstractions[content_id]
		if page_number < 1 or page_number > len(pages):
			return f"Erro: Página {page_number} inválida. Disponíveis: 1-{len(pages)}"
		
		page_content = pages[page_number - 1]
		page_info = f"[Página {page_number}/{len(pages)} do conteúdo '{content_id}']"
		
		if page_number < len(pages):
			page_info += f"\n[Use continue_reading com id='{content_id}' page={page_number+1} para próxima página]"
		
		return f"{page_info}\n\n{page_content}"
	
	def get_summary(self):
		"""Retorna resumo dos conteúdos abstraídos disponíveis."""
		if not self.abstractions:
			return "Nenhum conteúdo abstraído disponível."
		
		summary = "Conteúdos abstraídos disponíveis:\n"
		for content_id, pages in self.abstractions.items():
			summary += f"- {content_id}: {len(pages)} páginas\n"
		return summary

# Instância global do paginador
paginator = ContentPaginator()

def abstract_class_code(class_code, class_name):
	"""Abstrai código de classe mostrando apenas assinaturas."""
	if len(class_code) <= 2000:
		return class_code
	
	# Extrai apenas assinaturas de métodos
	lines = class_code.split('\n')
	abstracted = []
	current_method = None
	brace_count = 0
	
	for line in lines:
		stripped = line.strip()
		
		# Cabeçalho da classe
		if 'class ' in line or 'interface ' in line:
			abstracted.append(line)
			continue
		
		# Imports e package
		if stripped.startswith('package ') or stripped.startswith('import '):
			abstracted.append(line)
			continue
		
		# Variáveis de instância
		if any(modifier in line for modifier in ['private ', 'protected ', 'public ']) and '(' not in line and '{' not in line:
			abstracted.append(line)
			continue
		
		# Assinaturas de métodos
		if any(modifier in line for modifier in ['private ', 'protected ', 'public ']) and '(' in line:
			if '{' in line:
				# Método de uma linha ou início
				method_sig = line.split('{')[0] + '{ ... }'
				abstracted.append(method_sig)
			else:
				# Assinatura multi-linha
				current_method = line
		elif current_method and '{' in line:
			current_method += ' ' + line.split('{')[0] + '{ ... }'
			abstracted.append(current_method)
			current_method = None
		elif current_method:
			current_method += ' ' + line
		
		# Fechamento da classe
		if stripped == '}' and brace_count == 0:
			abstracted.append(line)
	
	abstracted_code = '\n'.join(abstracted)
	
	# Se ainda estiver muito grande, usa o paginador
	if len(abstracted_code) > 3000:
		return paginator.abstract_content(abstracted_code, f"class_{class_name}")
	
	return abstracted_code + f"\n\n[Código abstraído - use get_code para ver implementações completas]"

def process_llm_request(request_json_str, symbol_table):
	"""
	Recebe uma string JSON do LLM, a interpreta e busca o contexto solicitado.
	Suporta paginação para conteúdos grandes.
	"""
	try:
		request = json.loads(request_json_str)
		path_file = request.get("pathFile")
		method_name = request.get("method")
		class_name = request.get("class")
		continue_reading = request.get("continue_reading")
		page = request.get("page", 1)
		abstract_mode = request.get("abstract", False)
	except json.JSONDecodeError:
		return "Erro: A requisição não é um JSON válido."
	except Exception as e:
		return f"Erro ao processar a requisição: {e}"

	# Comando para continuar lendo conteúdo abstraído
	if continue_reading:
		return paginator.get_page(continue_reading, page)

	# Comando para ver resumo de abstrações
	if request.get("list_abstractions"):
		return paginator.get_summary()

	# Regra: Se tiver apenas o pathFile, retorna o arquivo completo
	if path_file and not class_name and not method_name:
		content = read_full_file(path_file)
		if abstract_mode or len(content) > 5000:
			return paginator.abstract_content(content, f"file_{os.path.basename(path_file)}")
		return content

	# Regra: Se não houver pathFile, tenta encontrar a classe ou método na tabela
	target_class_name = class_name
	if not path_file and (class_name or method_name):
		if class_name:
			if class_name not in symbol_table:
				return f"Erro de busca: Classe '{class_name}' não encontrada na tabela de símbolos."
			target_class_name = class_name
		else: # Apenas method_name foi fornecido
			found_in = find_member_in_symbol_table(symbol_table, method_name)
			if len(found_in) == 0:
				return f"Erro de busca: Método '{method_name}' não encontrado em nenhuma classe."
			if len(found_in) > 1:
				return f"Erro de ambiguidade: Método '{method_name}' encontrado em múltiplas classes: {found_in}. Por favor, especifique a classe."
			target_class_name = found_in[0]

	if not target_class_name:
		return "Erro: Requisição inválida. Forneça 'pathFile', 'class' ou 'method'."

	# Agora que temos a classe alvo (target_class_name), buscamos o código
	class_code = get_source_code_for_member(symbol_table, target_class_name)
	method_code = None
	if method_name:
		method_code = get_source_code_for_member(symbol_table, target_class_name, method_name)

	# Aplica abstração se necessário
	if abstract_mode and class_code and len(class_code) > 2000:
		class_code = abstract_class_code(class_code, target_class_name)

	# Monta a resposta final de acordo com as regras
	if class_name and method_name:
		result = f"--- CÓDIGO DA CLASSE ---\n{class_code}\n\n--- CÓDIGO DO MÉTODO ---\n{method_code}"
	elif class_name and not method_name:
		result = class_code
	elif method_name and not class_name:
		result = method_code
	else:
		# Este caso cobre a busca implícita onde só encontramos target_class_name
		result = class_code if class_code else "Erro inesperado ao buscar contexto."
	
	# Controle de tamanho final
	if result and len(result) > 8000:
		content_id = f"{target_class_name}_{method_name if method_name else 'full'}"
		return paginator.abstract_content(result, content_id)
	
	return result
