#!/usr/bin/env python3
"""
Setup script for kytan-py that builds the kytan Rust binary during installation.
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install


class CargoNotFoundError(Exception):
    """Raised when cargo (Rust build tool) is not found."""
    pass


def check_cargo():
    """Check if cargo is available."""
    try:
        subprocess.run(
            ["cargo", "--version"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_kytan():
    """Build the kytan Rust binary."""
    if not check_cargo():
        raise CargoNotFoundError(
            "Cargo (Rust) is required to build kytan. "
            "Please install Rust from https://rustup.rs/"
        )
    
    print("Building kytan binary...")
    
    # Find the project root (where Cargo.toml is located)
    current_dir = Path(__file__).parent.absolute()
    
    # First try the development layout (parent directory)
    project_root = current_dir.parent
    cargo_toml_path = project_root / "Cargo.toml"
    
    # If not found, try the packaged layout (files included in the package)
    if not cargo_toml_path.exists():
        # Look for Cargo.toml in the current package directory
        cargo_toml_path = current_dir / "Cargo.toml"
        if cargo_toml_path.exists():
            project_root = current_dir
        else:
            # Try to find it in the installed package
            import pkg_resources
            try:
                cargo_toml_path = Path(pkg_resources.resource_filename(__name__, 'Cargo.toml'))
                project_root = cargo_toml_path.parent
            except:
                pass
    
    if not cargo_toml_path.exists():
        raise FileNotFoundError(
            f"Could not find Cargo.toml in any expected location. "
            "Searched: {project_root}, {current_dir}"
        )
    
    print(f"Found Cargo.toml at: {cargo_toml_path}")
    
    # Build the binary
    try:
        env = os.environ.copy()
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=project_root,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ kytan binary built successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build kytan binary: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise
    
    # Copy the binary to the package
    binary_src = project_root / "target" / "release" / "kytan"
    if not binary_src.exists():
        raise FileNotFoundError(f"Built binary not found at {binary_src}")
    
    # Create bin directory in package
    bin_dir = current_dir / "kytan" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    binary_dst = bin_dir / "kytan"
    shutil.copy2(binary_src, binary_dst)
    
    # Make sure it's executable
    os.chmod(binary_dst, 0o755)
    
    print(f"✓ Binary copied to {binary_dst}")


class BuildCommand(build_py):
    """Custom build command that builds the Rust binary."""
    
    def run(self):
        build_kytan()
        super().run()


class DevelopCommand(develop):
    """Custom develop command that builds the Rust binary."""
    
    def run(self):
        build_kytan()
        super().run()


class InstallCommand(install):
    """Custom install command that builds the Rust binary."""
    
    def run(self):
        build_kytan()
        super().run()


# Read the contents of README file
def read_readme():
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return ""


setup(
    name="kytan-py",
    version="0.1.0",
    author="kytan-py contributors",
    description="Python wrapper for kytan VPN - High Performance Peer-to-Peer VPN",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/changlan/kytan",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Security",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "kytan-py=kytan.kytan:main",
        ],
    },
    keywords="vpn, networking, security, peer-to-peer, tunnel",
    include_package_data=True,
    package_data={
        "kytan": ["bin/*"],
        "": ["Cargo.toml", "Cargo.lock", "build.sh", "src/*.rs", "LICENSE"],
    },
    cmdclass={
        "build_py": BuildCommand,
        "develop": DevelopCommand,
        "install": InstallCommand,
    },
    zip_safe=False,  # Binary files can't be in a zip
)