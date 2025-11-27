import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import time
from collections import deque
import logging
import argparse

# Problem Statement:
# Design a personalized LinkedIn feed to maximize long-term user engagement.
# We measure engagement using Click Through Rate (CTR), which is the ratio of
# clicks a feed receives to the number of times it's shown.

# Algorithm Explanation:
# This implementation uses a neural network-based approach for feed ranking.
# The model architecture consists of:
# 1. Embedding layers for user IDs and activity types to capture latent features
# 2. A series of fully connected layers with ReLU activations and dropout for regularization
# 3. A final sigmoid activation to output probabilities

# The algorithm works as follows:
# 1. Preprocess and normalize input features
# 2. Convert categorical variables (user IDs, activity types) into dense embeddings
# 3. Concatenate all features and pass through the neural network
# 4. Output a probability score for each feed item
# 5. During inference, filter out recently shown content to maintain freshness

# Metrics Explanation:
# 1. Offline metrics:
#    - Normalized Cross-Entropy (NCE): Measures how well the model's predictions match the true probabilities,
#      normalized to account for class imbalance. Lower values indicate better performance.
#    - Area Under the ROC Curve (AUC): Measures the model's ability to distinguish between classes.
#      A higher AUC indicates better discrimination between positive and negative samples.
# 2. Online metrics:
#    - Conversion rate (ratio of clicks to number of feeds shown): This directly measures user engagement
#      and the effectiveness of the ranking algorithm in real-world scenarios.

# These metrics were chosen because:
# - NCE is suitable for imbalanced datasets and provides a normalized measure of prediction quality.
# - AUC is threshold-independent and gives an overall measure of ranking performance.
# - Conversion rate directly aligns with the business goal of increasing user engagement.

# Requirements:
# Training:
# - Handle large volumes of data in distributed settings
# - Support for high level of personalization
# - Ability to retrain models multiple times per day to address data distribution shifts
# - Ensure data freshness to avoid repetitive content

# Inference:
# - Scalability: Handle 300 million users
# - Latency: Return results within 50ms (as part of a 200ms end-to-end pipeline)
# - Data freshness: Avoid showing repetitive content

# Configure logger
logger = logging.getLogger(__name__)


def configure_logger(log_level=logging.INFO):
    """
    Configure the logger for the FeedRanking module.
    Args:
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG)
    """
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class FeedRanking(nn.Module):
    def __init__(self, input_feature_dim, num_users, num_activity_types=5):
        """
        Initialize the FeedRanking model.
        Args:
            input_feature_dim (int): Dimension of input features
            num_users (int): Number of unique users
            num_activity_types (int): Number of activity types
        """
        super(FeedRanking, self).__init__()
        self.user_embedding = nn.Embedding(num_users, 32)
        self.activity_embedding = nn.Embedding(num_activity_types, 16)
        self.model = nn.Sequential(
            nn.Linear(input_feature_dim + 32 + 16, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        self.feature_scaler = StandardScaler()
        self.recent_content_ids = deque(maxlen=1000)  # Store recent content IDs
        logger.info(
            f"FeedRanking model initialized with input_feature_dim={input_feature_dim}, num_users={num_users}, num_activity_types={num_activity_types}")

    def forward(self, features, user_ids, activity_types):
        """
        Forward pass of the model.
        Args:
            features (torch.Tensor): Input features
            user_ids (torch.Tensor): User IDs
            activity_types (torch.Tensor): Activity types
        Returns:
            torch.Tensor: Model predictions
        """
        user_embeddings = self.user_embedding(user_ids)
        activity_embeddings = self.activity_embedding(activity_types)
        combined_features = torch.cat([features, user_embeddings, activity_embeddings], dim=1)
        return self.model(combined_features)

    def preprocess_data(self, features, user_ids, activity_types, targets=None):
        """
        Preprocess input data.
        Args:
            features (np.array): Input features
            user_ids (np.array): User IDs
            activity_types (np.array): Activity types
            targets (np.array, optional): Target values
        Returns:
            tuple: Preprocessed data as PyTorch tensors
        """
        logger.debug(
            f"Preprocessing data: features shape={features.shape}, user_ids shape={user_ids.shape}, activity_types shape={activity_types.shape}")
        if targets is not None:
            scaled_features = self.feature_scaler.fit_transform(features)
            logger.info("Fitted StandardScaler on input features")
            return (torch.FloatTensor(scaled_features),
                    torch.LongTensor(user_ids),
                    torch.LongTensor(activity_types),
                    torch.FloatTensor(targets))
        return (torch.FloatTensor(self.feature_scaler.transform(features)),
                torch.LongTensor(user_ids),
                torch.LongTensor(activity_types))

    def train_model(self, features, user_ids, activity_types, targets, num_epochs=5, batch_size=128):
        """
        Train the model.
        Args:
            features (np.array): Input features
            user_ids (np.array): User IDs
            activity_types (np.array): Activity types
            targets (np.array): Target values
            num_epochs (int): Number of training epochs
            batch_size (int): Batch size for training
        """
        logger.info(f"Starting model training: num_epochs={num_epochs}, batch_size={batch_size}")
        scaled_features, user_ids_tensor, activity_types_tensor, targets_tensor = self.preprocess_data(features, user_ids, activity_types, targets)
        train_features, val_features, train_user_ids, val_user_ids, train_activity_types, val_activity_types, train_targets, val_targets = train_test_split(
            scaled_features, user_ids_tensor, activity_types_tensor, targets_tensor, test_size=0.2, random_state=42)
        logger.debug(f"Train-validation split: train size={len(train_features)}, validation size={len(val_features)}")

        train_dataset = TensorDataset(train_features, train_user_ids, train_activity_types, train_targets)
        val_dataset = TensorDataset(val_features, val_user_ids, val_activity_types, val_targets)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        loss_function = nn.BCELoss()
        optimizer = optim.Adam(self.parameters(), lr=0.001)

        for epoch in range(num_epochs):
            self.train()
            total_loss = 0
            for batch_features, batch_user_ids, batch_activity_types, batch_targets in train_loader:
                optimizer.zero_grad()
                predictions = self(batch_features, batch_user_ids, batch_activity_types)
                loss = loss_function(predictions, batch_targets.unsqueeze(1))
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(train_loader)
            logger.info(f"Epoch {epoch + 1}/{num_epochs}, Average Training Loss: {avg_loss:.4f}")

            self.eval()
            with torch.no_grad():
                val_predictions = self(val_features, val_user_ids, val_activity_types)
                val_loss = loss_function(val_predictions, val_targets.unsqueeze(1))
                auc_score = roc_auc_score(val_targets.numpy(), val_predictions.numpy())
                nce_score = self.normalized_cross_entropy(val_targets.numpy(), val_predictions.numpy())
            logger.info(
                f"Epoch {epoch + 1}/{num_epochs}, Validation Loss: {val_loss.item():.4f}, AUC: {auc_score:.4f}, NCE: {nce_score:.4f}")

    def predict(self, features, user_ids, activity_types, content_ids):
        """
        Make predictions using the trained model.
        Args:
            features (np.array): Input features
            user_ids (np.array): User IDs
            activity_types (np.array): Activity types
            content_ids (np.array): Content IDs
        Returns:
            np.array: Filtered predictions
        """
        logger.debug(f"Making predictions for {len(features)} samples")
        self.eval()
        scaled_features, user_ids_tensor, activity_types_tensor = self.preprocess_data(features, user_ids, activity_types)
        start_time = time.time()
        with torch.no_grad():
            predictions = self(scaled_features, user_ids_tensor, activity_types_tensor).numpy()

        # Filter out recently shown content
        filtered_predictions = []
        for prediction, content_id in zip(predictions, content_ids):
            if content_id not in self.recent_content_ids:
                filtered_predictions.append(prediction[0])
                self.recent_content_ids.append(content_id)
            else:
                filtered_predictions.append(0)  # Assign low score to recent content
        logger.debug(f"Filtered {len(predictions) - len(filtered_predictions)} recent content items")

        end_time = time.time()
        inference_latency = (end_time - start_time) * 1000  # Convert to milliseconds
        if inference_latency > 50:
            logger.warning(f"Inference latency ({inference_latency:.2f}ms) exceeds 50ms threshold")
        else:
            logger.info(f"Inference completed in {inference_latency:.2f}ms")

        return np.array(filtered_predictions)

    def update_model(self, new_features, new_user_ids, new_activity_types, new_targets):
        """
        Update the model with new data.
        Args:
            new_features (np.array): New input features
            new_user_ids (np.array): New user IDs
            new_activity_types (np.array): New activity types
            new_targets (np.array): New target values
        """
        logger.info(f"Updating model with {len(new_features)} new samples")
        scaled_features, user_ids_tensor, activity_types_tensor, targets_tensor = self.preprocess_data(new_features, new_user_ids,
                                                                                   new_activity_types, new_targets)
        dataset = TensorDataset(scaled_features, user_ids_tensor, activity_types_tensor, targets_tensor)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)
        loss_function = nn.BCELoss()
        optimizer = optim.Adam(self.parameters(), lr=0.001)

        self.train()
        total_loss = 0
        for batch_features, batch_user_ids, batch_activity_types, batch_targets in loader:
            optimizer.zero_grad()
            predictions = self(batch_features, batch_user_ids, batch_activity_types)
            loss = loss_function(predictions, batch_targets.unsqueeze(1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        logger.info(f"Model update completed. Average Loss: {avg_loss:.4f}")

    def normalized_cross_entropy(self, true_labels, predicted_probs):
        """
        Calculate the Normalized Cross-Entropy (NCE).
        Args:
            true_labels (np.array): True labels
            predicted_probs (np.array): Predicted probabilities
        Returns:
            float: Normalized Cross-Entropy
        """
        epsilon = 1e-15
        predicted_probs = np.clip(predicted_probs, epsilon, 1 - epsilon)
        num_samples = len(true_labels)
        positive_rate = np.mean(true_labels)

        cross_entropy = -np.sum(true_labels * np.log(predicted_probs) + (1 - true_labels) * np.log(1 - predicted_probs)) / num_samples
        normalized_cross_entropy = cross_entropy - (positive_rate * np.log(positive_rate) + (1 - positive_rate) * np.log(1 - positive_rate))

        logger.debug(f"Calculated NCE: {normalized_cross_entropy:.4f}")
        return normalized_cross_entropy


def generate_sample_data(num_samples, num_users, num_activity_types=5):
    """
    Generate realistic sample data for feed ranking.

    Args:
    num_samples (int): Number of samples to generate
    num_users (int): Number of unique users
    num_activity_types (int): Number of different activity types (default: 5)

    Returns:
    Tuple of (features, user_ids, activity_types, targets, content_ids)
    """
    logger.info(
        f"Generating sample data: num_samples={num_samples}, num_users={num_users}, num_activity_types={num_activity_types}")
    np.random.seed(42)

    # Generate user features
    user_ages = np.random.randint(18, 65, num_users)
    user_genders = np.random.choice(['M', 'F'], num_users)
    user_locations = np.random.choice(['Urban', 'Suburban', 'Rural'], num_users)

    # Generate content features
    content_categories = ['News', 'Entertainment', 'Sports', 'Technology', 'Lifestyle']
    content_lengths = np.random.randint(50, 1000, num_samples)  # Content length in words
    content_recency = np.random.randint(0, 30, num_samples)  # Days since content was published

    # Generate sample data
    features = np.zeros((num_samples, 10))  # 10 features
    user_ids = np.random.randint(0, num_users, num_samples)
    activity_types = np.random.randint(0, num_activity_types, num_samples)
    content_ids = np.arange(num_samples)

    for i in range(num_samples):
        user_id = user_ids[i]
        features[i, 0] = user_ages[user_id] / 65.0  # Normalized age
        features[i, 1] = 1 if user_genders[user_id] == 'M' else 0  # Gender (binary)
        features[i, 2] = {'Urban': 0, 'Suburban': 1, 'Rural': 2}[user_locations[user_id]] / 2.0  # Normalized location
        features[i, 3] = content_lengths[i] / 1000.0  # Normalized content length
        features[i, 4] = 1 - (content_recency[i] / 30.0)  # Normalized recency (1 = very recent, 0 = old)
        features[i, 5:10] = np.eye(5)[np.random.choice(5)]  # One-hot encoded content category

    # Simulate different CTRs for different activity types and user segments
    base_ctr = np.array([0.02, 0.05, 0.03, 0.04, 0.01])  # Base CTR for each activity type
    age_factor = np.where(user_ages[user_ids] < 30, 1.2, 0.8)  # Younger users click more
    gender_factor = np.where(user_genders[user_ids] == 'F', 1.1, 0.9)  # Females click slightly more in this example
    recency_factor = 1 + (1 - content_recency / 30) * 0.5  # More recent content gets more clicks

    click_probabilities = base_ctr[activity_types] * age_factor * gender_factor * recency_factor
    targets = np.random.rand(num_samples) < click_probabilities

    logger.debug(f"Generated sample data: features shape={features.shape}, targets shape={targets.shape}")
    return features, user_ids, activity_types, targets.astype(float), content_ids


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Feed Ranking Model")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Configure logger
    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logger(log_level)

    # Generate sample data
    features, user_ids, activity_types, targets, content_ids = generate_sample_data(100000, 10000)

    # Initialize the FeedRanking model
    input_feature_dim = features.shape[1]
    num_users = 10000
    num_activity_types = 5
    feed_ranking_model = FeedRanking(input_feature_dim, num_users, num_activity_types)

    # Train the model
    feed_ranking_model.train_model(features, user_ids, activity_types, targets)

    # Example prediction
    new_features, new_user_ids, new_activity_types, _, new_content_ids = generate_sample_data(5, 10000)
    predictions = feed_ranking_model.predict(new_features, new_user_ids, new_activity_types, new_content_ids)
    logger.info(f"CTR Predictions for new feeds: {predictions}")

    # Example of model update with new data
    new_features, new_user_ids, new_activity_types, new_targets, _ = generate_sample_data(10000, 10000)
    feed_ranking_model.update_model(new_features, new_user_ids, new_activity_types, new_targets)
