from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import re
from langchain_groq import ChatGroq
# from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config

class ProjectType(Enum):
    WEB_APP = "web_app"
    API = "api"
    CLI_TOOL = "cli_tool"
    DATA_ANALYSIS = "data_analysis"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    LIBRARY = "library"

@dataclass
class ProjectPlan:
    project_name: str
    project_type: ProjectType
    description: str
    features: List[str]
    technologies: List[str]
    file_structure: Dict[str, Any]
    dependencies: List[str]
    complexity: str  # simple, medium, complex
    estimated_files: int

class PlannerAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        
        self.system_prompt = """
        You are an expert software architect and project planner. Your role is to analyze user requests 
        and create comprehensive project plans. You need to:
        
        1. Understand the user's requirements and intent
        2. Identify the project type (web app, API, CLI tool, etc.)
        3. Determine the appropriate technology stack
        4. Plan the file structure and architecture
        5. Estimate complexity and required files
        
        Be specific and practical. Focus on modern, well-accepted technologies and patterns.
        """
    
    def analyze_request(self, user_request: str) -> ProjectPlan:
        """Analyze user request and create a comprehensive project plan"""
        
        prompt = f"""
        Analyze this user request and create a detailed project plan:
        
        User Request: "{user_request}"
        
        Please provide a JSON response with the following structure:
        {{
            "project_name": "descriptive project name",
            "project_type": "web_app|api|cli_tool|data_analysis|mobile_app|desktop_app|library",
            "description": "brief description of what this project does",
            "features": ["feature1", "feature2", "feature3"],
            "technologies": ["tech1", "tech2", "tech3"],
            "file_structure": {{
                "root_files": ["file1", "file2"],
                "directories": {{
                    "dir1": ["file1", "file2"],
                    "dir2": ["file1"]
                }}
            }},
            "dependencies": ["dependency1", "dependency2"],
            "complexity": "simple|medium|complex",
            "estimated_files": 10
        }}
        
        Consider:
        - For web apps: HTML, CSS, JavaScript frameworks (React, Vue), or Python frameworks (Flask, Django, Streamlit)
        - For APIs: FastAPI, Flask, Express.js
        - For CLI tools: Python with Click/argparse, Node.js with commander
        - For data analysis: Python with pandas, matplotlib, seaborn
        - Choose technologies that are modern, well-supported, and appropriate for the project
        """
        
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip())
            
            # Validate and clean the response
            project_type = ProjectType(result.get("project_type", "web_app"))
            
            return ProjectPlan(
                project_name=result.get("project_name", "Untitled Project"),
                project_type=project_type,
                description=result.get("description", ""),
                features=result.get("features", []),
                technologies=result.get("technologies", []),
                file_structure=result.get("file_structure", {}),
                dependencies=result.get("dependencies", []),
                complexity=result.get("complexity", "medium"),
                estimated_files=result.get("estimated_files", 5)
            )
            
        except Exception as e:
            print(f"Error in planner agent: {e}")
            # Fallback to a simple web app plan
            return self._create_fallback_plan(user_request)
    
    def _create_fallback_plan(self, user_request: str) -> ProjectPlan:
        """Create a basic fallback plan when LLM fails"""
        return ProjectPlan(
            project_name="Generated Project",
            project_type=ProjectType.WEB_APP,
            description=f"A project based on: {user_request}",
            features=["Basic functionality"],
            technologies=["HTML", "CSS", "JavaScript"],
            file_structure={
                "root_files": ["index.html", "style.css", "script.js"],
                "directories": {}
            },
            dependencies=[],
            complexity="simple",
            estimated_files=3
        )
    
    def extract_project_name(self, user_request: str) -> str:
        """Extract a suitable project name from the user request"""
        # Simple heuristics for project name extraction
        patterns = [
            r"build\s+(?:a\s+)?(\w+(?:\s+\w+)*)",
            r"create\s+(?:a\s+)?(\w+(?:\s+\w+)*)",
            r"make\s+(?:a\s+)?(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(?:app|application|tool|system)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_request.lower())
            if match:
                name = match.group(1).title()
                return name.replace(" ", "")
        
        return "GeneratedProject"
    
    def validate_plan(self, plan: ProjectPlan) -> bool:
        """Validate that the project plan is complete and reasonable"""
        if not plan.project_name or not plan.description:
            return False
        
        if not plan.technologies or not plan.file_structure:
            return False
        
        if plan.estimated_files < 1 or plan.estimated_files > 50:
            return False
        
        return True
