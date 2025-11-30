"""
BGE-M3 Embedding Model Downloader

This script downloads the BGE-M3 model from HuggingFace
and saves it locally for offline usage.
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    import torch
except ImportError:
    print("❌ Missing dependencies. Please install requirements first:")
    print("   pip install sentence-transformers rich torch")
    sys.exit(1)

console = Console()

# Model configuration
MODEL_NAME = "BAAI/bge-m3"
MODEL_PATH = Path(__file__).parent / "bge-m3"


def check_gpu_availability() -> bool:
    """Check if CUDA GPU is available."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        console.print(f"✅ GPU detected: [green]{gpu_name}[/green]")
        return True
    else:
        console.print("⚠️  No GPU detected. Model will use CPU (slower).")
        return False


def calculate_dir_hash(directory: Path) -> str:
    """Calculate hash of all files in directory for verification."""
    hasher = hashlib.sha256()
    
    for filepath in sorted(directory.rglob("*")):
        if filepath.is_file():
            with open(filepath, "rb") as f:
                hasher.update(f.read())
    
    return hasher.hexdigest()


def download_model() -> bool:
    """Download BGE-M3 model from HuggingFace."""
    try:
        console.print(f"\n🔽 Downloading BGE-M3 model from HuggingFace...")
        console.print(f"   Source: [cyan]{MODEL_NAME}[/cyan]")
        console.print(f"   Destination: [cyan]{MODEL_PATH}[/cyan]\n")
        
        # Create model directory if it doesn't exist
        MODEL_PATH.mkdir(parents=True, exist_ok=True)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading model...", total=None)
            
            # Download model
            model = SentenceTransformer(MODEL_NAME)
            
            progress.update(task, description="Saving model locally...")
            
            # Save to local path
            model.save(str(MODEL_PATH))
            
            progress.update(task, description="✅ Download complete!", completed=True)
        
        console.print(f"\n✅ Model successfully downloaded to: [green]{MODEL_PATH}[/green]")
        return True
        
    except Exception as e:
        console.print(f"\n❌ Error downloading model: [red]{str(e)}[/red]")
        return False


def verify_model() -> bool:
    """Verify the downloaded model works correctly."""
    try:
        console.print("\n🔍 Verifying model...")
        
        # Load model
        model = SentenceTransformer(str(MODEL_PATH))
        
        # Test embedding generation
        test_text = "This is a test sentence for BGE-M3 embedding model."
        embedding = model.encode(test_text)
        
        console.print(f"   ✅ Model loaded successfully")
        console.print(f"   ✅ Embedding dimension: [cyan]{len(embedding)}[/cyan]")
        console.print(f"   ✅ Model is ready to use!")
        
        return True
        
    except Exception as e:
        console.print(f"\n❌ Model verification failed: [red]{str(e)}[/red]")
        return False


def main():
    """Main execution function."""
    console.print("\n" + "="*60)
    console.print("  BGE-M3 Embedding Model Downloader")
    console.print("="*60 + "\n")
    
    # Check if model already exists
    if MODEL_PATH.exists() and any(MODEL_PATH.iterdir()):
        console.print(f"⚠️  Model directory already exists: [yellow]{MODEL_PATH}[/yellow]")
        response = input("\nDo you want to re-download? (y/N): ").strip().lower()
        
        if response != 'y':
            console.print("\n✅ Using existing model. Verifying...")
            if verify_model():
                console.print("\n✨ Model is ready! You can now run the Vibe Agent.\n")
                return 0
            else:
                console.print("\n❌ Existing model is corrupted. Please re-download.\n")
                return 1
    
    # Check GPU
    has_gpu = check_gpu_availability()
    
    # Download model
    if not download_model():
        return 1
    
    # Verify model
    if not verify_model():
        return 1
    
    console.print("\n" + "="*60)
    console.print("  ✨ Setup Complete!")
    console.print("="*60)
    console.print("\nNext steps:")
    console.print("  1. Configure your .env file")
    console.print("  2. Start the backend: cd backend && uvicorn src.app.main:app --reload")
    console.print("  3. Start the frontend: cd frontend && npm run dev")
    console.print("\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
