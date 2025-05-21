import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess_text(self, text):
        """
        Preprocess text by:
        1. Converting to lowercase
        2. Removing special characters and numbers
        3. Tokenizing
        4. Removing stopwords
        5. Lemmatizing
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words
        ]
        
        return ' '.join(processed_tokens)
    
    def create_vocabulary(self, texts, max_words=10000):
        """
        Create vocabulary from a list of texts
        """
        # Combine all texts
        all_text = ' '.join(texts)
        
        # Preprocess
        processed_text = self.preprocess_text(all_text)
        
        # Get unique words
        words = processed_text.split()
        word_freq = {}
        
        # Count word frequencies
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Create vocabulary
        vocabulary = {word: idx for idx, (word, _) in enumerate(sorted_words[:max_words])}
        
        # Add special tokens
        vocabulary['<PAD>'] = len(vocabulary)
        vocabulary['<START>'] = len(vocabulary)
        vocabulary['<END>'] = len(vocabulary)
        vocabulary['<UNK>'] = len(vocabulary)
        
        return vocabulary
    
    def text_to_sequence(self, text, vocabulary, max_length=50):
        """
        Convert text to sequence of indices
        """
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Convert to sequence
        sequence = []
        for word in processed_text.split():
            if word in vocabulary:
                sequence.append(vocabulary[word])
            else:
                sequence.append(vocabulary['<UNK>'])
        
        # Add start and end tokens
        sequence = [vocabulary['<START>']] + sequence + [vocabulary['<END>']]
        
        # Pad or truncate
        if len(sequence) < max_length:
            sequence = sequence + [vocabulary['<PAD>']] * (max_length - len(sequence))
        else:
            sequence = sequence[:max_length-1] + [vocabulary['<END>']]
        
        return sequence 