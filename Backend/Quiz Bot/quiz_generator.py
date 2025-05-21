import requests
import json
import re
import os
import time
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import PyPDF2
import docx
import textwrap
import tkinter as tk
from tkinter import filedialog

console = Console()

class QuizGenerator:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        self.console = Console()
        self.supported_extensions = {'.txt', '.pdf', '.docx'}
        # Initialize tkinter root window (hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window

    def select_file(self):
        """Open a file dialog to select a file."""
        filetypes = [
            ("All supported files", "*.txt;*.pdf;*.docx"),
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=filetypes
        )
        return file_path if file_path else None

    def clean_json_response(self, text):
        try:
            # Remove any markdown code block markers
            text = re.sub(r'```json\s*|\s*```', '', text)
            # Remove any leading/trailing whitespace
            text = text.strip()
            # Find the first [ and last ] to extract just the JSON array
            start = text.find('[')
            end = text.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("Could not find JSON array in response")
            json_str = text[start:end]
            # Try to parse it to validate JSON format
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing response: {str(e)}")

    def read_file_content(self, file_path):
        """Read content from different file types."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {extension}")

        try:
            if extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif extension == '.pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            elif extension == '.docx':
                doc = docx.Document(file_path)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    def validate_question(self, q, i):
        """Validate a single question based on its type."""
        if 'type' not in q:
            raise ValueError(f"Question {i} is missing type field")
        
        if not isinstance(q['question'], str) or not q['question'].strip():
            raise ValueError(f"Question {i} has invalid question text")
        
        if 'explanation' not in q or not isinstance(q['explanation'], str) or not q['explanation'].strip():
            raise ValueError(f"Question {i} is missing or has invalid explanation")
        
        if q['type'] == 'mcq':
            if not all(k in q for k in ['options', 'correct_answer']):
                raise ValueError(f"MCQ {i} is missing required fields")
            if not isinstance(q['options'], list) or len(q['options']) != 4:
                raise ValueError(f"MCQ {i} must have exactly 4 options")
            if q['correct_answer'] not in ['A', 'B', 'C', 'D']:
                raise ValueError(f"MCQ {i} has invalid correct_answer: {q['correct_answer']}")
        
        elif q['type'] == 'fill_blank':
            if 'correct_answer' not in q:
                raise ValueError(f"Fill in the blank {i} is missing correct_answer")
            if '_____' not in q['question']:
                raise ValueError(f"Fill in the blank {i} must contain _____ to indicate the blank")
        
        elif q['type'] == 'true_false':
            if 'correct_answer' not in q:
                raise ValueError(f"True/False {i} is missing correct_answer")
            if q['correct_answer'] not in ['True', 'False']:
                raise ValueError(f"True/False {i} has invalid correct_answer: {q['correct_answer']}")
        
        else:
            raise ValueError(f"Question {i} has invalid type: {q['type']}")

    def generate_questions_with_retry(self, prompt, max_retries=3):
        """Generate questions with retry logic for failed attempts."""
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    self.base_url,
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Clean and parse the response
                json_str = self.clean_json_response(result['response'])
                questions = json.loads(json_str)
                
                # Validate each question
                valid_questions = []
                for i, q in enumerate(questions, 1):
                    try:
                        self.validate_question(q, i)
                        valid_questions.append(q)
                    except ValueError as e:
                        console.print(f"[yellow]Warning: {str(e)}. Skipping question {i}.[/yellow]")
                
                # Filter out invalid questions
                valid_questions = [q for q in valid_questions if all(
                    k in q for k in ['type', 'question', 'explanation']
                )]
                
                # Extract question types from the prompt
                import re
                types_match = re.search(r'Include ONLY the following question types: (.*?)(?:\n|$)', prompt)
                if types_match:
                    selected_types = [t.strip() for t in types_match.group(1).split(',')]
                    # Strictly filter questions to only include the selected types
                    valid_questions = [q for q in valid_questions if q['type'] in selected_types]
                    
                    # If we don't have enough questions of the right type, retry
                    if len(valid_questions) < self.num_questions and attempt < max_retries:
                        console.print(f"[yellow]Not enough questions of the selected type(s). Retrying (attempt {attempt+1}/{max_retries})...[/yellow]")
                        time.sleep(1)
                        continue
                
                if not valid_questions:
                    if attempt < max_retries:
                        console.print(f"[yellow]No valid questions generated. Retrying (attempt {attempt+1}/{max_retries})...[/yellow]")
                        time.sleep(1)  # Wait a bit before retrying
                        continue
                    else:
                        raise ValueError("No valid questions were generated after multiple attempts")
                
                return valid_questions
                
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    console.print(f"[yellow]Connection error. Retrying (attempt {attempt+1}/{max_retries})...[/yellow]")
                    time.sleep(1)
                    continue
                else:
                    console.print("[red]Error: Could not connect to Ollama. Make sure Ollama is running.[/red]")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    console.print(f"[yellow]Request error: {str(e)}. Retrying (attempt {attempt+1}/{max_retries})...[/yellow]")
                    time.sleep(1)
                    continue
                else:
                    console.print(f"[red]Error communicating with Ollama: {str(e)}[/red]")
                    return None
            except Exception as e:
                if attempt < max_retries:
                    console.print(f"[yellow]Error: {str(e)}. Retrying (attempt {attempt+1}/{max_retries})...[/yellow]")
                    time.sleep(1)
                    continue
                else:
                    console.print(f"[red]Error generating quiz: {str(e)}[/red]")
                    return None

    def generate_quiz_from_content(self, content, num_questions=5, question_types=None):
        """Generate quiz from provided content."""
        if question_types is None:
            question_types = ["mcq", "fill_blank", "true_false"]
        
        # Handle random option
        if "random" in question_types:
            import random
            all_types = ["mcq", "fill_blank", "true_false"]
            question_types = [random.choice(all_types)]
            console.print(f"[yellow]Randomly selected question type: {question_types[0]}[/yellow]")
        
        # Store num_questions for use in generate_questions_with_retry
        self.num_questions = num_questions
        
        prompt = f"""Create a quiz based on the following content with {num_questions} questions.
        Content: {content[:2000]}  # Limiting content length to avoid token limits
        
        Return a JSON array with questions of different types. Each question should have a "type" field indicating its type.
        For each type, use this structure:
        
        For Multiple Choice Questions (type: "mcq"):
        {{
            "type": "mcq",
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": "B",
            "explanation": "2 + 2 equals 4, which is option B"
        }}
        
        For Fill in the Blanks (type: "fill_blank"):
        {{
            "type": "fill_blank",
            "question": "The capital of France is _____.",
            "correct_answer": "Paris",
            "explanation": "Paris is the capital city of France."
        }}
        
        For True/False Questions (type: "true_false"):
        {{
            "type": "true_false",
            "question": "The Earth is flat.",
            "correct_answer": "False",
            "explanation": "The Earth is an oblate spheroid, not flat."
        }}
        
        Rules:
        1. Include ONLY the following question types: {', '.join(question_types)}
        2. For MCQs, each question must have exactly 4 options
        3. For MCQs, the correct_answer must be exactly "A", "B", "C", or "D" (uppercase)
        4. For fill in the blanks, use _____ to indicate the blank
        5. For true/false, correct_answer must be exactly "True" or "False"
        6. Return only the JSON array, no other text
        7. Make questions challenging but fair
        8. Ensure explanations are clear and concise
        9. Do not include any markdown formatting or code blocks
        10. Questions should be based on the provided content
        11. IMPORTANT: Every question MUST have a "type", "question", and "explanation" field
        12. For True/False questions, the correct_answer MUST be exactly "True" or "False" (case-sensitive)"""

        return self.generate_questions_with_retry(prompt)

    def generate_quiz(self, topic, num_questions=5, question_types=None):
        """Generate quiz from a topic."""
        if question_types is None:
            question_types = ["mcq", "fill_blank", "true_false"]
        
        # Handle random option
        if "random" in question_types:
            import random
            all_types = ["mcq", "fill_blank", "true_false"]
            question_types = [random.choice(all_types)]
            console.print(f"[yellow]Randomly selected question type: {question_types[0]}[/yellow]")
        
        # Store num_questions for use in generate_questions_with_retry
        self.num_questions = num_questions
        
        prompt = f"""Create a quiz about {topic} with {num_questions} questions.
        Return a JSON array with questions of different types. Each question should have a "type" field indicating its type.
        For each type, use this structure:
        
        For Multiple Choice Questions (type: "mcq"):
        {{
            "type": "mcq",
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": "B",
            "explanation": "2 + 2 equals 4, which is option B"
        }}
        
        For Fill in the Blanks (type: "fill_blank"):
        {{
            "type": "fill_blank",
            "question": "The capital of France is _____.",
            "correct_answer": "Paris",
            "explanation": "Paris is the capital city of France."
        }}
        
        For True/False Questions (type: "true_false"):
        {{
            "type": "true_false",
            "question": "The Earth is flat.",
            "correct_answer": "False",
            "explanation": "The Earth is an oblate spheroid, not flat."
        }}
        
        Rules:
        1. Include ONLY the following question types: {', '.join(question_types)}
        2. For MCQs, each question must have exactly 4 options
        3. For MCQs, the correct_answer must be exactly "A", "B", "C", or "D" (uppercase)
        4. For fill in the blanks, use _____ to indicate the blank
        5. For true/false, correct_answer must be exactly "True" or "False"
        6. Return only the JSON array, no other text
        7. Make questions challenging but fair
        8. Ensure explanations are clear and concise
        9. Do not include any markdown formatting or code blocks
        10. IMPORTANT: Every question MUST have a "type", "question", and "explanation" field
        11. For True/False questions, the correct_answer MUST be exactly "True" or "False" (case-sensitive)"""

        return self.generate_questions_with_retry(prompt)

    def display_quiz(self, questions):
        if not questions:
            console.print("[red]No questions generated.[/red]")
            return

        score = 0
        total_questions = len(questions)

        for i, q in enumerate(questions, 1):
            console.print(Panel(f"[bold blue]Question {i}/{total_questions}[/bold blue]"))
            console.print(f"[bold]{q['question']}[/bold]")
            
            if q['type'] == 'mcq':
                for j, option in enumerate(q['options'], 1):
                    console.print(f"{chr(64+j)}. {option}")
                
                # Allow both uppercase and lowercase answers
                answer = Prompt.ask("Your answer", choices=["a", "b", "c", "d", "A", "B", "C", "D"])
                
                # Convert to uppercase for comparison
                if answer.upper() == q['correct_answer']:
                    console.print("[green]Correct![/green]")
                    score += 1
                else:
                    console.print(f"[red]Incorrect. The correct answer was {q['correct_answer']}[/red]")
            
            elif q['type'] == 'fill_blank':
                answer = Prompt.ask("Your answer")
                
                # Case-insensitive comparison for fill in the blanks
                if answer.lower().strip() == q['correct_answer'].lower().strip():
                    console.print("[green]Correct![/green]")
                    score += 1
                else:
                    console.print(f"[red]Incorrect. The correct answer was {q['correct_answer']}[/red]")
            
            elif q['type'] == 'true_false':
                answer = Prompt.ask("Your answer", choices=["true", "false", "True", "False"])
                
                # Case-insensitive comparison for true/false
                if answer.lower() == q['correct_answer'].lower():
                    console.print("[green]Correct![/green]")
                    score += 1
                else:
                    console.print(f"[red]Incorrect. The correct answer was {q['correct_answer']}[/red]")
            
            console.print(f"[italic]{q['explanation']}[/italic]")
            console.print("")

        console.print(Panel(f"[bold]Final Score: {score}/{total_questions}[/bold]"))

def main():
    console.print(Panel("[bold blue]Welcome to the AI Quiz Generator![/bold blue]"))
    
    generator = QuizGenerator()
    
    while True:
        console.print("\n[bold]Choose quiz generation method:[/bold]")
        console.print("1. Generate from topic")
        console.print("2. Generate from file")
        console.print("3. Generate from text input")
        console.print("4. Quit")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"])
        
        if choice == "4":
            break
            
        num_questions = int(Prompt.ask("How many questions would you like?", default="5"))
        
        # Ask for question types
        console.print("\n[bold]Select question types:[/bold]")
        console.print("1. Multiple Choice (mcq)")
        console.print("2. Fill in the Blanks (fill_blank)")
        console.print("3. True/False (true_false)")
        console.print("4. Random (any type)")
        console.print("5. All types (mixed)")
        
        type_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])
        question_types = []
        
        if type_choice == "1":
            question_types = ["mcq"]
        elif type_choice == "2":
            question_types = ["fill_blank"]
        elif type_choice == "3":
            question_types = ["true_false"]
        elif type_choice == "4":
            # Random option - will be handled in the generate_quiz methods
            question_types = ["random"]
        elif type_choice == "5":
            question_types = ["mcq", "fill_blank", "true_false"]
        
        if choice == "1":
            topic = Prompt.ask("Enter a topic for the quiz")
            console.print("\n[bold]Generating quiz from topic...[/bold]")
            questions = generator.generate_quiz(topic, num_questions, question_types)
        
        elif choice == "2":
            console.print("\n[bold]Please select a file in the file dialog...[/bold]")
            file_path = generator.select_file()
            
            if not file_path:
                console.print("[yellow]No file selected. Skipping...[/yellow]")
                continue
                
            try:
                content = generator.read_file_content(file_path)
                console.print(f"\n[bold]Generating quiz from file: {os.path.basename(file_path)}[/bold]")
                questions = generator.generate_quiz_from_content(content, num_questions, question_types)
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                continue
        
        elif choice == "3":
            console.print("\nEnter your text (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            content = "\n".join(lines[:-1])  # Remove the last empty line
            console.print("\n[bold]Generating quiz from text...[/bold]")
            questions = generator.generate_quiz_from_content(content, num_questions, question_types)
        
        if questions:
            generator.display_quiz(questions)
        
        console.print("\n")

if __name__ == "__main__":
    main() 