"""
TMP AI Sales Outreach Agent - Main Entry Point

Run the Gradio UI:
    python main.py

Run the API server:
    python main.py --api

Run with custom port:
    python main.py --port 8080
"""

# Load environment variables FIRST, before any other imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

import argparse
import sys

# Add project root to path
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="TMP AI Sales Outreach Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                 # Launch Gradio UI
  python main.py --api           # Launch FastAPI server
  python main.py --port 8080     # Custom port
  python main.py --share         # Create public Gradio link
        """
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run FastAPI server instead of Gradio UI"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public Gradio share link"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (API mode only)"
    )
    
    args = parser.parse_args()
    
    if args.api:
        # Run FastAPI server
        import uvicorn
        from app.api import api
        from config.settings import settings
        
        port = args.port or 8000
        print(f"🚀 Starting API server on http://localhost:{port}")
        print(f"📚 API docs available at http://localhost:{port}/docs")
        
        uvicorn.run(
            "app.api:api",
            host="0.0.0.0",
            port=port,
            reload=args.reload,
        )
    else:
        # Run Gradio UI
        from app.gradio_app import create_gradio_app
        from config.settings import settings
        
        port = args.port or settings.gradio_server_port
        
        print(f"🚀 Starting Gradio UI on http://localhost:{port}")
        
        demo = create_gradio_app()
        demo.launch(
            server_port=port,
            share=args.share or settings.gradio_share,
        )


if __name__ == "__main__":
    main()
