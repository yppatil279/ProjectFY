# AI Quiz Generator

This is an interactive quiz generator that uses Ollama to create custom quizzes on any topic. The application uses the Mistral model through Ollama to generate multiple-choice questions.

## Prerequisites

- Python 3.7 or higher
- Ollama installed and running (version 0.6.4 or higher)
- The Mistral model pulled in Ollama

## Setup

1. Make sure Ollama is running on your system
2. Pull the Mistral model if you haven't already:
   ```
   ollama pull mistral
   ```
3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the quiz generator:
   ```
   python quiz_generator.py
   ```
2. Enter a topic when prompted
3. Choose how many questions you want
4. Answer the questions by selecting A, B, C, or D
5. Get your score and explanations for each answer
6. Type 'quit' to exit the program

## Features

- Generate quizzes on any topic
- Multiple choice questions with 4 options
- Immediate feedback on answers
- Explanations for correct answers
- Score tracking
- Beautiful console interface with color coding 