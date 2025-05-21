import tensorflow as tf
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

class Seq2SeqModel:
    def __init__(self, vocab_size, embedding_dim=256, lstm_units=512):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.model = self._build_model()
        
    def _build_model(self):
        # Encoder
        encoder_inputs = Input(shape=(None,))
        encoder_embedding = Embedding(self.vocab_size, self.embedding_dim)(encoder_inputs)
        encoder_lstm = LSTM(self.lstm_units, return_state=True)
        encoder_outputs, state_h, state_c = encoder_lstm(encoder_embedding)
        encoder_states = [state_h, state_c]
        
        # Decoder
        decoder_inputs = Input(shape=(None,))
        decoder_embedding = Embedding(self.vocab_size, self.embedding_dim)(decoder_inputs)
        decoder_lstm = LSTM(self.lstm_units, return_sequences=True, return_state=True)
        decoder_outputs, _, _ = decoder_lstm(decoder_embedding, initial_state=encoder_states)
        decoder_dense = Dense(self.vocab_size, activation='softmax')
        decoder_outputs = decoder_dense(decoder_outputs)
        
        # Model
        model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, train_data, validation_data, batch_size=64, epochs=50):
        """
        Train the model
        """
        # Callbacks
        checkpoint = ModelCheckpoint(
            'models/seq2seq_model.h5',
            monitor='val_loss',
            save_best_only=True,
            mode='min'
        )
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        # Train
        history = self.model.fit(
            train_data,
            validation_data=validation_data,
            batch_size=batch_size,
            epochs=epochs,
            callbacks=[checkpoint, early_stopping]
        )
        
        return history
    
    def save(self, filepath):
        """
        Save model weights
        """
        self.model.save_weights(filepath)
    
    def load(self, filepath):
        """
        Load model weights
        """
        self.model.load_weights(filepath)
    
    def predict(self, input_sequence, max_length=50):
        """
        Generate prediction for a single input sequence
        """
        # Encode input
        encoder_model = Model(
            self.model.input[0],
            self.model.layers[4].output
        )
        encoder_outputs = encoder_model.predict(input_sequence)
        
        # Decoder setup
        decoder_input = tf.zeros((1, 1))
        decoder_states = encoder_outputs
        
        # Generate sequence
        output_sequence = []
        for _ in range(max_length):
            decoder_output, state_h, state_c = self.model.layers[5](
                self.model.layers[3](decoder_input),
                initial_state=decoder_states
            )
            decoder_states = [state_h, state_c]
            
            # Get predicted token
            output_token = self.model.layers[6](decoder_output)
            predicted_token = tf.argmax(output_token[0, -1, :])
            
            # Break if end token is predicted
            if predicted_token == 2:  # Assuming 2 is the index of <END> token
                break
                
            output_sequence.append(predicted_token.numpy())
            decoder_input = tf.expand_dims(predicted_token, 0)
        
        return output_sequence 