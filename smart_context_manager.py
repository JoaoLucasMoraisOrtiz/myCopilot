"""
Sistema de Contexto Inteligente tipo RAG para otimizar o contexto das tasks
Reduz drasticamente o tamanho do contexto mantendo apenas informações relevantes
"""

import os
import re
import json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from datetime import datetime

class SmartContextManager:
    def __init__(self, output_dir: str, max_context_size: int = 8000):
        self.output_dir = output_dir
        self.max_context_size = max_context_size
        self.knowledge_base = {}
        self.context_cache = {}
        
        # Carrega base de conhecimento existente
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Carrega a base de conhecimento de um arquivo JSON"""
        kb_file = os.path.join(self.output_dir, "knowledge_base.json")
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                print(f"📚 Base de conhecimento carregada: {len(self.knowledge_base)} entradas")
            except Exception as e:
                print(f"⚠️ Erro ao carregar base de conhecimento: {e}")
                self.knowledge_base = {}
        else:
            self.knowledge_base = {}
    
    def save_knowledge_base(self):
        """Salva a base de conhecimento em um arquivo JSON"""
        kb_file = os.path.join(self.output_dir, "knowledge_base.json")
        try:
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
            print(f"💾 Base de conhecimento salva: {len(self.knowledge_base)} entradas")
        except Exception as e:
            print(f"❌ Erro ao salvar base de conhecimento: {e}")
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave relevantes do texto"""
        # Remove caracteres especiais e converte para minúsculas
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filtra palavras irrelevantes
        stop_words = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos',
            'para', 'por', 'com', 'em', 'no', 'na', 'nos', 'nas', 'se', 'que', 'como', 'quando',
            'onde', 'porque', 'mais', 'menos', 'muito', 'pouco', 'bem', 'mal', 'já', 'ainda',
            'também', 'só', 'apenas', 'sim', 'não', 'ser', 'estar', 'ter', 'fazer', 'ir', 'vir',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Filtra palavras relevantes (pelo menos 3 caracteres, não são stop words)
        keywords = [word for word in words 
                   if len(word) >= 3 and word not in stop_words]
        
        # Remove duplicatas mantendo ordem
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)
        
        return unique_keywords[:20]  # Máximo 20 palavras-chave
    
    def index_document(self, doc_id: str, content: str, doc_type: str = "general"):
        """Indexa um documento na base de conhecimento"""
        keywords = self.extract_keywords(content)
        
        # Cria resumo do documento (primeiras 500 caracteres)
        summary = content[:500] + "..." if len(content) > 500 else content
        
        # Identifica seções importantes
        sections = self.extract_sections(content)
        
        self.knowledge_base[doc_id] = {
            'content': content,
            'summary': summary,
            'keywords': keywords,
            'doc_type': doc_type,
            'sections': sections,
            'indexed_at': datetime.now().isoformat(),
            'size': len(content)
        }
        
        print(f"📚 Documento indexado: {doc_id} ({len(content)} chars, {len(keywords)} keywords)")
    
    def extract_sections(self, content: str) -> Dict[str, str]:
        """Extrai seções importantes do documento"""
        sections = {}
        
        # Busca por títulos markdown
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Salva seção anterior
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Inicia nova seção
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Salva última seção
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def search_relevant_docs(self, query: str, max_results: int = 5) -> List[Tuple[str, float, str]]:
        """Busca documentos relevantes para uma query"""
        query_keywords = set(self.extract_keywords(query))
        results = []
        
        for doc_id, doc_data in self.knowledge_base.items():
            doc_keywords = set(doc_data.get('keywords', []))
            
            # Calcula relevância baseada na interseção de palavras-chave
            intersection = query_keywords.intersection(doc_keywords)
            union = query_keywords.union(doc_keywords)
            
            if union:
                relevance_score = len(intersection) / len(union)
                
                # Bonus para tipos específicos de documento
                if 'architecture' in doc_id:
                    relevance_score *= 1.2
                elif 'business' in doc_id:
                    relevance_score *= 1.1
                elif 'dependencies' in doc_id:
                    relevance_score *= 1.1
                
                if relevance_score > 0:
                    results.append((doc_id, relevance_score, doc_data.get('summary', '')))
        
        # Ordena por relevância
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def build_smart_context_for_task(self, task_description: str, task_type: str = "implementation") -> str:
        """Constrói contexto inteligente para uma task específica"""
        print(f"🧠 Construindo contexto inteligente para: {task_type}")
        
        # Busca documentos relevantes
        relevant_docs = self.search_relevant_docs(task_description, max_results=3)
        
        context_parts = []
        current_size = 0
        
        # Adiciona configuração da migração (sempre importante)
        migration_config = self.get_migration_config_summary()
        if migration_config:
            context_parts.append(f"# CONFIGURAÇÃO DA MIGRAÇÃO\n{migration_config}")
            current_size += len(migration_config)
        
        # Adiciona documentos relevantes
        if relevant_docs:
            context_parts.append("# CONTEXTO RELEVANTE")
            
            for doc_id, relevance, summary in relevant_docs:
                if current_size + len(summary) > self.max_context_size * 0.8:
                    break
                
                doc_data = self.knowledge_base.get(doc_id, {})
                
                # Usa resumo ou seção específica baseada no tipo de task
                if task_type == "implementation":
                    content = self.get_implementation_relevant_content(doc_data, task_description)
                elif task_type == "validation":
                    content = self.get_validation_relevant_content(doc_data, task_description)
                else:
                    content = summary
                
                context_parts.append(f"## {doc_id} (Relevância: {relevance:.2f})\n{content}")
                current_size += len(content)
        
        # Adiciona contexto técnico essencial
        tech_context = self.get_technical_essentials()
        if tech_context and current_size + len(tech_context) < self.max_context_size:
            context_parts.append(f"# ESSENCIAIS TÉCNICOS\n{tech_context}")
        
        final_context = "\n\n".join(context_parts)
        
        # Limita tamanho total
        if len(final_context) > self.max_context_size:
            final_context = final_context[:self.max_context_size] + "\n\n[...contexto truncado para otimização]"
        
        print(f"✅ Contexto otimizado: {len(final_context)} chars (redução de ~{((56942 - len(final_context)) / 56942 * 100):.1f}%)")
        return final_context
    
    def get_migration_config_summary(self) -> str:
        """Obtém resumo da configuração de migração"""
        config_file = os.path.join(self.output_dir, "migration_configuration.md")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extrai apenas as partes mais importantes
                lines = content.split('\n')
                important_lines = []
                in_important_section = False
                
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['tecnologia', 'framework', 'arquitetura', 'requisitos']):
                        in_important_section = True
                    elif line.startswith('#') and in_important_section:
                        in_important_section = False
                    
                    if in_important_section or any(keyword in line.lower() for keyword in ['target', 'fonte', 'objetivo']):
                        important_lines.append(line)
                
                summary = '\n'.join(important_lines[:20])  # Máximo 20 linhas
                return summary if len(summary) > 50 else content[:800]
                
            except Exception as e:
                print(f"⚠️ Erro ao ler configuração: {e}")
        
        return ""
    
    def get_implementation_relevant_content(self, doc_data: Dict, task_description: str) -> str:
        """Extrai conteúdo relevante para implementação"""
        sections = doc_data.get('sections', {})
        
        # Busca seções relevantes para implementação
        relevant_sections = []
        task_keywords = set(self.extract_keywords(task_description))
        
        for section_name, section_content in sections.items():
            section_keywords = set(self.extract_keywords(section_content))
            intersection = task_keywords.intersection(section_keywords)
            
            if intersection or any(keyword in section_name.lower() for keyword in ['arquitetura', 'componente', 'estrutura', 'implementação']):
                relevant_sections.append(f"### {section_name}\n{section_content[:400]}...")
        
        if relevant_sections:
            return '\n\n'.join(relevant_sections[:2])  # Máximo 2 seções
        else:
            return doc_data.get('summary', '')
    
    def get_validation_relevant_content(self, doc_data: Dict, task_description: str) -> str:
        """Extrai conteúdo relevante para validação"""
        sections = doc_data.get('sections', {})
        
        # Busca seções relevantes para validação
        for section_name, section_content in sections.items():
            if any(keyword in section_name.lower() for keyword in ['teste', 'validação', 'qualidade', 'padrão']):
                return f"### {section_name}\n{section_content[:500]}..."
        
        return doc_data.get('summary', '')
    
    def get_technical_essentials(self) -> str:
        """Retorna informações técnicas essenciais compactas"""
        essentials = []
        
        # Busca informações sobre tecnologias detectadas
        for doc_id, doc_data in self.knowledge_base.items():
            if 'dependencies' in doc_id or 'architecture' in doc_id:
                sections = doc_data.get('sections', {})
                for section_name, content in sections.items():
                    if any(keyword in section_name.lower() for keyword in ['tecnologia', 'framework', 'dependência']):
                        essentials.append(f"**{section_name}**: {content[:200]}...")
                        break
        
        return '\n'.join(essentials[:3])  # Máximo 3 essenciais
    
    def update_from_files(self, context_files: List[str]):
        """Atualiza a base de conhecimento com arquivos do contexto"""
        print("📚 Atualizando base de conhecimento...")
        
        for filename in context_files:
            file_path = os.path.join(self.output_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Determina tipo do documento
                    if 'architecture' in filename:
                        doc_type = 'architecture'
                    elif 'business' in filename:
                        doc_type = 'business'
                    elif 'dependencies' in filename:
                        doc_type = 'dependencies'
                    elif 'roadmap' in filename:
                        doc_type = 'roadmap'
                    elif 'backlog' in filename:
                        doc_type = 'backlog'
                    else:
                        doc_type = 'general'
                    
                    self.index_document(filename, content, doc_type)
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar {filename}: {e}")
        
        self.save_knowledge_base()
    
    def get_context_stats(self) -> Dict:
        """Retorna estatísticas da base de conhecimento"""
        total_docs = len(self.knowledge_base)
        total_size = sum(doc.get('size', 0) for doc in self.knowledge_base.values())
        
        doc_types = defaultdict(int)
        for doc in self.knowledge_base.values():
            doc_types[doc.get('doc_type', 'unknown')] += 1
        
        return {
            'total_documents': total_docs,
            'total_size': total_size,
            'average_size': total_size // max(total_docs, 1),
            'document_types': dict(doc_types)
        }
