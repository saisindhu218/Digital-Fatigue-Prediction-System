#!/usr/bin/env python3
"""
Backend setup script
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_venv():
    """Setup Python virtual environment"""
    print("Setting up Python virtual environment...")
    
    if not Path("venv").exists():
        result = subprocess.run([sys.executable, "-m", "venv", "venv"])
        if result.returncode != 0:
            print("❌ Failed to create virtual environment")
            return False
    
    print("✅ Virtual environment created")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    
    if sys.platform == "win32":
        pip = "venv\\Scripts\\pip"
    else:
        pip = "venv/bin/pip"
    
    # Upgrade pip
    subprocess.run([pip, "install", "--upgrade", "pip"])
    
    # Install requirements
    result = subprocess.run([pip, "install", "-r", "requirements.txt"])
    
    if result.returncode == 0:
        print("✅ Dependencies installed")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file from template")
        print("   Please edit .env with your configuration")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env.example found")
    
    return True

def check_ml_models():
    """Check if ML models exist"""
    models_dir = Path("ml_models")
    required = [
        "fatigue_classifier.pkl",
        "fatigue_label_encoder.pkl",
        "productivity_loss_model.pkl"
    ]
    
    if not models_dir.exists():
        print("❌ ml_models directory not found")
        return False
    
    missing = []
    for model in required:
        if not (models_dir / model).exists():
            missing.append(model)
    
    if missing:
        print("⚠️  Missing ML models:")
        for model in missing:
            print(f"   - {model}")
        print("\n   Train models with:")
        print("   cd ../data_science")
        print("   python train_models.py")
        return False
    
    print("✅ All ML models found")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("   Backend Setup")
    print("=" * 60)
    
    steps = [
        ("Virtual Environment", setup_venv),
        ("Dependencies", install_dependencies),
        ("Configuration", create_env_file),
        ("ML Models", check_ml_models),
    ]
    
    all_ok = True
    for name, func in steps:
        print(f"\n{name}...")
        if not func():
            all_ok = False
    
    if all_ok:
        print("\n" + "=" * 60)
        print("✅ Backend setup complete!")
        print("\nTo run the backend:")
        print("   python run.py")
        print("\nAPI will be available at: http://localhost:8000")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  Backend setup incomplete")
        print("Please fix the issues above")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()