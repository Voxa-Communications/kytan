#!/usr/bin/env python3
"""
Python wrapper for kytan VPN - High Performance Peer-to-Peer VPN

This module provides a Python interface to the kytan VPN application,
allowing easy integration of VPN functionality into Python applications.
"""

import subprocess
import os
import signal
import threading
import time
from typing import Optional, Union, Dict, Any
from dataclasses import dataclass
import logging


@dataclass
class ClientConfig:
    """Configuration for kytan VPN client"""
    server: str
    port: int
    key: str
    no_default_route: bool = False


@dataclass
class ServerConfig:
    """Configuration for kytan VPN server"""
    bind: str = "0.0.0.0"
    port: int = 9527
    key: str = ""
    dns: str = "8.8.8.8"


class KytanError(Exception):
    """Custom exception for kytan-related errors"""
    pass


class KytanBase:
    """Base class for kytan VPN operations"""
    
    def __init__(self, binary_path: Optional[str] = None):
        """
        Initialize kytan wrapper
        
        Args:
            binary_path: Path to kytan binary. If None, searches in PATH and common locations
        """
        self.binary_path = self._find_binary(binary_path)
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def _find_binary(self, binary_path: Optional[str]) -> str:
        """Find kytan binary in system"""
        if binary_path and os.path.isfile(binary_path):
            return binary_path
        
        # First, check for bundled binary (built during pip install)
        try:
            import kytan
            package_dir = os.path.dirname(kytan.__file__)
            bundled_binary = os.path.join(package_dir, "bin", "kytan")
            if os.path.isfile(bundled_binary) and os.access(bundled_binary, os.X_OK):
                return bundled_binary
        except (ImportError, AttributeError):
            pass
        
        # Common locations to search
        search_paths = [
            "kytan",  # In PATH
            "./kytan",  # Current directory
            "../target/release/kytan",  # Rust build output
            "/usr/local/bin/kytan",
            "/usr/bin/kytan"
        ]
        
        for path in search_paths:
            try:
                # Test if binary exists and is executable
                result = subprocess.run([path, "-h"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode in [0, 1]:  # Help command might return 1
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue
        
        raise KytanError("kytan binary not found. Please ensure it's installed and in PATH.")
    
    def _get_bundled_binary_path(self) -> Optional[str]:
        """Get path to bundled kytan binary"""
        try:
            # Get the directory where this module is located
            module_dir = os.path.dirname(os.path.abspath(__file__))
            binary_name = "kytan.exe" if os.name == "nt" else "kytan"
            bundled_path = os.path.join(module_dir, "bin", binary_name)
            
            if os.path.isfile(bundled_path) and os.access(bundled_path, os.X_OK):
                return bundled_path
        except Exception:
            pass
        
        return None
    
    def _check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            raise KytanError("kytan requires root privileges. Please run as root/sudo.")
    
    def _build_command(self, mode: str, config: Union[ClientConfig, ServerConfig]) -> list:
        """Build command line arguments"""
        cmd = [self.binary_path, mode]
        
        if isinstance(config, ClientConfig):
            cmd.extend(["-s", config.server])
            cmd.extend(["-p", str(config.port)])
            cmd.extend(["-k", config.key])
            if config.no_default_route:
                cmd.append("-n")
        elif isinstance(config, ServerConfig):
            cmd.extend(["-l", config.bind])
            cmd.extend(["-p", str(config.port)])
            cmd.extend(["-k", config.key])
            cmd.extend(["-d", config.dns])
        
        return cmd
    
    def start(self, mode: str, config: Union[ClientConfig, ServerConfig], 
              env_vars: Optional[Dict[str, str]] = None) -> None:
        """
        Start kytan process
        
        Args:
            mode: "client" or "server"
            config: Configuration object
            env_vars: Additional environment variables
        """
        with self._lock:
            if self.is_running:
                raise KytanError("kytan is already running")
            
            self._check_root()
            
            cmd = self._build_command(mode, config)
            
            # Set up environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            self.logger.info(f"Starting kytan {mode}: {' '.join(cmd[1:])}")
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                self.is_running = True
                self.logger.info(f"kytan {mode} started with PID {self.process.pid}")
                
            except Exception as e:
                raise KytanError(f"Failed to start kytan: {e}")
    
    def stop(self, timeout: int = 10) -> None:
        """
        Stop kytan process
        
        Args:
            timeout: Timeout in seconds to wait for graceful shutdown
        """
        with self._lock:
            if not self.is_running or not self.process:
                return
            
            self.logger.info(f"Stopping kytan (PID {self.process.pid})")
            
            try:
                # Try graceful shutdown first
                self.process.send_signal(signal.SIGTERM)
                try:
                    self.process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Graceful shutdown timed out, forcing kill")
                    self.process.kill()
                    self.process.wait()
                
                self.logger.info("kytan stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping kytan: {e}")
            finally:
                self.is_running = False
                self.process = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of kytan process"""
        with self._lock:
            if not self.is_running or not self.process:
                return {"running": False, "pid": None}
            
            # Check if process is still alive
            poll_result = self.process.poll()
            if poll_result is not None:
                self.is_running = False
                return {"running": False, "pid": None, "exit_code": poll_result}
            
            return {"running": True, "pid": self.process.pid}
    
    def get_logs(self, lines: int = 50) -> Dict[str, str]:
        """
        Get recent logs from kytan process
        
        Args:
            lines: Number of lines to retrieve
            
        Returns:
            Dictionary with 'stdout' and 'stderr' keys
        """
        if not self.process:
            return {"stdout": "", "stderr": ""}
        
        try:
            # This is a simple implementation - in production you might want
            # to implement proper log rotation and buffering
            stdout_data = ""
            stderr_data = ""
            
            if self.process.stdout:
                stdout_data = self.process.stdout.read() or ""
            if self.process.stderr:
                stderr_data = self.process.stderr.read() or ""
            
            return {"stdout": stdout_data, "stderr": stderr_data}
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
            return {"stdout": "", "stderr": ""}


class KytanClient(KytanBase):
    """kytan VPN Client wrapper"""
    
    def connect(self, server: str, port: int, key: str, 
                no_default_route: bool = False,
                log_level: str = "info") -> None:
        """
        Connect to kytan VPN server
        
        Args:
            server: Server hostname or IP address
            port: Server port
            key: Encryption key
            no_default_route: Don't set default route
            log_level: Log level (debug, info, warn, error)
        """
        config = ClientConfig(
            server=server,
            port=port,
            key=key,
            no_default_route=no_default_route
        )
        
        env_vars = {"RUST_LOG": log_level} if log_level else None
        self.start("client", config, env_vars)
    
    def disconnect(self, timeout: int = 10) -> None:
        """Disconnect from VPN server"""
        self.stop(timeout)


class KytanServer(KytanBase):
    """kytan VPN Server wrapper"""
    
    def serve(self, port: int = 9527, key: str = "", 
              bind: str = "0.0.0.0", dns: str = "8.8.8.8",
              log_level: str = "info") -> None:
        """
        Start kytan VPN server
        
        Args:
            port: Port to listen on
            key: Encryption key
            bind: Address to bind to
            dns: DNS server for clients
            log_level: Log level (debug, info, warn, error)
        """
        if not key:
            raise KytanError("Encryption key is required for server mode")
        
        config = ServerConfig(
            bind=bind,
            port=port,
            key=key,
            dns=dns
        )
        
        env_vars = {"RUST_LOG": log_level} if log_level else None
        self.start("server", config, env_vars)
    
    def shutdown(self, timeout: int = 10) -> None:
        """Shutdown VPN server"""
        self.stop(timeout)


# Context manager support
class KytanContextManager:
    """Context manager for automatic cleanup"""
    
    def __init__(self, kytan_instance: KytanBase):
        self.kytan = kytan_instance
    
    def __enter__(self):
        return self.kytan
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kytan.stop()


def create_client(binary_path: Optional[str] = None) -> KytanClient:
    """Create a new kytan client instance"""
    return KytanClient(binary_path)


def create_server(binary_path: Optional[str] = None) -> KytanServer:
    """Create a new kytan server instance"""
    return KytanServer(binary_path)


def main():
    """Main entry point for the kytan-py command line interface"""
    # Simple CLI interface
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Python wrapper for kytan VPN")
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")
    
    # Client subcommand
    client_parser = subparsers.add_parser("client", help="Connect as client")
    client_parser.add_argument("-s", "--server", required=True, help="Server address")
    client_parser.add_argument("-p", "--port", type=int, default=9527, help="Server port")
    client_parser.add_argument("-k", "--key", required=True, help="Encryption key")
    client_parser.add_argument("-n", "--no-default-route", action="store_true",
                              help="Don't set default route")
    client_parser.add_argument("--log-level", default="info", help="Log level")
    
    # Server subcommand
    server_parser = subparsers.add_parser("server", help="Run as server")
    server_parser.add_argument("-l", "--bind", default="0.0.0.0", help="Bind address")
    server_parser.add_argument("-p", "--port", type=int, default=9527, help="Listen port")
    server_parser.add_argument("-k", "--key", required=True, help="Encryption key")
    server_parser.add_argument("-d", "--dns", default="8.8.8.8", help="DNS server")
    server_parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    # Set up logging
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    
    try:
        if args.mode == "client":
            client = create_client()
            client.connect(
                server=args.server,
                port=args.port,
                key=args.key,
                no_default_route=args.no_default_route,
                log_level=args.log_level
            )
            
            print(f"Connected to {args.server}:{args.port}")
            print("Press Ctrl+C to disconnect...")
            
            try:
                while client.get_status()["running"]:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nDisconnecting...")
                client.disconnect()
        
        elif args.mode == "server":
            server = create_server()
            server.serve(
                port=args.port,
                key=args.key,
                bind=args.bind,
                dns=args.dns,
                log_level=args.log_level
            )
            
            print(f"Server listening on {args.bind}:{args.port}")
            print("Press Ctrl+C to shutdown...")
            
            try:
                while server.get_status()["running"]:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down server...")
                server.shutdown()
    
    except KytanError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()