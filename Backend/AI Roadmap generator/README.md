# AI Learning Roadmap Generator

This tool generates personalized learning roadmaps for any topic using AI. It creates graphical representations of learning paths, breaking down complex subjects into manageable steps.

## Features
- Generate learning roadmaps for any topic
- Interactive graphical visualization
- AI-powered using Ollama
- Modern web interface

## Prerequisites
- Python 3.8+
- Node.js 14+
- Ollama installed and running locally

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies:
```bash
cd frontend
npm install
```

3. Start the backend server:
```bash
uvicorn main:app --reload
```

4. Start the frontend development server:
```bash
cd frontend
npm start
```

## Usage
1. Enter your desired learning topic in the input field
2. The AI will generate a personalized learning roadmap
3. View the interactive graphical representation of your learning path
4. Explore different branches and topics within your roadmap

## Technologies Used
- Backend: FastAPI, Python
- Frontend: React, TypeScript
- AI: Ollama
- Visualization: NetworkX, Matplotlib 