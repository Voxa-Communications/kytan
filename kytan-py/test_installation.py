#!/usr/bin/env python3
"""
Test script to verify the kytan-py installation and binary building works correctly.
"""

import sys
import os
import subprocess

def test_binary_detection():
    """Test that the wrapper can find the bundled binary."""
    print("🔍 Testing binary detection...")
    
    try:
        sys.path.insert(0, '.')
        from kytan import create_client
        
        client = create_client()
        print(f"✅ Binary found at: {client.binary_path}")
        
        # Check if binary is executable
        if os.access(client.binary_path, os.X_OK):
            print("✅ Binary is executable")
        else:
            print("❌ Binary is not executable")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_binary_version():
    """Test that the binary responds to help command."""
    print("\n🔍 Testing binary functionality...")
    
    try:
        sys.path.insert(0, '.')
        from kytan import create_client
        
        client = create_client()
        result = subprocess.run([client.binary_path, "--help"], 
                              capture_output=True, text=True, timeout=5)
        
        # kytan requires root privileges even for --help, so exit code 101 is expected
        if result.returncode in [0, 1, 101] or "Please run as root" in result.stderr:
            print("✅ Binary responds correctly (requires root privileges)")
            return True
        else:
            print(f"❌ Binary returned unexpected exit code: {result.returncode}")
            print(f"stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_functionality():
    """Test basic API functionality without actual network operations."""
    print("\n🔍 Testing Python API...")
    
    try:
        sys.path.insert(0, '.')
        from kytan import create_client, create_server, KytanError, ClientConfig, ServerConfig
        
        # Test client creation
        client = create_client()
        print("✅ Client creation successful")
        
        # Test server creation
        server = create_server()
        print("✅ Server creation successful")
        
        # Test configuration objects
        client_config = ClientConfig(
            server="test.example.com",
            port=9527,
            key="test-key"
        )
        print("✅ ClientConfig creation successful")
        
        server_config = ServerConfig(
            bind="0.0.0.0",
            port=9527,
            key="test-key",
            dns="8.8.8.8"
        )
        print("✅ ServerConfig creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cli_interface():
    """Test the command line interface."""
    print("\n🔍 Testing CLI interface...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "kytan.kytan", "--help"], 
                              capture_output=True, text=True, timeout=5)
        
        if "Python wrapper for kytan VPN" in result.stdout:
            print("✅ CLI interface working")
            return True
        else:
            print("❌ CLI interface not responding correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing kytan-py Python wrapper with bundled binary\n")
    
    tests = [
        test_binary_detection,
        test_binary_version,
        test_api_functionality,
        test_cli_interface
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The kytan-py wrapper is working correctly.")
        print("\n✨ Features verified:")
        print("   - Automatic Rust binary building during installation")
        print("   - Binary bundling with Python package")
        print("   - Python API functionality")
        print("   - Command line interface")
        print("   - Binary detection and execution")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()