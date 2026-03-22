import os
import subprocess
import sys
import shutil
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import streamlit as st
import webbrowser
import threading
import time

class ProjectExecutor:
    """Handles project execution and running capabilities"""
    
    def __init__(self):
        self.running_processes = {}
        
    def detect_project_type(self, project_path: str) -> str:
        """Detect the type of project for execution"""
        
        project_files = []
        if os.path.exists(project_path):
            for root, dirs, files in os.walk(project_path):
                project_files.extend(files)
        
        project_files = [f.lower() for f in project_files]
        
        # Check for different project types
        if "package.json" in project_files:
            return "nodejs"
        elif "requirements.txt" in project_files or "pyproject.toml" in project_files:
            return "python"
        elif "index.html" in project_files:
            return "static"
        elif "dockerfile" in project_files:
            return "docker"
        elif "cargo.toml" in project_files:
            return "rust"
        elif "go.mod" in project_files:
            return "go"
        else:
            return "unknown"
    
    def get_run_commands(self, project_path: str) -> List[Dict[str, str]]:
        """Get available run commands for the project"""
        
        project_type = self.detect_project_type(project_path)
        commands = []
        
        if project_type == "nodejs":
            commands = [
                {"name": "Install Dependencies", "command": "npm install"},
                {"name": "Start Development Server", "command": "npm start"},
                {"name": "Build Project", "command": "npm run build"}
            ]
        elif project_type == "python":
            commands = [
                {"name": "Install Dependencies", "command": "pip install -r requirements.txt"},
                {"name": "Run Main App", "command": "python main.py"},
                {"name": "Run with Flask", "command": "flask run"},
                {"name": "Run with FastAPI", "command": "uvicorn main:app --reload"}
            ]
        elif project_type == "static":
            commands = [
                {"name": "Open in Browser", "command": f"start {project_path}/index.html"},
                {"name": "Start Local Server", "command": f"python -m http.server 8000 --directory {project_path}"}
            ]
        else:
            commands = [
                {"name": "List Files", "command": f"ls -la {project_path}"}
            ]
        
        return commands
    
    def execute_command(self, command: str, project_path: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command in the project directory"""
        
        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Restore original directory
            os.chdir(original_cwd)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1
            }
        except Exception as e:
            os.chdir(original_cwd)
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def find_available_port(self, start_port: int = 8000) -> int:
        """Find an available port starting from start_port"""
        
        import socket
        
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        
        return start_port
    
    def start_project_server(self, project_path: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Start a development server for the project"""
        
        if port is None:
            port = self.find_available_port()
        
        project_type = self.detect_project_type(project_path)
        
        try:
            if project_type == "nodejs":
                # Check if npm start is available
                package_json_path = os.path.join(project_path, "package.json")
                if os.path.exists(package_json_path):
                    # Start npm start
                    process = subprocess.Popen(
                        f"npm start -- --port {port}",
                        shell=True,
                        cwd=project_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    return {
                        "success": True,
                        "port": port,
                        "process_id": process.pid,
                        "url": f"http://localhost:{port}",
                        "command": f"npm start -- --port {port}"
                    }
            
            elif project_type == "python":
                # Try to find main Python file
                main_files = ["main.py", "app.py", "server.py", "index.py"]
                main_file = None
                
                for file in main_files:
                    if os.path.exists(os.path.join(project_path, file)):
                        main_file = file
                        break
                
                if main_file:
                    process = subprocess.Popen(
                        [sys.executable, main_file],
                        cwd=project_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    return {
                        "success": True,
                        "port": port,
                        "process_id": process.pid,
                        "url": f"http://localhost:{port}",
                        "command": f"python {main_file}"
                    }
            
            elif project_type == "static":
                # Start simple HTTP server
                process = subprocess.Popen(
                    [sys.executable, "-m", "http.server", str(port)],
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return {
                    "success": True,
                    "port": port,
                    "process_id": process.pid,
                    "url": f"http://localhost:{port}",
                    "command": f"python -m http.server {port}"
                }
            
            return {
                "success": False,
                "error": f"No suitable server configuration found for {project_type} project"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_project_server(self, process_id: int) -> bool:
        """Stop a running project server"""
        
        try:
            # Try to terminate the process gracefully
            os.kill(process_id, 15)  # SIGTERM
            time.sleep(2)
            
            # Force kill if still running
            try:
                os.kill(process_id, 9)  # SIGKILL
            except OSError:
                pass  # Process already terminated
            
            return True
            
        except Exception as e:
            print(f"Error stopping process {process_id}: {e}")
            return False
    
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """Get detailed information about the project"""
        
        info = {
            "path": project_path,
            "type": self.detect_project_type(project_path),
            "files": [],
            "size_mb": 0,
            "dependencies": [],
            "run_commands": []
        }
        
        try:
            # Get file list
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    file_info = {
                        "path": relative_path,
                        "size": os.path.getsize(file_path),
                        "type": os.path.splitext(file)[1][1:] if os.path.splitext(file)[1] else "unknown"
                    }
                    info["files"].append(file_info)
                    info["size_mb"] += file_info["size"]
            
            info["size_mb"] = info["size_mb"] / (1024 * 1024)  # Convert to MB
            
            # Get dependencies
            package_json = os.path.join(project_path, "package.json")
            requirements_txt = os.path.join(project_path, "requirements.txt")
            
            if os.path.exists(package_json):
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    info["dependencies"] = list(package_data.get("dependencies", {}).keys())
            
            elif os.path.exists(requirements_txt):
                with open(requirements_txt, 'r') as f:
                    lines = f.readlines()
                    info["dependencies"] = [line.strip().split("==")[0] for line in lines if line.strip() and not line.startswith("#")]
            
            # Get run commands
            info["run_commands"] = self.get_run_commands(project_path)
            
        except Exception as e:
            info["error"] = str(e)
        
        return info

def render_project_execution_interface(project_path: str):
    """Render the project execution interface in Streamlit"""
    
    executor = ProjectExecutor()
    project_info = executor.get_project_info(project_path)
    
    st.markdown("## 🚀 Project Execution")
    
    # Project information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Project Type", project_info["type"].title())
    
    with col2:
        st.metric("Total Files", len(project_info["files"]))
    
    with col3:
        st.metric("Project Size", f"{project_info['size_mb']:.2f} MB")
    
    # Dependencies
    if project_info["dependencies"]:
        st.markdown("### 📦 Dependencies")
        st.write(", ".join(project_info["dependencies"]))
    
    # Run commands
    if project_info["run_commands"]:
        st.markdown("### ⚡ Available Commands")
        
        selected_command = st.selectbox(
            "Select command to execute:",
            options=project_info["run_commands"],
            format_func=lambda x: x["name"],
            key="run_command_select"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Execute Command", type="primary"):
                with st.spinner(f"Executing {selected_command['name']}..."):
                    result = executor.execute_command(
                        selected_command["command"],
                        project_path
                    )
                    
                    if result["success"]:
                        st.success(f"✅ Command executed successfully!")
                        
                        if result["stdout"]:
                            st.markdown("### 📤 Output")
                            st.code(result["stdout"], language="text")
                    else:
                        st.error(f"❌ Command failed!")
                        
                        if result["stderr"]:
                            st.markdown("### ❌ Error Output")
                            st.code(result["stderr"], language="text")
        
        with col2:
            if st.button("📋 Copy Command"):
                st.write(f"```bash\n{selected_command['command']}\n```")
    
    # Server controls
    st.markdown("### 🌐 Development Server")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        port = st.number_input("Port", value=8000, min_value=1000, max_value=9999)
    
    with col2:
        if st.button("🚀 Start Server", type="primary"):
            with st.spinner("Starting development server..."):
                server_result = executor.start_project_server(project_path, port)
                
                if server_result["success"]:
                    st.success(f"✅ Server started on {server_result['url']}")
                    
                    # Store server info in session state
                    st.session_state.running_server = server_result
                    
                    # Show open in browser button
                    if st.button("🌐 Open in Browser"):
                        webbrowser.open(server_result["url"])
                else:
                    st.error(f"❌ Failed to start server: {server_result.get('error', 'Unknown error')}")
    
    with col3:
        if st.button("🛑 Stop Server") and "running_server" in st.session_state:
            server_info = st.session_state.running_server
            
            if executor.stop_project_server(server_info["process_id"]):
                st.success("✅ Server stopped")
                del st.session_state.running_server
            else:
                st.error("❌ Failed to stop server")
    
    # Show running server status
    if "running_server" in st.session_state:
        server_info = st.session_state.running_server
        st.info(f"""
        🟢 **Server Running**
        - **URL**: [{server_info['url']}]({server_info['url']})
        - **Port**: {server_info['port']}
        - **Process ID**: {server_info['process_id']}
        - **Command**: `{server_info['command']}`
        """)
    
    # File browser
    st.markdown("### 📁 Project Files")
    
    # Create file tree
    file_tree = {}
    for file_info in project_info["files"]:
        parts = file_info["path"].split(os.sep)
        current = file_tree
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = file_info
    
    # Display file tree
    def display_tree(tree, indent=0):
        for key, value in tree.items():
            if isinstance(value, dict):
                st.write("  " * indent + f"📁 {key}/")
                display_tree(value, indent + 2)
            else:
                size_kb = value["size"] / 1024
                st.write("  " * indent + f"📄 {key} ({size_kb:.1f} KB)")
    
    display_tree(file_tree)
