# Custom NLP Educational Chatbot

This is a custom NLP chatbot built for educational purposes, specifically designed for doubt-solving and teaching. The chatbot uses a Seq2Seq model with LSTM layers to generate responses to student questions.

## Features

- Custom NLP preprocessing pipeline
- Seq2Seq model with LSTM layers
- Web scraping for educational content
- Flask web interface
- Real-time chat interaction
- Support for multiple subjects

## Project Structure

```
chatbot/
├── data/
│   ├── qa_data.json
│   └── vocabulary.json
├── models/
│   └── seq2seq_model.h5
├── utils/
│   ├── preprocessor.py
│   └── data_preparation.py
├── templates/
│   └── index.html
├── app.py
└── requirements.txt
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Start asking questions in the chat interface!

## Training the Model

The model comes pre-trained with a sample dataset, but you can train it with your own data:

1. Prepare your Q&A dataset in JSON format:
```json
[
    {
        "question": "What is photosynthesis?",
        "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy to produce food."
    },
    ...
]
```

2. Save your dataset as `data/qa_data.json`

3. Train the model by sending a POST request to `/train`:
```bash
curl -X POST http://localhost:5000/train
```

## Customization

- Modify `utils/preprocessor.py` to change text preprocessing steps
- Adjust model parameters in `models/seq2seq_model.py`
- Add more training data to `data/qa_data.json`
- Customize the web interface in `templates/index.html`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 