"""
Setup script for Smart Attendance System
Run this after installation to configure the system
"""
import os
import sys
from pathlib import Path
import getpass

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    dirs = [
        'data',
        'data/known_faces',
        'data/backups',
        'logs',
        'assets'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"  ✓ Created: {dir_path}")


def create_env_file():
    """Create .env file from .env.example"""
    print("\n🔧 Setting up environment configuration...")
    
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_file.exists():
        response = input("  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("  ⊘ Skipped .env creation")
            return
    
    if not env_example.exists():
        print("  ⚠ .env.example not found!")
        return
    
    # Copy example file
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("  ✓ Created .env file")


def generate_secret_key():
    """Generate a secure secret key"""
    import secrets
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        print("  ⚠ bcrypt not installed. Please install it first.")
        return ""


def setup_admin_credentials():
    """Set up admin credentials"""
    print("\n🔐 Setting up admin credentials...")
    
    username = input("  Enter admin username (default: admin): ").strip() or "admin"
    
    while True:
        password = getpass.getpass("  Enter admin password: ")
        confirm = getpass.getpass("  Confirm password: ")
        
        if password == confirm:
            if len(password) < 6:
                print("  ⚠ Password too short. Use at least 6 characters.")
                continue
            break
        else:
            print("  ⚠ Passwords don't match. Try again.")
    
    password_hash = hash_password(password)
    
    if not password_hash:
        return
    
    # Update .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        with open(env_file, 'w') as f:
            for line in lines:
                if line.startswith('ADMIN_USERNAME='):
                    f.write(f'ADMIN_USERNAME={username}\n')
                elif line.startswith('ADMIN_PASSWORD_HASH='):
                    f.write(f'ADMIN_PASSWORD_HASH={password_hash}\n')
                elif line.startswith('SECRET_KEY='):
                    secret_key = generate_secret_key()
                    f.write(f'SECRET_KEY={secret_key}\n')
                else:
                    f.write(line)
        
        print(f"  ✓ Admin credentials configured")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")


def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required = [
        'streamlit',
        'opencv-python',
        'face_recognition',
        'numpy',
        'pandas',
        'bcrypt',
        'plotly',
        'pyttsx3',
        'pygame'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n  ⚠ Missing packages: {', '.join(missing)}")
        print(f"  Run: pip install {' '.join(missing)}")
        return False
    
    print("\n  ✓ All dependencies installed")
    return True


def create_sample_audio():
    """Create a simple notification sound"""
    print("\n🔊 Creating sample notification sound...")
    
    assets_dir = Path('assets')
    chime_path = assets_dir / 'chime.mp3'
    
    if chime_path.exists():
        print("  ⊘ chime.mp3 already exists")
        return
    
    try:
        import pygame
        import numpy as np
        from scipy.io import wavfile
        
        # Generate simple beep
        sample_rate = 44100
        duration = 0.3
        frequency = 1000
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Fade in/out
        fade_samples = int(sample_rate * 0.05)
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # Convert to 16-bit
        audio = (audio * 32767).astype(np.int16)
        
        # Save as WAV (pygame can load this)
        wav_path = assets_dir / 'chime.wav'
        wavfile.write(str(wav_path), sample_rate, audio)
        
        print(f"  ✓ Created notification sound (WAV)")
        print(f"  Note: Update CHIME_PATH in config.py to use chime.wav")
        
    except ImportError:
        print("  ⊘ Skipped audio generation (scipy not available)")
        print("  You can add your own chime.mp3 to the assets folder")


def main():
    """Main setup function"""
    print("=" * 60)
    print("  Smart Attendance System - Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"\n✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Run setup steps
    create_directories()
    
    if not check_dependencies():
        print("\n⚠ Please install missing dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    create_env_file()
    setup_admin_credentials()
    create_sample_audio()
    
    print("\n" + "=" * 60)
    print("  ✓ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review .env file and adjust settings if needed")
    print("  2. Run the application:")
    print("     streamlit run app.py")
    print("  3. Login with your admin credentials")
    print("  4. Register faces and start tracking attendance")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⊘ Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
