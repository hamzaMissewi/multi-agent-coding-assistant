import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-3-70b-8192")
    
    # Application Settings
    APP_HOST = os.getenv("APP_HOST", "localhost")
    APP_PORT = int(os.getenv("APP_PORT", "8501"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # Project Generation
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "./generated_projects")
    MAX_PROJECT_SIZE_MB = int(os.getenv("MAX_PROJECT_SIZE_MB", "100"))
    
    # Agent Settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    
    @classmethod
    def validate(cls):
        required_vars = ["GROQ_API_KEY"]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def ensure_output_directory(cls):
        os.makedirs(cls.OUTPUT_DIRECTORY, exist_ok=True)
        return cls.OUTPUT_DIRECTORY
