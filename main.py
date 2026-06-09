import os
import sys
import uvicorn

def main():
    # Set default directory to project root
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Run uvicorn pointing to the FastAPI app in src-backend
    sys.path.insert(0, os.path.join(project_dir, "src-backend"))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
