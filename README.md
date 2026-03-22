# Multi-Agent Coding Assistant

An AI-powered coding assistant that uses multiple agents to convert natural language requests into working software projects.

## 🚀 Features

- **Multi-Agent Architecture**: Uses specialized agents for planning, architecture, and coding
- **LangGraph Workflow**: Coordinated agent execution with state management
- **Intelligent Planning**: Analyzes user requests and creates comprehensive project plans
- **Code Generation**: Generates high-quality, production-ready code
- **Project Execution**: Run and test generated projects directly
- **Download Support**: Export projects as ZIP files
- **Interactive Interface**: Beautiful Streamlit dashboard

## 🤖 Agent System

### Planner Agent
- Analyzes user requests and requirements
- Determines project type and technology stack
- Creates comprehensive project plans
- Estimates complexity and file count

### Architect Agent  
- Breaks down plans into specific coding tasks
- Designs optimal file structures
- Determines task dependencies and execution order
- Provides build and test instructions

### Coder Agent
- Generates high-quality code for each file
- Uses templates for common patterns
- Applies best practices for each technology
- Assesses code quality automatically

## 🛠️ Tech Stack

- **Agent Framework**: LangGraph for workflow orchestration
- **LLM**: Groq Cloud (Qwen 3, Kimi K2)
- **Frontend**: Streamlit dashboard
- **Backend**: Python with FastAPI
- **Code Generation**: Template-based + LLM fallback

## 📦 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd multi-agent-coding-assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the application**
```bash
streamlit run streamlit_app.py --server.port 8501
```

## ⚙️ Configuration

### Environment Variables

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=qwen-3-70b-8192

# Application Settings
APP_HOST=localhost
APP_PORT=8501
OUTPUT_DIRECTORY=./generated_projects
```

### Required API Keys

- **Groq API Key**: Get from [Groq Console](https://console.groq.com/)
- Free tier available with generous limits

## 🎯 Usage

### Basic Usage

1. **Describe your project**: Enter a natural language description of what you want to build
2. **Configure options**: Set project name, complexity, and preferences
3. **Generate**: Click the generate button to start the multi-agent workflow
4. **Review**: Check the generated files and code quality
5. **Download**: Export the project as a ZIP file
6. **Run**: Execute the project directly from the interface

### Example Prompts

- "Build a calculator web app with add, subtract, multiply and divide buttons"
- "Create a REST API for managing a todo list"
- "Make a command-line tool for file conversion"
- "Build a data analysis dashboard with charts"
- "Create a simple blog with Flask"

## 🏗️ Project Types Supported

### Web Applications
- HTML/CSS/JavaScript
- React applications
- Vue.js applications
- Flask/FastAPI backends
- Full-stack applications

### APIs
- REST APIs with FastAPI
- GraphQL APIs
- Microservices
- API documentation

### CLI Tools
- Python command-line tools
- Node.js CLI applications
- Utility scripts
- Data processing tools

### Data Analysis
- Jupyter notebooks
- Data visualization dashboards
- Statistical analysis tools
- Report generators

## 📊 Workflow Process

1. **Request Analysis**: User input is parsed and understood
2. **Project Planning**: Comprehensive plan with technologies and structure
3. **Architecture Design**: Detailed tasks and dependencies
4. **Code Generation**: High-quality code for each file
5. **Quality Assurance**: Code validation and quality checks
6. **Project Packaging**: File organization and documentation
7. **Delivery**: Download and execution options

## 🎨 Interface Features

### Generation Tab
- Natural language input
- Project configuration options
- Real-time progress tracking
- Results visualization
- Download controls

### History Tab
- Previous generations
- Success metrics
- Project statistics
- Re-download options

### Settings Tab
- Configuration validation
- System information
- Performance metrics
- Debug options

## 🔍 Code Quality

### Quality Assessment
- **Excellent**: Complete, well-structured, documented
- **Good**: Functional with minor improvements needed
- **Acceptable**: Basic functionality present
- **Needs Improvement**: Incomplete or problematic

### Validation Checks
- Syntax validation
- Structure verification
- Dependency checking
- Best practices compliance

## 🚀 Project Execution

### Supported Project Types
- **Node.js**: npm install, npm start
- **Python**: pip install, python main.py
- **Static**: HTTP server, direct browser opening
- **Docker**: docker build, docker run

### Development Server
- Automatic port detection
- Server status monitoring
- Browser integration
- Process management

## 📁 Project Structure

```
multi-agent-coding-assistant/
├── src/
│   ├── planner_agent.py      # Project planning logic
│   ├── architect_agent.py    # Architecture design
│   ├── coder_agent.py        # Code generation
│   ├── workflow.py          # Agent coordination
│   └── project_executor.py  # Project execution
├── streamlit_app.py         # Main application
├── config.py              # Configuration management
├── requirements.txt        # Dependencies
└── .env.example          # Environment template
```

## 🔄 Advanced Features

### Retry Logic
- Automatic retry on failed generation
- Exponential backoff
- Quality improvement iterations
- Error recovery mechanisms

### Template System
- Pre-built templates for common patterns
- Language-specific best practices
- Customizable templates
- Fallback to LLM generation

### Memory Management
- Session state persistence
- Generation history
- Project caching
- Performance optimization

## 🛠️ Development

### Running in Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run streamlit_app.py --server.port 8501 --server.headless false
```

### Code Structure
- **Modular Design**: Each agent is a separate module
- **State Management**: LangGraph handles workflow state
- **Error Handling**: Comprehensive error handling throughout
- **Logging**: Detailed logging for debugging

### Adding New Agents
1. Create agent class in `src/`
2. Implement required methods
3. Add to workflow in `workflow.py`
4. Update interface as needed

## 🐛 Troubleshooting

### Common Issues

**Generation Fails**
- Check API key configuration
- Verify internet connection
- Try simpler request
- Check error logs

**Code Quality Issues**
- Increase complexity setting
- Provide more specific requirements
- Review generated code manually
- Regenerate with different settings

**Execution Problems**
- Check project dependencies
- Verify runtime environment
- Review error messages
- Try manual commands

### Debug Mode
Enable debug mode in `.env`:
```env
DEBUG_MODE=true
```

## 📈 Performance

### Optimization Features
- Parallel agent execution
- Template caching
- Lazy loading
- Memory management

### Metrics
- Generation time tracking
- Success rate monitoring
- Code quality metrics
- Resource usage monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Add comprehensive documentation
- Include error handling
- Test thoroughly

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **LangGraph**: Agent workflow orchestration
- **Groq**: LLM hosting and inference
- **Streamlit**: Beautiful web interface
- **OpenAI**: LLM integration patterns

---

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide
- Join the community discussions

*Built with ❤️ by the Multi-Agent Coding Assistant team*
