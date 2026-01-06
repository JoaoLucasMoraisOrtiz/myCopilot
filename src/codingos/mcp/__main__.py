from __future__ import annotations

import os

from codingos.mcp.supervisor import create_mcp_server


def main() -> None:
    repo_root = os.getcwd()
    memory_path = os.path.join(repo_root, ".gemini", "ace_memory.json")
    mcp = create_mcp_server(repo_root=repo_root, memory_path=memory_path)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
