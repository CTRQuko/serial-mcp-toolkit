from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from uart_mcp.server import DOCS_DIR, SERVER_DIR, ROOT_DIR

print("SERVER_DIR:", SERVER_DIR)
print("ROOT_DIR:", ROOT_DIR)
print("DOCS_DIR:", DOCS_DIR)
print("EXISTS:", DOCS_DIR.exists())
