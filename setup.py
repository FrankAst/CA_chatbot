#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import venv
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure logging settings"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"setup_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger('setup')

def run_command(command, check=True):
    """Run a command and return its output"""
    logger = logging.getLogger('setup')
    try:
        logger.debug(f"Executing command: {command}")
        result = subprocess.run(
            command,
            check=check,
            shell=True,
            text=True,
            capture_output=True
        )
        if result.stdout:
            logger.debug(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {command}")
        logger.error(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def is_venv():
    """Check if running inside a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def activate_venv(venv_dir):
    """Activate the virtual environment"""
    logger = logging.getLogger('setup')
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_dir, "Scripts", "activate.bat")
    else:
        activate_script = os.path.join(venv_dir, "bin", "activate")
    
    logger.debug(f"Activating virtual environment using: {activate_script}")
    if platform.system() == "Windows":
        os.system(f'"{activate_script}"')
    else:
        os.system(f'source "{activate_script}"')

def setup_environment():
    """Main setup function"""
    logger = logging.getLogger('setup')
    logger.info("🚀 Starting setup process...")
    
    # Determine the python executable to use
    python_exec = "python" if platform.system() == "Windows" else "python3"
    pip_exec = "pip" if platform.system() == "Windows" else "pip3"
    
    # Create virtual environment if it doesn't exist
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        logger.info("📦 Creating virtual environment...")
        try:
            venv.create(venv_dir, with_pip=True)
            logger.info("✅ Virtual environment created successfully")
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            raise
    
    # Activate virtual environment
    if not is_venv():
        logger.info("🔄 Activating virtual environment...")
        activate_venv(venv_dir)
    
    # Upgrade pip
    logger.info("⬆️ Upgrading pip...")
    run_command(f"{pip_exec} install --upgrade pip")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        logger.info("📥 Installing requirements...")
        run_command(f"{pip_exec} install -r requirements.txt")
    else:
        logger.warning("requirements.txt not found!")
    
    # Check and install PyTorch
    try:
        import torch
        logger.info("✅ PyTorch is already installed")
    except ImportError:
        logger.info("📥 Installing PyTorch...")
        pytorch_command = f"{pip_exec} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        run_command(pytorch_command)
    
    # Run initial scripts
    logger.info("🔄 Running setup scripts...")
    scripts = [
        "datasets/textorag/generador_grafo.py",
        "datasets/create_corpus_rag.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            logger.info(f"Running {script}...")
            run_command(f"{python_exec} {script}")
        else:
            logger.warning(f"⚠️ Script not found: {script}")
    
    # Handle config file
    config_dir = Path("config")
    config_file = config_dir / "cfg.py"
    
    if not config_dir.exists():
        logger.info("Creating config directory...")
        config_dir.mkdir(parents=True)
    
    if not config_file.exists():
        logger.info("📝 Config file not found. Creating new config file...")
        token = input("Please enter your Telegram BOT TOKEN: ").strip()
        try:
            with open(config_file, "w") as f:
                f.write(f'TOKEN_BOT = "{token}"\n')
            logger.info("✅ Config file created successfully")
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            raise
    else:
        logger.info("✅ Config file already exists")
    
    # Start the bot
    bot_file = "src/bot_core.py"
    if os.path.exists(bot_file):
        logger.info("🤖 Starting the bot...")
        run_command(f"{python_exec} {bot_file}")
    else:
        logger.error(f"❌ Bot file {bot_file} not found")
        raise FileNotFoundError(f"Bot file {bot_file} not found")

if __name__ == "__main__":
    logger = setup_logging()
    try:
        setup_environment()
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ An error occurred during setup: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        sys.exit(1)
