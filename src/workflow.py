from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass
import os
import json
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.planner_agent import PlannerAgent, ProjectPlan
from src.architect_agent import ArchitectAgent, ArchitecturePlan
from src.coder_agent import CoderAgent, CodeGenerationResult
from config import Config

class AgentState(TypedDict):
    user_request: str
    project_plan: Optional[ProjectPlan]
    architecture_plan: Optional[ArchitecturePlan]
    code_result: Optional[CodeGenerationResult]
    errors: List[str]
    warnings: List[str]
    current_step: str
    project_path: Optional[str]
    success: bool

@dataclass
class WorkflowResult:
    success: bool
    project_plan: Optional[ProjectPlan]
    architecture_plan: Optional[ArchitecturePlan]
    code_result: Optional[CodeGenerationResult]
    errors: List[str]
    warnings: List[str]
    project_path: Optional[str]
    total_time: float

class MultiAgentWorkflow:
    def __init__(self):
        self.planner = PlannerAgent()
        self.architect = ArchitectAgent()
        self.coder = CoderAgent()
        
        # Initialize LangGraph workflow
        self.workflow = self._create_workflow()
        self.memory = MemorySaver()
        
        # Ensure output directory exists
        Config.ensure_output_directory()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for agent coordination"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("architect", self._architect_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("validator", self._validator_node)
        workflow.add_node("finalizer", self._finalizer_node)
        
        # Define the workflow edges
        workflow.set_entry_point("planner")
        
        # Planner -> Architect
        workflow.add_edge("planner", "architect")
        
        # Architect -> Coder
        workflow.add_edge("architect", "coder")
        
        # Coder -> Validator
        workflow.add_edge("coder", "validator")
        
        # Validator -> Finalizer or back to Coder
        workflow.add_conditional_edges(
            "validator",
            self._should_retry_coding,
            {
                "retry": "coder",
                "finalize": "finalizer"
            }
        )
        
        # Finalizer -> END
        workflow.add_edge("finalizer", END)
        
        return workflow
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Planner agent node"""
        try:
            print("🎯 Planner Agent: Analyzing user request...")
            
            # Create project plan
            project_plan = self.planner.analyze_request(state["user_request"])
            
            # Validate the plan
            if not self.planner.validate_plan(project_plan):
                state["errors"].append("Invalid project plan generated")
                state["success"] = False
                return state
            
            state["project_plan"] = project_plan
            state["current_step"] = "planning_completed"
            
            print(f"✅ Planner: Created plan for {project_plan.project_name}")
            print(f"   Type: {project_plan.project_type.value}")
            print(f"   Files: {project_plan.estimated_files}")
            
            return state
            
        except Exception as e:
            state["errors"].append(f"Planner agent error: {str(e)}")
            state["success"] = False
            return state
    
    def _architect_node(self, state: AgentState) -> AgentState:
        """Architect agent node"""
        try:
            print("🏗️ Architect Agent: Creating detailed tasks...")
            
            if not state["project_plan"]:
                state["errors"].append("No project plan available for architect")
                state["success"] = False
                return state
            
            # Create architecture plan
            architecture_plan = self.architect.create_architecture_plan(state["project_plan"])
            
            # Validate the architecture plan
            if not self.architect.validate_architecture_plan(architecture_plan):
                state["errors"].append("Invalid architecture plan generated")
                state["success"] = False
                return state
            
            state["architecture_plan"] = architecture_plan
            state["current_step"] = "architecture_completed"
            
            print(f"✅ Architect: Created {len(architecture_plan.tasks)} tasks")
            print(f"   Build instructions: {len(architecture_plan.build_instructions)}")
            
            return state
            
        except Exception as e:
            state["errors"].append(f"Architect agent error: {str(e)}")
            state["success"] = False
            return state
    
    def _coder_node(self, state: AgentState) -> AgentState:
        """Coder agent node"""
        try:
            print("💻 Coder Agent: Generating code...")
            
            if not state["architecture_plan"]:
                state["errors"].append("No architecture plan available for coder")
                state["success"] = False
                return state
            
            # Create project directory
            project_name = state["project_plan"].project_name.lower().replace(" ", "-")
            project_path = os.path.join(Config.OUTPUT_DIRECTORY, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Generate all files
            code_result = self.coder.generate_files(state["architecture_plan"], project_path)
            
            state["code_result"] = code_result
            state["project_path"] = project_path
            state["current_step"] = "coding_completed"
            
            print(f"✅ Coder: Generated {len(code_result.generated_files)} files")
            print(f"   Quality: {self._get_quality_summary(code_result)}")
            
            if code_result.errors:
                state["warnings"].extend(code_result.errors)
            
            return state
            
        except Exception as e:
            state["errors"].append(f"Coder agent error: {str(e)}")
            state["success"] = False
            return state
    
    def _validator_node(self, state: AgentState) -> AgentState:
        """Validator node to check results"""
        try:
            print("🔍 Validator: Checking results...")
            
            if not state["code_result"]:
                state["errors"].append("No code result available for validation")
                state["success"] = False
                return state
            
            code_result = state["code_result"]
            
            # Check if generation was successful
            if not code_result.success:
                state["errors"].extend(code_result.errors)
                state["success"] = False
                return state
            
            # Check file quality
            low_quality_files = [
                f for f in code_result.generated_files
                if f.quality.value in ["needs_improvement", "acceptable"]
            ]
            
            if low_quality_files:
                state["warnings"].append(f"{len(low_quality_files)} files have low quality")
            
            # Check if all expected files were generated
            expected_files = len(state["architecture_plan"].tasks)
            actual_files = len(code_result.generated_files)
            
            if actual_files < expected_files:
                state["warnings"].append(f"Only {actual_files}/{expected_files} files generated")
            
            state["current_step"] = "validation_completed"
            
            print(f"✅ Validator: Validation completed")
            print(f"   Files generated: {actual_files}/{expected_files}")
            print(f"   Warnings: {len(state['warnings'])}")
            
            return state
            
        except Exception as e:
            state["errors"].append(f"Validator error: {str(e)}")
            state["success"] = False
            return state
    
    def _finalizer_node(self, state: AgentState) -> AgentState:
        """Finalizer node to complete the workflow"""
        try:
            print("🎉 Finalizer: Completing workflow...")
            
            # Create project summary
            if state["project_path"] and state["project_plan"]:
                self._create_project_summary(state)
            
            state["current_step"] = "completed"
            state["success"] = True
            
            print("✅ Finalizer: Workflow completed successfully!")
            
            return state
            
        except Exception as e:
            state["errors"].append(f"Finalizer error: {str(e)}")
            state["success"] = False
            return state
    
    def _should_retry_coding(self, state: AgentState) -> str:
        """Determine if coding should be retried"""
        
        if not state["success"]:
            return "finalize"
        
        if state["code_result"] and not state["code_result"].success:
            # Check if we should retry (limit retries to avoid infinite loops)
            if len(state["warnings"]) < 3:  # Max 3 retries
                state["warnings"].append("Retrying code generation...")
                return "retry"
        
        return "finalize"
    
    def _get_quality_summary(self, code_result: CodeGenerationResult) -> str:
        """Get a summary of code quality"""
        if not code_result.generated_files:
            return "No files generated"
        
        quality_counts = {}
        for file in code_result.generated_files:
            quality = file.quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        return ", ".join([f"{count} {quality}" for quality, count in quality_counts.items()])
    
    def _create_project_summary(self, state: AgentState):
        """Create a summary file for the generated project"""
        
        try:
            summary_path = os.path.join(state["project_path"], "PROJECT_SUMMARY.md")
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"""# {state['project_plan'].project_name}

## Project Summary

**Description**: {state['project_plan'].description}
**Type**: {state['project_plan'].project_type.value}
**Complexity**: {state['project_plan'].complexity}
**Generated Files**: {len(state['code_result'].generated_files) if state['code_result'] else 0}

## Features

""" + "\n".join([f"- {feature}" for feature in state['project_plan'].features]) + f"""

## Technologies Used

""" + "\n".join([f"- {tech}" for tech in state['project_plan'].technologies]) + """

## Generated Files

""")
                
                if state['code_result'] and state['code_result'].generated_files:
                    for file in state['code_result'].generated_files:
                        f.write(f"- **{file.file_path}** ({file.file_type}, {file.lines_of_code} lines, {file.quality.value})\n")
                
                f.write(f"""
## Build Instructions

""" + "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(state['architecture_plan'].build_instructions)]) + """

## Test Instructions

""" + "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(state['architecture_plan'].test_instructions)]) + """

## Generation Information

- Generated by: Multi-Agent Coding Assistant
- Generation time: {state['code_result'].total_generation_time:.2f}s if state['code_result'] else 'N/A'}
- Warnings: {len(state['warnings'])}
- Errors: {len(state['errors'])}

---
*This project was automatically generated by AI agents. Please review and test before use.*
""")
            
        except Exception as e:
            print(f"Warning: Could not create project summary: {e}")
    
    def execute_workflow(self, user_request: str) -> WorkflowResult:
        """Execute the complete multi-agent workflow"""
        
        start_time = time.time()
        
        # Initialize state
        initial_state = AgentState(
            user_request=user_request,
            project_plan=None,
            architecture_plan=None,
            code_result=None,
            errors=[],
            warnings=[],
            current_step="initialized",
            project_path=None,
            success=False
        )
        
        try:
            # Create the compiled workflow
            app = self.workflow.compile(checkpointer=self.memory)
            
            # Execute the workflow
            config = {"configurable": {"thread_id": f"workflow_{int(time.time())}"}}
            
            print("🚀 Starting Multi-Agent Coding Assistant Workflow...")
            print(f"📝 Request: {user_request}")
            print("-" * 50)
            
            # Run the workflow
            result = app.invoke(initial_state, config=config)
            
            total_time = time.time() - start_time
            
            print("-" * 50)
            print(f"⏱️ Total workflow time: {total_time:.2f}s")
            
            return WorkflowResult(
                success=result["success"],
                project_plan=result["project_plan"],
                architecture_plan=result["architecture_plan"],
                code_result=result["code_result"],
                errors=result["errors"],
                warnings=result["warnings"],
                project_path=result["project_path"],
                total_time=total_time
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ Workflow failed: {str(e)}")
            
            return WorkflowResult(
                success=False,
                project_plan=None,
                architecture_plan=None,
                code_result=None,
                errors=[f"Workflow execution error: {str(e)}"],
                warnings=[],
                project_path=None,
                total_time=total_time
            )
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status and statistics"""
        return {
            "agents_initialized": 3,
            "workflow_nodes": ["planner", "architect", "coder", "validator", "finalizer"],
            "output_directory": Config.OUTPUT_DIRECTORY,
            "llm_model": Config.LLM_MODEL,
            "max_retries": Config.MAX_RETRIES
        }
