import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import ndcg_score
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AirbnbRankingModel(nn.Module):
    def __init__(self, input_dim):
        super(AirbnbRankingModel, self).__init__()
        self.embedding = nn.Embedding(5000, 32)  # Assuming 5000 unique listings
        self.layers = nn.Sequential(
            nn.Linear(input_dim + 32, 256),  # +32 for the embedding
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x, listing_ids):
        listing_embeddings = self.embedding(listing_ids)
        x = torch.cat([x, listing_embeddings], dim=1)
        return self.layers(x)


def preprocess_data(data):
    """
    Preprocess the input data for the Airbnb ranking model.

    Args:
    data (pd.DataFrame): Raw input data

    Returns:
    pd.DataFrame: Preprocessed data
    """
    logger.info("Starting data preprocessing")

    # Feature engineering
    data['log_lat_distance'] = np.log(np.abs(data['latitude'] - data['map_center_lat']))
    data['log_long_distance'] = np.log(np.abs(data['longitude'] - data['map_center_long']))

    # Normalize numerical features
    scaler = StandardScaler()
    numerical_features = ['user_age', 'num_previous_bookings', 'previous_length_of_stays']
    data[numerical_features] = scaler.fit_transform(data[numerical_features])

    # One-hot encode categorical features
    categorical_features = ['user_gender', 'listing_city', 'month', 'weekofyear', 'dayofweek', 'hourofday']
    data = pd.get_dummies(data, columns=categorical_features)

    logger.info("Data preprocessing completed")
    return data


def generate_sample_data(num_samples=10000):
    np.random.seed(42)
    data = pd.DataFrame({
        'user_id': np.random.randint(1, 1000, num_samples),
        'user_age': np.random.randint(18, 80, num_samples),
        'user_gender': np.random.choice(['M', 'F'], num_samples),
        'num_previous_bookings': np.random.randint(0, 20, num_samples),
        'previous_length_of_stays': np.random.randint(1, 30, num_samples),
        'listing_id': np.random.randint(1, 5000, num_samples),
        'listing_city': np.random.choice(['New York', 'Paris', 'London', 'Tokyo', 'Sydney'], num_samples),
        'latitude': np.random.uniform(30, 50, num_samples),
        'longitude': np.random.uniform(-120, 120, num_samples),
        'map_center_lat': np.random.uniform(30, 50, num_samples),
        'map_center_long': np.random.uniform(-120, 120, num_samples),
        'date': pd.date_range(start='2024-01-01', periods=num_samples).tolist(),
        'month': np.random.randint(1, 13, num_samples),
        'weekofyear': np.random.randint(1, 53, num_samples),
        'dayofweek': np.random.randint(0, 7, num_samples),
        'hourofday': np.random.randint(0, 24, num_samples),
        'booking': np.random.choice([0, 1], num_samples, p=[0.9, 0.1])  # 10% booking rate
    })
    return data


def train_model(model, train_loader, val_loader, criterion, optimizer, device, num_epochs=10):
    """
    Train the Airbnb ranking model.

    Args:
    model (nn.Module): The neural network model
    train_loader (DataLoader): Training data loader
    val_loader (DataLoader): Validation data loader
    criterion: Loss function
    optimizer: Optimization algorithm
    device: Device to run the model on (CPU or GPU)
    num_epochs (int): Number of training epochs

    Returns:
    model (nn.Module): Trained model
    """
    logger.info("Starting model training")

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0.0
        for batch_features, batch_listing_ids, batch_labels in train_loader:
            batch_features, batch_listing_ids, batch_labels = batch_features.to(device), batch_listing_ids.to(
                device), batch_labels.to(device)
            optimizer.zero_grad()
            outputs = model(batch_features, batch_listing_ids)
            loss = criterion(outputs, batch_labels.unsqueeze(1))
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_features, batch_listing_ids, batch_labels in val_loader:
                batch_features, batch_listing_ids, batch_labels = batch_features.to(device), batch_listing_ids.to(
                    device), batch_labels.to(device)
                outputs = model(batch_features, batch_listing_ids)
                loss = criterion(outputs, batch_labels.unsqueeze(1))
                val_loss += loss.item()

        logger.info(
            f"Epoch {epoch + 1}/{num_epochs}, Train Loss: {train_loss / len(train_loader):.4f}, Val Loss: {val_loss / len(val_loader):.4f}")

    logger.info("Model training completed")
    return model


def evaluate_model(model, test_loader, device):
    """
    Evaluate the Airbnb ranking model using nDCG metric.

    Args:
    model (nn.Module): Trained model
    test_loader (DataLoader): Test data loader
    device: Device to run the model on (CPU or GPU)

    Returns:
    float: nDCG score
    """
    logger.info("Starting model evaluation")

    model.eval()
    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for batch_features, batch_listing_ids, batch_labels in test_loader:
            batch_features, batch_listing_ids, batch_labels = batch_features.to(device), batch_listing_ids.to(
                device), batch_labels.to(device)
            outputs = model(batch_features, batch_listing_ids)
            all_predictions.extend(outputs.cpu().numpy().flatten())
            all_labels.extend(batch_labels.cpu().numpy())

    # Ensure predictions and labels are 1-dimensional
    all_predictions = np.array(all_predictions).flatten()
    all_labels = np.array(all_labels).flatten()

    ndcg = ndcg_score([all_labels], [all_predictions])
    logger.info(f"nDCG Score: {ndcg:.4f}")
    return ndcg


def main():
    # Generate sample data
    data = generate_sample_data()
    logger.info(f"Generated sample data with {len(data)} rows")

    preprocessed_data = preprocess_data(data)

    # Split data
    split_date = datetime.now() - timedelta(days=7)
    train_data = preprocessed_data[preprocessed_data['date'] < split_date]
    val_data = preprocessed_data[preprocessed_data['date'] >= split_date]

    # Prepare features and labels
    features = preprocessed_data.drop(['booking', 'date', 'listing_id'], axis=1)
    labels = preprocessed_data['booking']
    listing_ids = preprocessed_data['listing_id']

    X_train, X_val, y_train, y_val, ids_train, ids_val = train_test_split(features, labels, listing_ids, test_size=0.2,
                                                                          random_state=42)

    # Ensure all data is numeric
    X_train = X_train.astype(float)
    X_val = X_val.astype(float)

    # Convert to PyTorch tensors
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train.values),
        torch.LongTensor(ids_train.values),
        torch.FloatTensor(y_train.values)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val.values),
        torch.LongTensor(ids_val.values),
        torch.FloatTensor(y_val.values)
    )

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64)

    # Initialize model
    input_dim = X_train.shape[1]
    model = AirbnbRankingModel(input_dim)

    # Set up training
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Train model
    trained_model = train_model(model, train_loader, val_loader, criterion, optimizer, device)

    # Evaluate model
    test_loader = DataLoader(val_dataset, batch_size=64)  # Using validation set as test set for demonstration
    ndcg_score = evaluate_model(trained_model, test_loader, device)

    logger.info("Airbnb ranking model training and evaluation completed")


if __name__ == "__main__":
    main()
