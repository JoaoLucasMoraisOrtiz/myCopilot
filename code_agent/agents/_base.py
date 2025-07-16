# code_agent/agents/_base.py
class BaseAgent:
    def run(self, *args, **kwargs):
        raise NotImplementedError