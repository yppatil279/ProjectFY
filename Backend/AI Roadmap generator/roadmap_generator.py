import requests
import json
import os
import time

def generate_roadmap(topic):
    """
    Generate a learning roadmap for the given topic using Ollama.
    """
    print(f"\nGenerating roadmap for '{topic}'...\n")
    
    # Create a prompt that instructs the model to generate a structured roadmap
    prompt = f"""Create a detailed learning roadmap for {topic}. 
    Structure it as a JSON object with the following format:
    {{
        "title": "Learning Roadmap for {topic}",
        "description": "A comprehensive guide to learning {topic}",
        "steps": [
            {{
                "level": 1,
                "title": "Step 1 Title",
                "description": "Description of what to learn in this step",
                "topics": ["Subtopic 1", "Subtopic 2", "Subtopic 3"],
                "resources": ["Resource 1", "Resource 2"]
            }},
            {{
                "level": 2,
                "title": "Step 2 Title",
                "description": "Description of what to learn in this step",
                "topics": ["Subtopic 1", "Subtopic 2"],
                "resources": ["Resource 1", "Resource 2"]
            }}
        ],
        "estimated_time": "X weeks/months",
        "prerequisites": ["Prerequisite 1", "Prerequisite 2"]
    }}
    
    Include 5-7 main steps with 2-4 subtopics each. Make it comprehensive but manageable.
    Ensure the response is valid JSON with proper quotes and formatting."""
    
    try:
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            print(f"Error: Failed to get response from Ollama (Status code: {response.status_code})")
            return None
        
        # Parse the response
        result = response.json()
        
        # Clean the response text to ensure it's valid JSON
        response_text = result["response"].strip()
        # Remove any markdown code block markers if present
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            roadmap_data = json.loads(response_text)
            return roadmap_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Problematic response text: {response_text}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def display_roadmap(roadmap):
    """
    Display the roadmap in a readable format.
    """
    if not roadmap:
        print("Failed to generate roadmap.")
        return
    
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print the title and description
    print("\n" + "=" * 80)
    print(f"{roadmap['title']}")
    print("=" * 80)
    print(f"\n{roadmap['description']}\n")
    
    # Print prerequisites if available
    if 'prerequisites' in roadmap and roadmap['prerequisites']:
        print("Prerequisites:")
        for prereq in roadmap['prerequisites']:
            print(f"  • {prereq}")
        print()
    
    # Print estimated time if available
    if 'estimated_time' in roadmap:
        print(f"Estimated Time: {roadmap['estimated_time']}\n")
    
    # Print each step
    print("Learning Path:")
    for i, step in enumerate(roadmap['steps'], 1):
        print(f"\n{'-' * 80}")
        print(f"Step {i}: {step['title']}")
        print(f"{'-' * 80}")
        print(f"{step['description']}\n")
        
        if 'topics' in step and step['topics']:
            print("Topics to cover:")
            for j, topic in enumerate(step['topics'], 1):
                print(f"  {i}.{j} {topic}")
        
        if 'resources' in step and step['resources']:
            print("\nRecommended Resources:")
            for resource in step['resources']:
                print(f"  • {resource}")
    
    print("\n" + "=" * 80)
    print("End of Roadmap")
    print("=" * 80 + "\n")

def main():
    """
    Main function to run the roadmap generator.
    """
    print("=" * 80)
    print("AI Learning Roadmap Generator")
    print("=" * 80)
    print("This tool generates personalized learning roadmaps for any topic.")
    print("=" * 80)
    
    while True:
        topic = input("\nEnter a topic (or 'quit' to exit): ")
        
        if topic.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using the AI Learning Roadmap Generator!")
            break
        
        if not topic.strip():
            print("Please enter a valid topic.")
            continue
        
        # Generate and display the roadmap
        roadmap = generate_roadmap(topic)
        display_roadmap(roadmap)
        
        # Ask if the user wants to generate another roadmap
        again = input("\nWould you like to generate another roadmap? (y/n): ")
        if again.lower() not in ['y', 'yes']:
            print("\nThank you for using the AI Learning Roadmap Generator!")
            break

if __name__ == "__main__":
    main() 