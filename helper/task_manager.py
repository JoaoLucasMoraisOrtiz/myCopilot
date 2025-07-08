import os
import json
from helper.context_manager import load_context, save_md
from helper.code_parser import extract_code_blocks, save_code_to_file

class TaskManager:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.backlog_file = os.path.join(output_dir, "migration-backlog.md")
        self.tasks_file = os.path.join(output_dir, "tasks_status.json")
        
    def load_tasks(self):
        """Carrega tasks do backlog."""
        if not os.path.exists(self.backlog_file):
            return []
        
        with open(self.backlog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse simples das tasks - você pode melhorar isso
        tasks = []
        lines = content.split('\n')
        current_task = None
        
        for line in lines:
            if line.startswith('## ') or line.startswith('### '):
                if current_task:
                    tasks.append(current_task)
                current_task = {
                    'title': line.strip('# '),
                    'description': '',
                    'status': 'pending'
                }
            elif current_task and line.strip():
                current_task['description'] += line + '\n'
        
        if current_task:
            tasks.append(current_task)
            
        return tasks
    
    def get_next_task(self):
        """Retorna a próxima task pendente."""
        tasks = self.load_tasks()
        status = self._load_status()
        
        for i, task in enumerate(tasks):
            if status.get(str(i), 'pending') == 'pending':
                return i, task
        
        return None, None
    
    def mark_task_completed(self, task_index):
        """Marca uma task como completa."""
        status = self._load_status()
        status[str(task_index)] = 'completed'
        self._save_status(status)
    
    def _load_status(self):
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_status(self, status):
        with open(self.tasks_file, 'w') as f:
            json.dump(status, f, indent=2)
