from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio
from celery import Celery
from sqlalchemy import create_engine, Column, String, Integer, Base
from sqlalchemy.orm import sessionmaker

from crewai import Crew, Process
from agents import doctor
from task import help_patients

# Initialize FastAPI app
app = FastAPI(title="Blood Test Report Analyser")

# Initialize Celery
celery_app = Celery(
    "blood_test_analyser",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Database setup
DATABASE_URL = "sqlite:///./blood_test_analyser.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    analysis = Column(String)
    file_name = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_crew(query: str, file_path: str="data/sample.pdf"):
    """To run the whole crew"""
    medical_crew = Crew(
        agents=[doctor],
        tasks=[help_patients],
        process=Process.sequential,
    )
    result = medical_crew.kickoff({'query': query, 'file_path': file_path})
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Blood Test Report Analyser API is running"}

@app.post("/analyze")
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarise my Blood Test Report")
):
    """Analyze blood test report and provide comprehensive health recommendations"""
    
    # Generate unique filename to avoid conflicts
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate query
        if query == "" or query is None:
            query = "Summarise my Blood Test Report"
            
        # Send task to Celery worker
        task = analyze_blood_report_task.delay(query=query.strip(), file_path=file_path, file_name=file.filename)
        
        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Your request is being processed. Use the task ID to check the status."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing blood report: {str(e)}")
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")

@celery_app.task
def analyze_blood_report_task(query: str, file_path: str, file_name: str):
    """Celery task to process blood report"""
    try:
        response = run_crew(query=query, file_path=file_path)
        
        # Save result to database
        db = SessionLocal()
        analysis_result = AnalysisResult(
            query=query,
            analysis=str(response),
            file_name=file_name
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
        return {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file_name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a Celery task"""
    task_result = celery_app.AsyncResult(task_id)
    if task_result.state == "SUCCESS":
        return {"status": "success", "result": task_result.result}
    elif task_result.state == "FAILURE":
        return {"status": "error", "message": str(task_result.result)}
    else:
        return {"status": task_result.state, "message": "Task is still processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)