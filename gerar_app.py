"""Gera docs/index.html (aplicação web) embutindo os pesos exportados em docs/modelo.json."""
import json
from pathlib import Path

modelo = Path("docs/modelo.json").read_text(encoding="utf-8")
json.loads(modelo)  # valida
html = Path("app/template.html").read_text(encoding="utf-8").replace("/*__MODELO__*/null", modelo)
Path("docs/index.html").write_text(html, encoding="utf-8")
print(f"docs/index.html gerado ({len(html)/1024:.0f} KB)")
