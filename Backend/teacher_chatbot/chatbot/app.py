from flask import Flask, request, jsonify, render_template
import os
import json
from utils.preprocessor import TextPreprocessor
from utils.data_preparation import DataPreparation
from models.seq2seq_model import Seq2SeqModel
import numpy as np

app = Flask(__name__)

# Initialize components
preprocessor = TextPreprocessor()
data_prep = DataPreparation('data/qa_data.json')
model = None
vocabulary = None

def load_model():
    global model, vocabulary
    # Load vocabulary
    with open('data/vocabulary.json', 'r') as f:
        vocabulary = json.load(f)
    
    # Initialize and load model
    model = Seq2SeqModel(len(vocabulary))
    model.load('models/seq2seq_model.h5')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    if not model:
        load_model()
    
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Preprocess question
        sequence = preprocessor.text_to_sequence(question, vocabulary)
        sequence = np.array([sequence])
        
        # Generate answer
        answer_sequence = model.predict(sequence)
        
        # Convert sequence back to text
        reverse_vocab = {v: k for k, v in vocabulary.items()}
        answer = ' '.join([reverse_vocab.get(idx, '<UNK>') for idx in answer_sequence])
        
        return jsonify({
            'question': question,
            'answer': answer
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/train', methods=['POST'])
def train():
    try:
        # Prepare data
        data = data_prep.prepare_data()
        
        # Save vocabulary
        with open('data/vocabulary.json', 'w') as f:
            json.dump(data['vocabulary'], f)
        
        # Initialize and train model
        global model
        model = Seq2SeqModel(len(data['vocabulary']))
        history = model.train(
            [data['X_train'], data['y_train']],
            [data['X_val'], data['y_val']]
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Model trained successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create sample dataset if it doesn't exist
    if not os.path.exists('data/qa_data.json'):
        data_prep.create_sample_dataset()
    
    app.run(debug=True) 