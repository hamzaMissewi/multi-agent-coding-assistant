import streamlit as st
import os
import json
import time
import zipfile
import io
from typing import Dict, Any, List
from pathlib import Path

from src.workflow import MultiAgentWorkflow, WorkflowResult
from config import Config

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Coding Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'workflow' not in st.session_state:
    st.session_state.workflow = MultiAgentWorkflow()

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

def main():
    st.title("🤖 Multi-Agent Coding Assistant")
    st.markdown("---")
    
    # Sidebar
    render_sidebar()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🏠 Generate", "📊 History", "⚙️ Settings"])
    
    with tab1:
        render_generation_tab()
    
    with tab2:
        render_history_tab()
    
    with tab3:
        render_settings_tab()

def render_sidebar():
    """Render the sidebar with information and controls"""
    
    st.sidebar.markdown("## 🎯 About")
    st.sidebar.info("""
    This AI-powered coding assistant uses multiple agents to convert your natural language requests into working software projects:
    
    - **Planner Agent**: Analyzes requirements
    - **Architect Agent**: Designs file structure  
    - **Coder Agent**: Generates actual code
    
    All agents work together using LangGraph for coordinated workflow execution.
    """)
    
    st.sidebar.markdown("## 📈 Workflow Status")
    
    # Get workflow status
    status = st.session_state.workflow.get_workflow_status()
    
    st.sidebar.metric("Agents Ready", status["agents_initialized"])
    st.sidebar.metric("LLM Model", status["llm_model"])
    st.sidebar.metric("Output Dir", status["output_directory"])
    
    st.sidebar.markdown("## 🛠️ Quick Examples")
    
    examples = [
        "Build a calculator web app with add, subtract, multiply and divide buttons",
        "Create a REST API for managing a todo list",
        "Make a command-line tool for file conversion",
        "Build a data analysis dashboard with charts",
        "Create a simple blog with Flask"
    ]
    
    for example in examples:
        if st.sidebar.button(f"📝 {example[:50]}...", key=f"example_{examples.index(example)}"):
            st.session_state.user_input = example

def render_generation_tab():
    """Render the main generation interface"""
    
    st.markdown("## 🚀 Generate Your Project")
    
    # User input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "Describe the project you want to build:",
            value=st.session_state.get('user_input', ''),
            height=100,
            placeholder="e.g., Build a calculator web app with add, subtract, multiply and divide buttons",
            help="Be specific about features, technologies, and requirements"
        )
    
    with col2:
        st.markdown("### 🎯 Tips")
        st.markdown("""
        - Be specific about features
        - Mention preferred technologies
        - Describe the main functionality
        - Include UI requirements
        """)
    
    # Generation controls
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        project_name = st.text_input(
            "Project Name (optional)",
            placeholder="Auto-generated if empty",
            help="Custom name for your project"
        )
    
    with col2:
        complexity = st.selectbox(
            "Complexity Level",
            ["simple", "medium", "complex"],
            index=1,
            help="Higher complexity may take longer but produces more detailed projects"
        )
    
    with col3:
        include_docs = st.checkbox(
            "Include Documentation",
            value=True,
            help="Generate README and documentation files"
        )
    
    # Generate button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    
    with generate_col2:
        if st.button("🚀 Generate Project", type="primary", use_container_width=True):
            if not user_input.strip():
                st.error("Please describe the project you want to build")
                return
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Update progress
                progress_bar.progress(10)
                status_text.text("🎯 Planning your project...")
                
                # Execute workflow
                result = st.session_state.workflow.execute_workflow(user_input)
                
                progress_bar.progress(100)
                status_text.text("✅ Generation complete!")
                
                # Store result
                st.session_state.current_result = result
                st.session_state.generation_history.append({
                    "timestamp": time.time(),
                    "request": user_input,
                    "result": result
                })
                
                # Show results
                render_generation_results(result)
                
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Generation failed")
                st.error(f"Generation failed: {str(e)}")
    
    # Show current results if available
    if st.session_state.current_result:
        st.markdown("---")
        render_generation_results(st.session_state.current_result)

def render_generation_results(result: WorkflowResult):
    """Render the results of project generation"""
    
    if not result.success:
        st.error("❌ Project generation failed!")
        
        if result.errors:
            st.markdown("### Errors:")
            for error in result.errors:
                st.error(f"• {error}")
        
        return
    
    # Success message
    st.success(f"✅ Project generated successfully in {result.total_time:.2f} seconds!")
    
    # Project details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Project Details")
        
        if result.project_plan:
            st.info(f"""
            **Name**: {result.project_plan.project_name}
            
            **Type**: {result.project_plan.project_type.value}
            
            **Description**: {result.project_plan.description}
            
            **Features**: {', '.join(result.project_plan.features)}
            
            **Technologies**: {', '.join(result.project_plan.technologies)}
            
            **Files Generated**: {len(result.code_result.generated_files) if result.code_result else 0}
            """)
    
    with col2:
        st.markdown("### 📊 Statistics")
        
        if result.code_result:
            files_by_quality = {}
            for file in result.code_result.generated_files:
                quality = file.quality.value
                files_by_quality[quality] = files_by_quality.get(quality, 0) + 1
            
            for quality, count in files_by_quality.items():
                st.metric(f"{quality.title()} Files", count)
            
            st.metric("Total Lines", sum(f.lines_of_code for f in result.code_result.generated_files))
    
    # File list
    if result.code_result and result.code_result.generated_files:
        st.markdown("### 📁 Generated Files")
        
        file_data = []
        for file in result.code_result.generated_files:
            file_data.append({
                "File Path": file.file_path,
                "Type": file.file_type,
                "Lines": file.lines_of_code,
                "Quality": file.quality.value,
                "Generation Time": f"{file.generation_time:.2f}s"
            })
        
        st.dataframe(file_data, use_container_width=True)
    
    # Download section
    if result.project_path and os.path.exists(result.project_path):
        st.markdown("### 💾 Download Project")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📦 Download ZIP", type="secondary"):
                zip_data = create_project_zip(result.project_path)
                if zip_data:
                    st.download_button(
                        label="Download project.zip",
                        data=zip_data,
                        file_name=f"{result.project_plan.project_name.lower().replace(' ', '-')}.zip",
                        mime="application/zip"
                    )
        
        with col2:
            if st.button("📂 Open Folder", type="secondary"):
                st.info(f"Project location: `{result.project_path}`")
        
        with col3:
            if st.button("🔄 Regenerate", type="secondary"):
                st.session_state.current_result = None
                st.rerun()
    
    # Warnings
    if result.warnings:
        st.markdown("### ⚠️ Warnings")
        for warning in result.warnings:
            st.warning(f"• {warning}")

def render_history_tab():
    """Render the generation history"""
    
    st.markdown("## 📊 Generation History")
    
    if not st.session_state.generation_history:
        st.info("No projects generated yet. Go to the Generate tab to create your first project!")
        return
    
    # History summary
    total_generations = len(st.session_state.generation_history)
    successful_generations = sum(1 for h in st.session_state.generation_history if h["result"].success)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Generations", total_generations)
    
    with col2:
        st.metric("Successful", successful_generations)
    
    with col3:
        st.metric("Success Rate", f"{(successful_generations/total_generations*100):.1f}%")
    
    # Detailed history
    st.markdown("### 📜 Detailed History")
    
    for i, entry in enumerate(reversed(st.session_state.generation_history[-10:])):  # Show last 10
        with st.expander(f"🕐 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))} - {entry['request'][:50]}..."):
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Request**: {entry['request']}")
                
                if entry['result'].success:
                    st.success(f"✅ Generated {entry['result'].project_plan.project_name if entry['result'].project_plan else 'Unknown'}")
                else:
                    st.error("❌ Generation failed")
            
            with col2:
                if st.button(f"📥 Download", key=f"download_{i}"):
                    if entry['result'].project_path and os.path.exists(entry['result'].project_path):
                        zip_data = create_project_zip(entry['result'].project_path)
                        if zip_data:
                            st.download_button(
                                label=f"Download {entry['result'].project_plan.project_name}.zip",
                                data=zip_data,
                                file_name=f"{entry['result'].project_plan.project_name.lower().replace(' ', '-')}.zip",
                                mime="application/zip",
                                key=f"dl_button_{i}"
                            )

def render_settings_tab():
    """Render the settings page"""
    
    st.markdown("## ⚙️ Settings")
    
    # Configuration validation
    try:
        Config.validate()
        st.success("✅ Configuration is valid")
    except ValueError as e:
        st.error(f"❌ Configuration error: {e}")
    
    # Current settings
    st.markdown("### 📋 Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("LLM Model", Config.LLM_MODEL)
        st.metric("Max Tokens", Config.MAX_TOKENS)
        st.metric("Temperature", Config.TEMPERATURE)
    
    with col2:
        st.metric("Output Directory", Config.OUTPUT_DIRECTORY)
        st.metric("Max Project Size", f"{Config.MAX_PROJECT_SIZE_MB}MB")
        st.metric("Max Retries", Config.MAX_RETRIES)
    
    # System information
    st.markdown("### 🖥️ System Information")
    
    import sys
    import platform
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Python Version", sys.version.split()[0])
        st.metric("Platform", platform.system())
    
    with col2:
        st.metric("Architecture", platform.architecture()[0])
        st.metric("Processor", platform.processor())

def create_project_zip(project_path: str) -> bytes:
    """Create a ZIP file of the generated project"""
    
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            project_dir = Path(project_path)
            
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path
                    arcname = file_path.relative_to(project_dir.parent)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Failed to create ZIP file: {e}")
        return None

if __name__ == "__main__":
    main()
