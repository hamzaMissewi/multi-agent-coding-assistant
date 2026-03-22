from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
# import json
import os
import re
import time
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from config import Config
from src.architect_agent import FileTask, TaskType, ArchitecturePlan
from src.planner_agent import ProjectPlan, ProjectType

class CodeQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"

@dataclass
class GeneratedFile:
    file_path: str
    content: str
    file_type: str
    quality: CodeQuality
    lines_of_code: int
    dependencies_used: List[str]
    generation_time: float

@dataclass
class CodeGenerationResult:
    success: bool
    generated_files: List[GeneratedFile]
    errors: List[str]
    warnings: List[str]
    total_generation_time: float
    project_path: str

class CoderAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        
        self.system_prompt = """
        You are an expert full-stack developer. Your role is to generate high-quality, 
        production-ready code based on specific task descriptions. You need to:
        
        1. Write clean, well-structured, and maintainable code
        2. Follow best practices for the specific programming language/framework
        3. Include appropriate comments and documentation
        4. Handle errors and edge cases appropriately
        5. Ensure code is functional and testable
        6. Follow modern coding standards and conventions
        
        Generate complete, working code that matches the requirements exactly.
        """
        
        # Code templates for common patterns
        self.templates = {
            "html": self._get_html_template,
            "css": self._get_css_template,
            "js": self._get_js_template,
            "py": self._get_python_template,
            "json": self._get_json_template,
            "md": self._get_markdown_template
        }
    
    def generate_files(self, architecture_plan: ArchitecturePlan, project_path: str) -> CodeGenerationResult:
        """Generate all files based on the architecture plan"""
        
        generated_files = []
        errors = []
        warnings = []
        start_time = time.time()
        
        try:
            # Optimize task order
            ordered_tasks = self._optimize_task_execution(architecture_plan.tasks)
            
            for task in ordered_tasks:
                try:
                    generated_file = self._generate_single_file(task, architecture_plan.project_plan)
                    if generated_file:
                        generated_files.append(generated_file)
                        
                        # Write file to disk
                        self._write_file_to_disk(generated_file, project_path)
                        
                    else:
                        warnings.append(f"Failed to generate file: {task.file_path}")
                        
                except Exception as e:
                    errors.append(f"Error generating {task.file_path}: {str(e)}")
            
            total_time = time.time() - start_time
            
            return CodeGenerationResult(
                success=len(errors) == 0,
                generated_files=generated_files,
                errors=errors,
                warnings=warnings,
                total_generation_time=total_time,
                project_path=project_path
            )
            
        except Exception as e:
            return CodeGenerationResult(
                success=False,
                generated_files=generated_files,
                errors=[f"Critical error in code generation: {str(e)}"],
                warnings=warnings,
                total_generation_time=time.time() - start_time,
                project_path=project_path
            )
    
    def _generate_single_file(self, task: FileTask, project_plan: ProjectPlan) -> Optional[GeneratedFile]:
        """Generate code for a single file"""
        
        start_time = time.time()
        
        # Check if we have a template for this file type
        if task.file_type in self.templates:
            try:
                content = self.templates[task.file_type](task, project_plan)
                quality = self._assess_code_quality(content, task.file_type)
                
                return GeneratedFile(
                    file_path=task.file_path,
                    content=content,
                    file_type=task.file_type,
                    quality=quality,
                    lines_of_code=len(content.split('\n')),
                    dependencies_used=task.dependencies,
                    generation_time=time.time() - start_time
                )
            except Exception as e:
                print(f"Template generation failed for {task.file_path}: {e}")
        
        # Fall back to LLM generation
        return self._generate_with_llm(task, project_plan, start_time)
    
    def _generate_with_llm(self, task: FileTask, project_plan: ProjectPlan, start_time: float) -> Optional[GeneratedFile]:
        """Generate code using LLM when templates are not available"""
        
        prompt = f"""
        Generate code for this specific file:
        
        Task Details:
        - File Path: {task.file_path}
        - File Type: {task.file_type}
        - Description: {task.description}
        - Dependencies: {', '.join(task.dependencies)}
        - Priority: {task.priority}
        - Estimated Lines: {task.estimated_lines}
        
        Project Context:
        - Project Name: {project_plan.project_name}
        - Project Type: {project_plan.project_type.value}
        - Features: {', '.join(project_plan.features)}
        - Technologies: {', '.join(project_plan.technologies)}
        
        Requirements:
        1. Generate complete, working code
        2. Follow best practices for {task.file_type}
        3. Include appropriate comments
        4. Handle errors appropriately
        5. Make it functional and testable
        6. Consider the dependencies listed
        
        Return ONLY the code content, nothing else. No explanations, no markdown formatting.
        """
        
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Clean up common LLM response issues
            content = self._clean_llm_response(content, task.file_type)
            
            quality = self._assess_code_quality(content, task.file_type)
            
            return GeneratedFile(
                file_path=task.file_path,
                content=content,
                file_type=task.file_type,
                quality=quality,
                lines_of_code=len(content.split('\n')),
                dependencies_used=task.dependencies,
                generation_time=time.time() - start_time
            )
            
        except Exception as e:
            print(f"LLM generation failed for {task.file_path}: {e}")
            return None
    
    def _clean_llm_response(self, content: str, file_type: str) -> str:
        """Clean up common issues in LLM-generated code"""
        
        # Remove markdown code blocks
        content = re.sub(r'```[\w]*\n?', '', content)
        content = re.sub(r'\n?```', '', content)
        
        # Remove explanatory text that sometimes appears
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip obvious explanation lines
            if any(phrase in line.lower() for phrase in [
                'here is the', 'this code', 'the following', 'note that',
                'make sure to', 'don\'t forget', 'remember to'
            ]):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _assess_code_quality(self, content: str, file_type: str) -> CodeQuality:
        """Assess the quality of generated code"""
        
        if not content or len(content.strip()) < 10:
            return CodeQuality.NEEDS_IMPROVEMENT
        
        # Basic quality checks
        score = 0
        
        # Check for appropriate length
        if len(content.split('\n')) >= 5:
            score += 1
        
        # Check for basic structure based on file type
        if file_type == "html" and "<html>" in content and "</html>" in content:
            score += 1
        elif file_type == "css" and "{" in content and "}" in content:
            score += 1
        elif file_type == "js" and ("function" in content or "const" in content or "let" in content):
            score += 1
        elif file_type == "py" and ("def " in content or "import " in content or "class " in content):
            score += 1
        
        # Check for comments
        if any(comment in content for comment in ["//", "#", "/*", "*"]):
            score += 1
        
        # Check for error handling
        if any(error_handle in content for error_handle in ["try:", "catch", "except", "error"]):
            score += 1
        
        # Determine quality based on score
        if score >= 4:
            return CodeQuality.EXCELLENT
        elif score >= 3:
            return CodeQuality.GOOD
        elif score >= 2:
            return CodeQuality.ACCEPTABLE
        else:
            return CodeQuality.NEEDS_IMPROVEMENT
    
    def _write_file_to_disk(self, generated_file: GeneratedFile, project_path: str):
        """Write generated file to disk"""
        
        full_path = os.path.join(project_path, generated_file.file_path)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(generated_file.content)
    
    def _optimize_task_execution(self, tasks: List[FileTask]) -> List[FileTask]:
        """Optimize the order of task execution"""
        
        # Sort by priority and dependencies
        return sorted(tasks, key=lambda x: (x.priority, len(x.dependencies)))
    
    # Template methods for common file types
    def _get_html_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate HTML template"""
        
        if "index" in task.file_path.lower():
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_plan.project_name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>{project_plan.project_name}</h1>
    </header>
    <main>
        <section id="app">
            <h2>Welcome to {project_plan.project_name}</h2>
            <p>{project_plan.description}</p>
            <!-- Main content will be generated here -->
        </section>
    </main>
    <footer>
        <p>&copy; 2024 {project_plan.project_name}</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>"""
        else:
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.splitext(task.file_path)[0].title()}</title>
</head>
<body>
    <h1>{task.description}</h1>
    <!-- Content for {task.file_path} -->
</body>
</html>"""
    
    def _get_css_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate CSS template"""
        
        return f"""/* {project_plan.project_name} Styles */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}}

header {{
    background-color: #333;
    color: white;
    padding: 1rem;
    text-align: center;
}}

main {{
    max-width: 1200px;
    margin: 2rem auto;
    padding: 1rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

footer {{
    text-align: center;
    padding: 1rem;
    background-color: #333;
    color: white;
    position: fixed;
    bottom: 0;
    width: 100%;
}}

/* Responsive design */
@media (max-width: 768px) {{
    main {{
        margin: 1rem;
        padding: 0.5rem;
    }}
}}"""
    
    def _get_js_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate JavaScript template"""
        
        return f"""// {project_plan.project_name} JavaScript
document.addEventListener('DOMContentLoaded', function() {{
    console.log('{project_plan.project_name} loaded successfully');
    
    // Main application logic
    const app = {{
        init: function() {{
            console.log('Initializing application...');
            this.setupEventListeners();
            this.loadInitialData();
        }},
        
        setupEventListeners: function() {{
            // Setup event listeners here
            console.log('Event listeners setup complete');
        }},
        
        loadInitialData: function() {{
            // Load initial data here
            console.log('Initial data loaded');
        }}
    }};
    
    // Initialize the application
    app.init();
}});"""
    
    def _get_python_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate Python template"""
        
        if "main" in task.file_path.lower() or "app" in task.file_path.lower():
            return f'''"""
{project_plan.project_name}
{project_plan.description}
"""

import sys
import os
from pathlib import Path

def main():
    """Main function for {project_plan.project_name}"""
    print(f"Starting {project_plan.project_name}...")
    print(f"Description: {project_plan.description}")
    
    # TODO: Implement main functionality
    print("Application functionality to be implemented")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())'''
        else:
            return f'''"""
{task.description}
"""

# TODO: Implement {task.file_path}
def main():
    """Main function"""
    pass

if __name__ == "__main__":
    main()'''
    
    def _get_json_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate JSON template"""
        
        return f'''{{
    "name": "{project_plan.project_name}",
    "version": "1.0.0",
    "description": "{project_plan.description}",
    "main": "index.html",
    "scripts": {{
        "start": "python -m http.server 8000",
        "test": "echo \\"Error: no test specified\\" && exit 1"
    }},
    "keywords": {project_plan.technologies},
    "author": "AI Coding Assistant",
    "license": "MIT"
}}'''
    
    def _get_markdown_template(self, task: FileTask, project_plan: ProjectPlan) -> str:
        """Generate Markdown template"""
        
        return f'''# {project_plan.project_name}

{project_plan.description}

## Features

{chr(10).join([f"- {feature}" for feature in project_plan.features])}

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {project_plan.project_name.lower().replace(" ", "-")}

# Install dependencies
npm install  # or pip install -r requirements.txt
```

## Usage

```bash
# Start the application
npm start  # or python main.py
```

## Technologies Used

{chr(10).join([f"- {tech}" for tech in project_plan.technologies])}

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
'''
