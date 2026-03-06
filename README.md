├──├──├──│├──│├──│├──│└──└──└──# ai-coding-mentor
🧑‍💻 AI Coding Mentor - Local Code Teacher powered by Llama. Explains code line by line, suggests improvements, generates tests, analyzes complexity, and debugs with an "Explain Like I'm 5" mode.

## Features
- Explain Code - Line-by-line teacher-style explanations
- - Suggest Improvements - Code quality, performance, best practices
  - - Generate Tests - Auto-generate pytest unit tests
    - - Complexity Analysis - Big-O time/space with AST metrics
      - - Debug Suggestions - Find and fix bugs step-by-step
        - - ELI5 Mode - "Explain Like I'm 5" kid-friendly mode
          - - Multi-language support (Python, JavaScript, Java, C++, Go)
           
            - ## Tech Stack
            - - AI: Llama 3 via Ollama (local, private, offline)
              - - Backend: Python + FastAPI
                - - AST Parser: Python ast module for code structure analysis
                  - - Frontend: Vanilla HTML/CSS/JS with dark theme
                   
                    - ## Quick Start
                   
                    - 1. Install Ollama: https://ollama.ai then run: ollama pull llama3
                      2. 2. Clone repo: git clone https://github.com/PranayMahendrakar/ai-coding-mentor.git
                         3. 3. Install deps: pip install -r requirements.txt
                            4. 4. Run: python main.py
                               5. 5. Open: http://localhost:8000
                                 
                                  6. ## API Endpoints
                                  7. - POST /api/explain - Explain code line by line
                                     - - POST /api/improve - Suggest improvements
                                       - - POST /api/generate-tests - Generate unit tests
                                         - - POST /api/complexity - Analyze Big-O complexity
                                           - - POST /api/debug - Debug suggestions
                                             - - POST /api/analyze-all - Run all analyses at once
                                               - - GET /api/health - Check Llama connection status
                                                
                                                 - ## Project Structure
                                                 - - main.py - FastAPI application entry point
                                                   - - requirements.txt - Python dependencies
                                                     - - mentor/__init__.py - Package init
                                                       - - mentor/llama_client.py - Ollama/Llama AI integration
                                                         - - mentor/ast_parser.py - Python AST code analysis
                                                           - - mentor/code_analyzer.py - Core analysis engine
                                                             - - static/index.html - Web UI
                                                              
                                                               - ## Mock Mode
                                                               - Works without Ollama - returns mock responses. Install Ollama for full AI analysis.
                                                              
                                                               - ## License
                                                               - MIT
