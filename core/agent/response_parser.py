import re
import json
from typing import Dict, Optional, Tuple

class AgentResponseParser:
    """
    Parses the full LLM response to extract
    the working memory (world_state) and the action (JSON).
    """

    def parse(self, response_text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Parses the LLM's response.

        Returns:
            A tuple containing (world_state, action_json).
            Returns (None, None) if parsing fails.
        """
        try:
            world_state = self._extract_section(response_text, "State Update")
            action_str = self._extract_section(response_text, "Action")
            
            if not action_str:
                return world_state, None

            json_match = re.search(r'\{.*\}', action_str, re.DOTALL)
            if json_match:
                action_json = json.loads(json_match.group(0))
                return world_state, action_json

            return world_state, None

        except Exception as e:
            print(f"🚨 Error parsing LLM response: {e}")
            print(f"Received response:\n{response_text}")
            return None, None

    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extracts content from a specific section (e.g., **Action:**)."""
        pattern = re.compile(rf'\*\*{section_name}:\*\*\s*(.*?)(?=\s*\*\*|$)', re.DOTALL)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return None
