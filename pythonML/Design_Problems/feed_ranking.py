import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, roc_auc_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

class FeedRanking:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()

    def create_model(self, input_dim):
        model = Sequential([
            Dense(64, activation='relu', input_dim=input_dim),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def preprocess_data(self, X, y=None):
        if y is not None:
            X_scaled = self.scaler.fit_transform(X)
            return X_scaled, y
        return self.scaler.transform(X)

    def train(self, X, y):
        X_scaled, y = self.preprocess_data(X, y)
        X_train, X_val, y_train, y_val = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        self.model = self.create_model(X_train.shape[1])
        self.model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=10, batch_size=32, verbose=1)

        # Compute and print offline metrics
        y_pred = self.model.predict(X_val)
        self.compute_metrics(y_val, y_pred)

    def predict(self, X):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        X_scaled = self.preprocess_data(X)
        return self.model.predict(X_scaled)

    def update_model(self, X_new, y_new):
        X_scaled, y = self.preprocess_data(X_new, y_new)
        self.model.fit(X_scaled, y, epochs=1, batch_size=32, verbose=0)

    def compute_metrics(self, y_true, y_pred):
        # Compute Normalized Cross-Entropy (NCE)
        # NCE helps the model be less sensitive to background CTR
        nce = log_loss(y_true, y_pred)
        print(f"Normalized Cross-Entropy (NCE): {nce}")

        # Compute Area Under the ROC Curve (AUC)
        # AUC is a good metric for binary classification problems
        auc = roc_auc_score(y_true, y_pred)
        print(f"Area Under the ROC Curve (AUC): {auc}")

def generate_sample_data(n_samples):
    np.random.seed(42)
    X = np.random.rand(n_samples, 10)  # 10 features
    y = (X[:, 0] + X[:, 1] > 1).astype(int)  # Simple rule for binary classification
    return X, y

if __name__ == "__main__":
    # Generate sample data
    X, y = generate_sample_data(10000)

    # Initialize the FeedRanking model
    # This model will be used to rank feeds based on their likelihood of being clicked (CTR)
    feed_ranking = FeedRanking()

    # Train the model using the generated sample data
    # X contains the feature vectors for each feed
    # y contains the binary labels (1 for clicked, 0 for not clicked)
    # The model will learn to predict the click-through rate (CTR) for new feeds
    feed_ranking.train(X, y)

    # Example prediction
    new_feeds = np.random.rand(5, 10)  # 5 new feeds
    predictions = feed_ranking.predict(new_feeds)
    print("CTR Predictions for new feeds:", predictions)

    # Example of model update with new data
    X_new, y_new = generate_sample_data(1000)
    feed_ranking.update_model(X_new, y_new)
