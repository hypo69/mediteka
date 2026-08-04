#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simple SSL Certificate Generator
# =============================================================================
# Description:
#   Creates self-signed SSL certificates for HTTPS
#
# File: generate-ssl.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: December 9, 2025
# =============================================================================

import os
import subprocess
from pathlib import Path

def generate_ssl_certificates():
    """Generates SSL certificates using openssl"""
    
    ssl_dir = Path.home() / ".ssl"
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    print(f"🔐 Creating SSL certificates in {ssl_dir}")
    
    # openssl command
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", "365", "-nodes",
        "-subj", "/C=US/ST=State/L=City/O=FastAPI-Foundry/CN=localhost"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ SSL certificates created:")
            print(f"   Certificate: {cert_file}")
            print(f"   Key: {key_file}")
            print(f"   Validity: 365 days")
            print()
            print("🚀 Now you can run the server with HTTPS support")
            return True
        else:
            print(f"❌ OpenSSL error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL not found!")
        print("💡 Install OpenSSL:")
        print("   Windows: https://slproweb.com/products/Win32OpenSSL.html")
        print("   or use: winget install OpenSSL.Light")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 SSL Certificate Generator for FastAPI Foundry")
    print("=" * 50)
    generate_ssl_certificates()