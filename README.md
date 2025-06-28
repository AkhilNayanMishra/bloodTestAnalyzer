# Blood Test Report Analyser

## Overview
This project analyzes blood test reports and provides health recommendations using AI agents.

## Setup Instructions

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd blood-test-analyser-debug
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the application:
   ```sh
   python main.py
   ```

## API Documentation

### Endpoints

#### `GET /`
- **Description**: Health check endpoint.
- **Response**:
  ```json
  {"message": "Blood Test Report Analyser API is running"}
  ```

#### `POST /analyze`
- **Description**: Analyze blood test report and provide recommendations.
- **Parameters**:
  - `file`: PDF file of the blood test report.
  - `query`: Query string (optional).
- **Response**:
  ```json
  {
    "status": "success",
    "query": "<query>",
    "analysis": "<analysis>",
    "file_processed": "<file_name>"
  }
  ```

## Bugs Fixed
1. Undefined `llm` in `agents.py`.
2. Incorrect `requirements.txt` path in README.md.
3. Missing `PDFLoader` import in `tools.py`.
4. Agent mismatch in `task.py`.
5. Unused `file_path` parameter in `run_crew`.
6. Potential race condition in file cleanup.