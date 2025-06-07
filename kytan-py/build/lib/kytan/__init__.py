"""
kytan-py: Python wrapper for kytan VPN

A Python interface to the kytan high-performance peer-to-peer VPN application.
"""

from .kytan import (
    KytanClient,
    KytanServer,
    KytanError,
    ClientConfig,
    ServerConfig,
    create_client,
    create_server,
    KytanContextManager
)

__version__ = "0.1.0"
__author__ = "kytan-py contributors"
__description__ = "Python wrapper for kytan VPN"

__all__ = [
    "KytanClient",
    "KytanServer", 
    "KytanError",
    "ClientConfig",
    "ServerConfig",
    "create_client",
    "create_server",
    "KytanContextManager"
]