"""
AcademicOmniSearch - Servidor Unificado
Inicia a API FastAPI e serve a interface web moderna (React + Tailwind Resend Design).
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def check_and_build_frontend():
    dist_path = Path(__file__).parent / "frontend" / "dist"
    frontend_path = Path(__file__).parent / "frontend"

    if not dist_path.exists() and frontend_path.exists():
        print("\n⚡ [AcademicOmniSearch] Primeira execução detectada: compilando interface frontend...")
        try:
            # Garante dependências instaladas
            if not (frontend_path / "node_modules").exists():
                print("📦 Instalando dependências do frontend (npm install)...")
                subprocess.run(["npm", "install"], cwd=str(frontend_path), shell=True, check=True)

            print("🔨 Gerando build de produção otimizado (npm run build)...")
            subprocess.run(["npm", "run", "build"], cwd=str(frontend_path), shell=True, check=True)
            print("✅ Frontend compilado com sucesso!\n")
        except Exception as e:
            print(f"⚠️ Aviso ao compilar frontend automaticamente: {e}")
            print("Você também pode rodar 'cd frontend && npm run dev' para hot-reload.\n")

def main():
    check_and_build_frontend()

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    banner = f"""
===================================================================
⚡ ACADEMIC OMNISEARCH — Modern Harvester & Bibliometrics v2.0
   Design System Resend (Dark OLED, Craft-Driven)
===================================================================
🚀 Servidor Web & API ativo em:   http://{host}:{port}
📚 Documentação Interativa (Swagger): http://{host}:{port}/docs
💻 Modo Desenvolvedor Frontend:   cd frontend && npm run dev
===================================================================
    """
    print(banner)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()

