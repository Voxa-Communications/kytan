#!/usr/bin/env python3
"""
Example usage of kytan-py Python wrapper

This script demonstrates how to use the kytan Python wrapper
for both client and server operations.
"""

import time
import logging
import sys
import signal
from kytan import create_client, create_server, KytanError, KytanContextManager


def client_example():
    """Example of using kytan as a VPN client"""
    print("=== kytan Client Example ===")
    
    try:
        # Create client instance
        client = create_client()
        
        # Connect to server
        print("Connecting to VPN server...")
        client.connect(
            server="127.0.0.1",  # Replace with your server
            port=9527,
            key="example-key",
            no_default_route=False,
            log_level="info"
        )
        
        print("Connected successfully!")
        
        # Monitor connection for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            status = client.get_status()
            if not status["running"]:
                print("Connection lost!")
                break
            
            print(f"Status: Connected (PID: {status['pid']})")
            time.sleep(5)
        
        print("Disconnecting...")
        client.disconnect()
        print("Disconnected.")
        
    except KytanError as e:
        print(f"VPN Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def server_example():
    """Example of using kytan as a VPN server"""
    print("=== kytan Server Example ===")
    
    try:
        # Create server instance
        server = create_server()
        
        # Start server
        print("Starting VPN server...")
        server.serve(
            port=9527,
            key="example-key",
            bind="0.0.0.0",
            dns="8.8.8.8",
            log_level="info"
        )
        
        print("Server started on port 9527")
        print("Press Ctrl+C to stop server...")
        
        # Keep server running until interrupted
        try:
            while server.get_status()["running"]:
                status = server.get_status()
                print(f"Server running (PID: {status['pid']})")
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        
        server.shutdown()
        print("Server stopped.")
        
    except KytanError as e:
        print(f"VPN Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def context_manager_example():
    """Example using context manager for automatic cleanup"""
    print("=== Context Manager Example ===")
    
    try:
        # Using context manager ensures automatic cleanup
        with KytanContextManager(create_client()) as client:
            print("Connecting with context manager...")
            client.connect(
                server="127.0.0.1",
                port=9527,
                key="example-key",
                log_level="info"
            )
            
            print("Connected! Working for 10 seconds...")
            time.sleep(10)
            
            # Client will automatically disconnect when exiting context
            print("Exiting context - client will auto-disconnect")
        
        print("Context exited - client disconnected automatically")
        
    except KytanError as e:
        print(f"VPN Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    """Main example runner"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python example.py [client|server|context]")
        print("  client  - Run client example")
        print("  server  - Run server example") 
        print("  context - Run context manager example")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "client":
        client_example()
    elif mode == "server":
        server_example()
    elif mode == "context":
        context_manager_example()
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: client, server, context")
        sys.exit(1)


if __name__ == "__main__":
    main()