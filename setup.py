#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure logging settings"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"setup_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger('setup')

def run_command(command):
    """Run a command and return its output"""
    logger = logging.getLogger('setup')
    try:
        logger.debug(f"Executing command: {command}")
        result = subprocess.run(
            command,
            check=True,
            shell=True,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        if result.stdout:
            logger.debug(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {command}")
        logger.error(f"Error output: {e.stderr}")
        raise

def check_system_requirements():
    """Check if system has required packages"""
    logger = logging.getLogger('setup')
    
    # Check Python version
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        raise SystemError("Python 3.6 or higher is required")
    
    # Check if pip is installed in system Python
    try:
        run_command(f"{sys.executable} -m pip --version")
    except subprocess.CalledProcessError:
        logger.error("pip is not installed in your system Python.")
        logger.info("Please install pip first using:")
        if platform.system() == "Windows":
            logger.info("python -m ensurepip --default-pip")
        else:
            logger.info("sudo apt-get update && sudo apt-get install python3-pip")
        sys.exit(1)

def setup_environment():
    """Main setup function"""
    logger = logging.getLogger('setup')
    logger.info("\U0001F680 Starting setup process...")
    
    # Check system requirements first
    check_system_requirements()
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        logger.info("\U0001F4E5 Installing requirements (excluding torch)...")
        with open("requirements.txt", "r", encoding="utf-8") as f:
            requirements = [line.strip() for line in f if not line.lower().startswith("torch")]
        for requirement in requirements:
            run_command(f'{sys.executable} -m pip install {requirement}')
        logger.warning("\u26A0\uFE0F PyTorch is excluded from the installation. Please install the correct version manually based on your system and GPU setup.")
    else:
        logger.warning("\u26A0\uFE0F requirements.txt file is missing. Ensure it is included for proper setup.")
    
    # Download SpaCy model
    logger.info("\U0001F527 Downloading SpaCy model es_core_news_sm...")
    try:
        run_command(f"{sys.executable} -m spacy download es_core_news_sm")
        logger.info("\u2705 SpaCy model es_core_news_sm downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download SpaCy model: {e}")
        raise
    
    # Run initial scripts
    logger.info("\U0001F504 Running setup scripts...")
    scripts = [
        "datasets/textorag/generador_grafo.py",
        "datasets/create_corpus_rag.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            logger.info(f"Running {script}...")
            run_command(f'{sys.executable} {script}')
        else:
            logger.warning(f"\u26A0\uFE0F Script not found: {script}")
    
    # Handle config file
    config_dir = Path("config")
    config_file = config_dir / "cfg.py"
    
    if not config_dir.exists():
        logger.info("Creating config directory...")
        config_dir.mkdir(parents=True)
    
    if not config_file.exists():
        logger.info("\U0001F4DD Config file not found. Creating new config file...")
        token = input("Please enter your Telegram BOT TOKEN: ").strip()
        try:
            with open(config_file, "w", encoding='utf-8') as f:
                f.write(f'TOKEN_BOT = "{token}"')
                
            logger.info("\u2705 Config file created successfully")
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            raise
    else:
        logger.info("\u2705 Config file already exists")
    logger.info("Setup completado, para correr el bot ejecute: cd src y luego python3 bot_core.py")

if __name__ == "__main__":
    logger = setup_logging()
    try:
        setup_environment()
    except KeyboardInterrupt:
        logger.warning("\n\u26A0\uFE0F Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\u274C An error occurred during setup: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        sys.exit(1)
