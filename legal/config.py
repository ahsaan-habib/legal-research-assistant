import os


def env(name: str, default: str) -> str:
    return os.environ.get(f"LEGAL_{name}", default)


OLLAMA_URL = env("OLLAMA_URL", "http://localhost:11434")
MODEL = env("MODEL", "qwen3:4b-instruct")
EMBED_MODEL = env("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
INDEX_DIR = env("INDEX_DIR", ".chroma")
CORPUS = env("CORPUS", "corpus")
