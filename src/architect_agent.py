from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config
from src.planner_agent import ProjectPlan, ProjectType

class TaskType(Enum):
    CREATE_FILE = "create_file"
    CREATE_DIRECTORY = "create_directory"
    SETUP_DEPENDENCIES = "setup_dependencies"
    CONFIGURE_BUILD = "configure_build"
    CREATE_DOCS = "create_docs"

@dataclass
class FileTask:
    file_path: str
    task_type: TaskType
    description: str
    dependencies: List[str]
    priority: int  # 1-10, lower is higher priority
    estimated_lines: int
    file_type: str  # html, css, js, py, md, etc.

@dataclass
class ArchitecturePlan:
    project_plan: ProjectPlan
    tasks: List[FileTask]
    execution_order: List[str]
    build_instructions: List[str]
    test_instructions: List[str]

class ArchitectAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        
        self.system_prompt = """
        You are a senior software architect. Your role is to break down project plans into 
        specific, actionable coding tasks for each file. You need to:
        
        1. Analyze the project plan and file structure
        2. Create detailed tasks for each file/directory
        3. Determine the optimal order of file creation
        4. Specify dependencies between files
        5. Provide build and test instructions
        
        Be practical and specific. Each task should be clear enough for a developer to implement.
        Consider file dependencies and logical ordering.
        """
    
    def create_architecture_plan(self, project_plan: ProjectPlan) -> ArchitecturePlan:
        """Break down project plan into specific coding tasks"""
        
        prompt = f"""
        Break down this project plan into specific coding tasks for each file:
        
        Project Plan:
        - Name: {project_plan.project_name}
        - Type: {project_plan.project_type.value}
        - Description: {project_plan.description}
        - Features: {', '.join(project_plan.features)}
        - Technologies: {', '.join(project_plan.technologies)}
        - File Structure: {json.dumps(project_plan.file_structure, indent=2)}
        - Dependencies: {', '.join(project_plan.dependencies)}
        - Complexity: {project_plan.complexity}
        
        Create a JSON response with this structure:
        {{
            "tasks": [
                {{
                    "file_path": "path/to/file.ext",
                    "task_type": "create_file|create_directory|setup_dependencies|configure_build|create_docs",
                    "description": "detailed description of what this file should contain",
                    "dependencies": ["file1.ext", "file2.ext"],
                    "priority": 1,
                    "estimated_lines": 50,
                    "file_type": "html|css|js|py|md|json|yaml|etc"
                }}
            ],
            "execution_order": ["file1.ext", "file2.ext", "dir1/", "file3.ext"],
            "build_instructions": [
                "Step 1: Install dependencies",
                "Step 2: Build the project"
            ],
            "test_instructions": [
                "How to test the project",
                "What to verify"
            ]
        }}
        
        Guidelines:
        - Root files (index.html, main.py, etc.) should have highest priority (1-3)
        - Configuration files come early (package.json, requirements.txt, etc.)
        - Dependencies should be listed before files that need them
        - Consider the logical flow of development
        - Be specific about what each file should contain
        - Include setup and build instructions
        """
        
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip())
            
            # Create FileTask objects
            tasks = []
            for task_data in result.get("tasks", []):
                task = FileTask(
                    file_path=task_data.get("file_path", ""),
                    task_type=TaskType(task_data.get("task_type", "create_file")),
                    description=task_data.get("description", ""),
                    dependencies=task_data.get("dependencies", []),
                    priority=task_data.get("priority", 5),
                    estimated_lines=task_data.get("estimated_lines", 20),
                    file_type=task_data.get("file_type", "txt")
                )
                tasks.append(task)
            
            return ArchitecturePlan(
                project_plan=project_plan,
                tasks=tasks,
                execution_order=result.get("execution_order", []),
                build_instructions=result.get("build_instructions", []),
                test_instructions=result.get("test_instructions", [])
            )
            
        except Exception as e:
            print(f"Error in architect agent: {e}")
            return self._create_fallback_architecture(project_plan)
    
    def _create_fallback_architecture(self, project_plan: ProjectPlan) -> ArchitecturePlan:
        """Create a basic fallback architecture when LLM fails"""
        
        # Create basic tasks based on project type
        tasks = []
        
        if project_plan.project_type == ProjectType.WEB_APP:
            tasks = [
                FileTask(
                    file_path="index.html",
                    task_type=TaskType.CREATE_FILE,
                    description="Main HTML file with basic structure",
                    dependencies=[],
                    priority=1,
                    estimated_lines=30,
                    file_type="html"
                ),
                FileTask(
                    file_path="style.css",
                    task_type=TaskType.CREATE_FILE,
                    description="CSS styling for the web application",
                    dependencies=["index.html"],
                    priority=2,
                    estimated_lines=20,
                    file_type="css"
                ),
                FileTask(
                    file_path="script.js",
                    task_type=TaskType.CREATE_FILE,
                    description="JavaScript functionality for the web app",
                    dependencies=["index.html", "style.css"],
                    priority=3,
                    estimated_lines=40,
                    file_type="js"
                )
            ]
        
        elif project_plan.project_type == ProjectType.API:
            tasks = [
                FileTask(
                    file_path="main.py",
                    task_type=TaskType.CREATE_FILE,
                    description="Main FastAPI application file",
                    dependencies=[],
                    priority=1,
                    estimated_lines=50,
                    file_type="py"
                ),
                FileTask(
                    file_path="requirements.txt",
                    task_type=TaskType.CREATE_FILE,
                    description="Python dependencies file",
                    dependencies=[],
                    priority=1,
                    estimated_lines=5,
                    file_type="txt"
                )
            ]
        
        return ArchitecturePlan(
            project_plan=project_plan,
            tasks=tasks,
            execution_order=[task.file_path for task in tasks],
            build_instructions=["Install dependencies", "Run the application"],
            test_instructions=["Test basic functionality"]
        )
    
    def optimize_task_order(self, tasks: List[FileTask]) -> List[FileTask]:
        """Optimize task execution order based on dependencies and priority"""
        
        # Sort by priority first, then by dependencies
        sorted_tasks = sorted(tasks, key=lambda x: (x.priority, len(x.dependencies)))
        
        # Simple dependency resolution
        ordered_tasks = []
        remaining_tasks = sorted_tasks.copy()
        
        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = [
                task for task in remaining_tasks
                if all(dep in [t.file_path for t in ordered_tasks] or not dep for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                # If no ready tasks, take the one with highest priority
                ready_tasks = [min(remaining_tasks, key=lambda x: x.priority)]
            
            # Add the highest priority ready task
            next_task = min(ready_tasks, key=lambda x: x.priority)
            ordered_tasks.append(next_task)
            remaining_tasks.remove(next_task)
        
        return ordered_tasks
    
    def validate_architecture_plan(self, plan: ArchitecturePlan) -> bool:
        """Validate that the architecture plan is complete and reasonable"""
        
        if not plan.tasks:
            return False
        
        if not plan.execution_order:
            return False
        
        # Check that all tasks have valid file paths
        for task in plan.tasks:
            if not task.file_path:
                return False
        
        # Check that execution order contains all tasks
        task_paths = {task.file_path for task in plan.tasks}
        order_paths = set(plan.execution_order)
        
        if not task_paths.issubset(order_paths):
            return False
        
        return True
