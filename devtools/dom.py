import time
from typing import Optional, Tuple, List

# Cache global para evitar re-busca de elementos
_element_cache = {}
_cache_max_size = 50

def _cleanup_cache():
    """Limpa cache quando fica muito grande para evitar memory leak."""
    global _element_cache
    if len(_element_cache) > _cache_max_size:
        # Remove metade das entradas mais antigas
        keys_to_remove = list(_element_cache.keys())[:_cache_max_size // 2]
        for key in keys_to_remove:
            del _element_cache[key]
        print(f"🧹 Cache DOM limpo ({len(keys_to_remove)} entradas removidas)")

def enable_dom(client):
    """Habilita o domínio DOM no DevTools com retry."""
    response = client.send('DOM.enable')
    if not response:
        raise Exception("Falha ao habilitar domínio DOM")
    return response


def get_document(client):
    """Retorna o nodo raiz do documento com retry."""
    response = client.send('DOM.getDocument', {'depth': -1})
    if not response or 'result' not in response:
        raise Exception("Falha ao obter documento")
    return response.get('result', {}).get('root', {})


def query_selector(client, root_node_id, selector):
    """Encontra um nó usando seletor CSS e retorna o nodeId."""
    res = client.send('DOM.querySelector', {'nodeId': root_node_id, 'selector': selector})
    return res.get('result', {}).get('nodeId')


def get_box_model(client, node_id):
    """Obtém o modelo de caixa de um nó para coordenadas e dimensões."""
    res = client.send('DOM.getBoxModel', {'nodeId': node_id})
    return res.get('result', {}).get('model')


def get_document_with_retries(client, frame_id, retries=5, delay=1.0):
    """
    Tenta obter o documento raiz de um frame, com retry robusto.
    Reduzido para 5 tentativas para evitar loops longos.
    """
    for i in range(retries):
        try:
            response = client.send('DOM.getDocument', {'frameId': frame_id, 'depth': -1})
            if response and 'result' in response and 'root' in response['result']:
                print(f"  ✅ Documento para frame {frame_id} obtido (tentativa {i+1})")
                return response['result']['root']
        except Exception as e:
            print(f"  ❌ Tentativa {i+1} falhou para frame {frame_id}: {e}")
        
        if i < retries - 1:  # Não aguarda na última tentativa
            print(f"  ⏳ Aguardando {delay}s...")
            time.sleep(delay)
    
    print(f"  💥 Falha definitiva ao obter documento para frame {frame_id}")
    return None

def find_nodes_by_tag_recursive(client, node, tag_name, found_nodes):
    """
    Busca recursivamente por nós com uma tag específica a partir de um nó raiz.
    Esta função agora apenas busca dentro do documento fornecido e não atravessa iframes.
    """
    # Verifica se o nó atual corresponde à tag procurada
    if node.get('nodeName', '').lower() == tag_name.lower():
        found_nodes.append(node['nodeId'])

    # Continua a busca nos nós filhos, se existirem
    if 'children' in node:
        for child_node in node['children']:
            find_nodes_by_tag_recursive(client, child_node, tag_name, found_nodes)


def find_elements_in_frames(client, tag_name):
    """
    Busca por elementos com uma tag específica em todos os frames da página,
    usando uma abordagem robusta com novas tentativas.
    Retorna uma lista de (node_id, frame_id).
    """
    client.send('DOM.enable')
    client.send('Page.enable') # Necessário para getFrameTree

    results = []
    
    frame_tree_res = client.send('Page.getFrameTree')
    frame_tree = frame_tree_res.get('result', {}).get('frameTree', {})

    frames_to_process = []
    
    def collect_frames(frame_node):
        frames_to_process.append(frame_node['frame'])
        if 'childFrames' in frame_node:
            for child_frame in frame_node['childFrames']:
                collect_frames(child_frame)

    collect_frames(frame_tree)

    print(f"Iniciando busca por '<{tag_name}>' em {len(frames_to_process)} frames...")

    for frame_info in frames_to_process:
        frame_id = frame_info['id']
        print(f"Processando frame {frame_id} (URL: {frame_info.get('url', 'N/A')})")

        document_root = get_document_with_retries(client, frame_id)
        
        if document_root:
            found_node_ids = []
            find_nodes_by_tag_recursive(client, document_root, tag_name, found_node_ids)
            
            for node_id in found_node_ids:
                print(f"SUCESSO: Encontrado '<{tag_name}>' (nodeId: {node_id}) no frame {frame_id}")
                results.append((node_id, frame_id))
        else:
            print(f"AVISO: Não foi possível obter o documento para o frame {frame_id}. Pulando.")

    print(f"Busca concluída. Total de '<{tag_name}>' encontrados: {len(results)}")
    return results


def find_first_element(client, tag_name):
    """
    Encontra o primeiro elemento com a tag_name especificada.
    Retorna (node_id, frame_id) ou (None, None).
    """
    elements = find_elements_in_frames(client, tag_name)
    print(elements)
    if elements:
        return elements[0]
    return None, None

def find_last_element(client, tag_name):
    """
    Encontra o primeiro elemento com a tag_name especificada.
    Retorna (node_id, frame_id) ou (None, None).
    """
    elements = find_elements_in_frames(client, tag_name)
    if elements:
        return elements[-1]
    return None, None

def find_element_by_selector(client, selector):
    """
    Encontra elemento por seletor CSS com cache e melhor gerenciamento de recursos.
    """
    global _element_cache
    
    # Verifica cache primeiro
    cache_key = f"selector:{selector}"
    if cache_key in _element_cache:
        cached_result = _element_cache[cache_key]
        # Verifica se o elemento ainda existe
        try:
            response = client.send('DOM.describeNode', {'nodeId': cached_result[0]})
            if response and 'result' in response:
                return cached_result
        except:
            # Remove do cache se não existe mais
            del _element_cache[cache_key]
    
    try:
        response = client.send('DOM.enable')
        if not response:
            return None, None
            
        response = client.send('Page.enable')
        if not response:
            return None, None

        frame_tree_res = client.send('Page.getFrameTree')
        if not frame_tree_res or 'result' not in frame_tree_res:
            return None, None
            
        frame_tree = frame_tree_res.get('result', {}).get('frameTree', {})

        frames_to_process = []
        def collect_frames(frame_node):
            frames_to_process.append(frame_node['frame'])
            if 'childFrames' in frame_node:
                for child_frame in frame_node['childFrames']:
                    collect_frames(child_frame)
        collect_frames(frame_tree)

        print(f"🔍 Buscando seletor em {len(frames_to_process)} frames...")

        for frame_info in frames_to_process[:3]:  # Limita a 3 frames para evitar loops longos
            frame_id = frame_info['id']
            document_root = get_document_with_retries(client, frame_id, retries=3)
            
            if document_root:
                try:
                    response = client.send('DOM.querySelector', {
                        'nodeId': document_root['nodeId'],
                        'selector': selector
                    })
                    
                    if response and 'result' in response:
                        node_id = response.get('result', {}).get('nodeId')
                        if node_id:
                            result = (node_id, frame_id)
                            # Adiciona ao cache
                            _element_cache[cache_key] = result
                            _cleanup_cache()
                            print(f"✅ Seletor encontrado no frame {frame_id}")
                            return result
                            
                except Exception as e:
                    print(f"⚠️ Erro ao executar querySelector no frame {frame_id}: {e}")
                    continue

        print("❌ Seletor não encontrado em nenhum frame")
        return None, None
        
    except Exception as e:
        print(f"💥 Erro crítico na busca por seletor: {e}")
        return None, None

def find_element_by_xpath_in_frames(client, xpath_expression):
    """
    Procura por um elemento usando XPath em todos os frames da página.
    Retorna o primeiro nodeId encontrado e o frameId correspondente.
    """
    # Habilita DOM e Runtime se ainda não estiverem habilitados
    client.send('DOM.enable')
    client.send('Runtime.enable')
    
    # 1. Obter a árvore de frames
    frame_tree_res = client.send('Page.getFrameTree')
    frames = frame_tree_res.get('result', {}).get('frameTree', {}).get('childFrames', [])
    all_frames = [frame_tree_res.get('result', {}).get('frameTree', {}).get('frame')] + [f['frame'] for f in frames]

    # Depuração: listar todos os contextos de execução
    contexts_res = client.send('Runtime.getExecutionContexts')
    print("Contextos de execução disponíveis:")
    for context in contexts_res.get('result', {}).get('contexts', []):
        print(f"  contextId={context['id']} frameId={context.get('auxData', {}).get('frameId')} isDefault={context.get('isDefault', False)} name={context.get('name')}")

    # 2. Iterar sobre cada frame e procurar usando XPath
    for frame_info in all_frames:
        frame_id = frame_info['id']
        try:
            # 3. Procurar contexto de execução para o frame
            target_context_id = None
            for context in contexts_res.get('result', {}).get('contexts', []):
                if context.get('auxData', {}).get('frameId') == frame_id and context.get('isDefault', False):
                    target_context_id = context['id']
                    break
            
            # Se não encontrou contexto padrão, tenta QUALQUER contexto desse frame
            if not target_context_id:
                for context in contexts_res.get('result', {}).get('contexts', []):
                    if context.get('auxData', {}).get('frameId') == frame_id:
                        target_context_id = context['id']
                        print(f"  Usando contexto não-padrão: {context.get('name', 'unnamed')}")
                        break
            
            print(f"Tentando frameId={frame_id} contextId={target_context_id} para XPath: {xpath_expression}")
            if not target_context_id:
                print(f"  Nenhum contexto de execução encontrado para frame {frame_id}")
                continue

            # 4. Executar XPath no contexto do frame específico
            js_code = f"""
            (function() {{
                try {{
                    const result = document.evaluate(
                        `{xpath_expression}`,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    );
                    return result.singleNodeValue;
                }} catch (e) {{
                    return null;
                }}
            }})()
            """

            res = client.send('Runtime.evaluate', {
                'expression': js_code,
                'contextId': target_context_id,
                'returnByValue': False
            })

            if ('result' in res and 'objectId' in res['result'] and 
                res['result']['type'] != 'undefined' and 
                res['result']['subtype'] != 'null'):

                # Converte o elemento encontrado em nodeId
                object_id = res['result']['objectId']
                node_res = client.send('DOM.requestNode', {'objectId': object_id})

                if 'result' in node_res and 'nodeId' in node_res['result']:
                    node_id = node_res['result']['nodeId']
                    print(f"Elemento encontrado via XPath no frame: {frame_id}")
                    return node_id, frame_id

        except Exception as e:
            print(f"Erro ao procurar no frame {frame_id}: {e}")
            continue

def get_outer_html(client, node_id):
    """Retorna o outerHTML de um nó."""
    res = client.send('DOM.getOuterHTML', {'nodeId': node_id})
    return res.get('result', {}).get('outerHTML', '')

def find_textarea_elements_directly(client):
    """
    Procura elementos textarea usando apenas comandos DOM, sem JavaScript.
    Retorna uma lista de (node_id, frame_id) de todos os textareas encontrados.
    """
    client.send('DOM.enable')
    
    results = []
    
    # 1. Obter a árvore de frames
    frame_tree_res = client.send('Page.getFrameTree')
    frames = frame_tree_res.get('result', {}).get('frameTree', {}).get('childFrames', [])
    all_frames = [frame_tree_res.get('result', {}).get('frameTree', {}).get('frame')] + [f['frame'] for f in frames]
    
    # 2. Para cada frame, obter o documento e procurar textareas
    for frame_info in all_frames:
        frame_id = frame_info['id']
        try:
            print(f"Procurando em frame {frame_id} ({frame_info.get('url', 'no-url')})")
            
            # Obter documento do frame
            doc_res = client.send('DOM.getDocument', {'frameId': frame_id, 'depth': -1})
            
            if 'result' not in doc_res or 'root' not in doc_res['result']:
                print(f"  Não foi possível obter documento do frame {frame_id}")
                continue
                
            root_node = doc_res['result']['root']
            print(f"  Documento obtido, nodeId raiz: {root_node.get('nodeId')}")
            
            # Buscar por todos os elementos textarea neste documento
            textarea_nodes = find_nodes_by_tag(client, root_node['nodeId'], 'textarea')
            
            for node_id in textarea_nodes:
                results.append((node_id, frame_id))
                print(f"  TEXTAREA encontrado! nodeId: {node_id}")
                
        except Exception as e:
            print(f"  Erro ao processar frame {frame_id}: {e}")
            continue
    
    print(f"Total de textareas encontrados: {len(results)}")
    return results


def find_nodes_by_tag(client, root_node_id, tag_name):
    """
    Encontra todos os nós com uma tag específica usando busca recursiva no DOM.
    """
    found_nodes = []
    
    def search_recursive(node_id):
        try:
            # Obter informações do nó
            node_res = client.send('DOM.describeNode', {'nodeId': node_id})
            if 'result' not in node_res or 'node' not in node_res['result']:
                return
                
            node = node_res['result']['node']
            
            # Se é o tipo de nó que procuramos
            if node.get('nodeName', '').lower() == tag_name.lower():
                found_nodes.append(node_id)
            
            # Procurar nos filhos
            children = node.get('children', [])
            for child in children:
                search_recursive(child['nodeId'])
                
        except Exception:
            # Alguns nós podem não ser acessíveis
            pass
    
    search_recursive(root_node_id)
    return found_nodes


def find_first_textarea(client):
    """
    Encontra o primeiro textarea da página usando busca DOM direta.
    Retorna (node_id, frame_id) ou (None, None) se não encontrar.
    """
    textareas = find_textarea_elements_directly(client)
    if textareas:
        return textareas[0]  # Retorna o primeiro encontrado
    return None, None


def save_page_html(client, output_file="page_html_debug.html"):
    """
    Salva o HTML de todos os frames da página para análise.
    Retorna o caminho do arquivo salvo.
    """
    client.send('DOM.enable')
    client.send('Runtime.enable')
    
    # Obter a árvore de frames
    frame_tree_res = client.send('Page.getFrameTree')
    frames = frame_tree_res.get('result', {}).get('frameTree', {}).get('childFrames', [])
    all_frames = [frame_tree_res.get('result', {}).get('frameTree', {}).get('frame')] + [f['frame'] for f in frames]
    
    html_content = []
    html_content.append("<html><head><title>Debug - HTML de todos os frames</title></head><body>")
    html_content.append("<h1>HTML de todos os frames da página</h1>")
    
    # Obter contextos de execução
    contexts_res = client.send('Runtime.getExecutionContexts')
    
    for i, frame_info in enumerate(all_frames):
        frame_id = frame_info['id']
        frame_url = frame_info.get('url', 'about:blank')
        
        html_content.append(f"<hr><h2>Frame {i+1}: {frame_id}</h2>")
        html_content.append(f"<p><strong>URL:</strong> {frame_url}</p>")
        
        try:
            # Procurar contexto de execução para o frame
            target_context_id = None
            for context in contexts_res.get('result', {}).get('contexts', []):
                if context.get('auxData', {}).get('frameId') == frame_id and context.get('isDefault', False):
                    target_context_id = context['id']
                    break
            
            # Se não encontrou contexto padrão, tenta QUALQUER contexto desse frame
            if not target_context_id:
                for context in contexts_res.get('result', {}).get('contexts', []):
                    if context.get('auxData', {}).get('frameId') == frame_id:
                        target_context_id = context['id']
                        break
            
            if not target_context_id:
                html_content.append("<p><em>Nenhum contexto de execução encontrado para este frame.</em></p>")
                continue
            
            # Obter o HTML do frame
            js_code = "document.documentElement.outerHTML"
            res = client.send('Runtime.evaluate', {
                'expression': js_code,
                'contextId': target_context_id,
                'returnByValue': True
            })
            
            if 'result' in res and 'value' in res['result']:
                frame_html = res['result']['value']
                html_content.append("<div style='border:1px solid #ccc; padding:10px; margin:10px;'>")
                html_content.append("<h3>HTML do Frame:</h3>")
                html_content.append("<pre style='background:#f5f5f5; padding:10px; overflow:auto; max-height:400px;'>")
                html_content.append(frame_html.replace('<', '&lt;').replace('>', '&gt;'))
                html_content.append("</pre>")
                html_content.append("</div>")
                
                # Contar textareas neste frame
                count_js = "document.querySelectorAll('textarea').length"
                count_res = client.send('Runtime.evaluate', {
                    'expression': count_js,
                    'contextId': target_context_id,
                    'returnByValue': True
                })
                textarea_count = count_res.get('result', {}).get('value', 0)
                html_content.append(f"<p><strong>Número de textareas encontradas neste frame:</strong> {textarea_count}</p>")
                
            else:
                html_content.append("<p><em>Não foi possível obter o HTML deste frame.</em></p>")
                
        except Exception as e:
            html_content.append(f"<p><em>Erro ao processar frame: {e}</em></p>")
    
    html_content.append("</body></html>")
    
    # Salvar arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_content))
    
    print(f"HTML da página salvo em: {output_file}")
    return output_file
