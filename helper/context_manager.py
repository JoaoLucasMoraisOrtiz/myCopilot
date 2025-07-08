import os

def save_md(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

def append_to_context(context_path, content):
    with open(context_path, "a", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

def load_context(filepaths):
    context = ""
    for fp in filepaths:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                context += f.read() + "\n"
    return context
