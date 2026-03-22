#!/usr/bin/env python3

print("Testing imports...")

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    print("✓ langchain_core.messages imported successfully")
except ImportError as e:
    print(f"✗ Failed to import langchain_core.messages: {e}")

try:
    from langchain_groq import ChatGroq
    print("✓ langchain_groq imported successfully")
except ImportError as e:
    print(f"✗ Failed to import langchain_groq: {e}")

try:
    from src.planner_agent import PlannerAgent, ProjectPlan
    print("✓ planner_agent imported successfully")
except ImportError as e:
    print(f"✗ Failed to import planner_agent: {e}")

try:
    from src.architect_agent import ArchitectAgent, ArchitecturePlan
    print("✓ architect_agent imported successfully")
except ImportError as e:
    print(f"✗ Failed to import architect_agent: {e}")

try:
    from src.coder_agent import CoderAgent, CodeGenerationResult
    print("✓ coder_agent imported successfully")
except ImportError as e:
    print(f"✗ Failed to import coder_agent: {e}")

try:
    from src.workflow import MultiAgentWorkflow, WorkflowResult
    print("✓ workflow imported successfully")
except ImportError as e:
    print(f"✗ Failed to import workflow: {e}")

print("Import test completed!")
