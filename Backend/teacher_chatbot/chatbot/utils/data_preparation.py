import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from .preprocessor import TextPreprocessor

class DataPreparation:
    def __init__(self, data_path):
        self.data_path = data_path
        self.preprocessor = TextPreprocessor()
        
    def load_data(self):
        """
        Load Q&A data from JSON file
        """
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def prepare_data(self, max_length=50):
        """
        Prepare data for training
        """
        # Load data
        data = self.load_data()
        
        # Extract questions and answers
        questions = [item['question'] for item in data]
        answers = [item['answer'] for item in data]
        
        # Create vocabulary
        all_texts = questions + answers
        vocabulary = self.preprocessor.create_vocabulary(all_texts)
        
        # Convert to sequences
        question_sequences = [
            self.preprocessor.text_to_sequence(q, vocabulary, max_length)
            for q in questions
        ]
        answer_sequences = [
            self.preprocessor.text_to_sequence(a, vocabulary, max_length)
            for a in answers
        ]
        
        # Convert to numpy arrays
        X = np.array(question_sequences)
        y = np.array(answer_sequences)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        return {
            'X_train': X_train,
            'X_val': X_val,
            'y_train': y_train,
            'y_val': y_val,
            'vocabulary': vocabulary
        }
    
    def create_sample_dataset(self):
        """
        Create a sample dataset for testing
        """
        sample_data = [
            {
                "question": "What is photosynthesis?",
                "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy to produce food."
            },
            {
                "question": "How does the water cycle work?",
                "answer": "The water cycle involves evaporation, condensation, precipitation, and collection of water."
            },
            {
                "question": "What is the Pythagorean theorem?",
                "answer": "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides."
            },
            {
                "question": "What is the difference between a plant and animal cell?",
                "answer": "Plant cells have cell walls and chloroplasts, while animal cells do not. Animal cells have centrioles, which plant cells lack."
            },
            {
                "question": "How does the digestive system work?",
                "answer": "The digestive system breaks down food into nutrients through mechanical and chemical processes, starting from the mouth and ending in the intestines."
            }
        ]
        
        # Save sample data
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=4) 