import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import random

class VideoRecommendationSystem:
    def __init__(self, n_users, n_videos, n_features):
        self.n_users = n_users
        self.n_videos = n_videos
        self.n_features = n_features
        
        # Initialize embeddings with small random values
        self.user_embeddings = np.random.randn(n_users, n_features) * 0.01
        self.video_embeddings = np.random.randn(n_videos, n_features) * 0.01
        
        self.interactions = defaultdict(list)
        
    def train(self, interactions, epochs=5, learning_rate=0.01):
        for _ in range(epochs):
            for user_id, video_id in interactions:
                self.interactions[user_id].append(video_id)
                
                # Compute error
                pred = np.dot(self.user_embeddings[user_id], self.video_embeddings[video_id])
                error = 1 - pred  # Assuming 1 for positive interaction
                
                # Update embeddings
                self.user_embeddings[user_id] += learning_rate * error * self.video_embeddings[video_id]
                self.video_embeddings[video_id] += learning_rate * error * self.user_embeddings[user_id]
        
        # Normalize embeddings
        self.user_embeddings /= np.linalg.norm(self.user_embeddings, axis=1)[:, np.newaxis]
        self.video_embeddings /= np.linalg.norm(self.video_embeddings, axis=1)[:, np.newaxis]
    
    def recommend(self, user_id, n_recommendations=10):
        similarities = cosine_similarity([self.user_embeddings[user_id]], self.video_embeddings)[0]
        watched_videos = set(self.interactions[user_id])
        
        # Sort videos by similarity, excluding watched ones
        sorted_videos = sorted([(i, sim) for i, sim in enumerate(similarities) if i not in watched_videos], 
                               key=lambda x: x[1], reverse=True)
        
        return [video_id for video_id, _ in sorted_videos[:n_recommendations]]
    
    def evaluate(self, test_interactions):
        precision_sum = recall_sum = 0
        n_users = len(test_interactions)
        
        for user_id, true_videos in test_interactions.items():
            if len(true_videos) > 0:
                predicted = set(self.recommend(user_id, n_recommendations=len(true_videos)))
                true_videos = set(true_videos)
                
                intersection = len(predicted.intersection(true_videos))
                precision = intersection / len(predicted) if len(predicted) > 0 else 0
                recall = intersection / len(true_videos) if len(true_videos) > 0 else 0
                
                precision_sum += precision
                recall_sum += recall
        
        return precision_sum / n_users, recall_sum / n_users

# Example usage
n_users, n_videos, n_features = 1000, 10000, 50
recommender = VideoRecommendationSystem(n_users, n_videos, n_features)

# Generate more realistic interactions
interactions = [(user_id, video_id) 
                for user_id in range(n_users) 
                for video_id in random.sample(range(n_videos), random.randint(5, 20))]

# Split interactions into train and test
random.shuffle(interactions)
split = int(0.8 * len(interactions))
train_interactions = interactions[:split]
test_interactions = defaultdict(list)
for user_id, video_id in interactions[split:]:
    test_interactions[user_id].append(video_id)

recommender.train(train_interactions)
precision, recall = recommender.evaluate(test_interactions)
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")

# Example recommendation
user_id = 0
recommendations = recommender.recommend(user_id)
print(f"Recommendations for user {user_id}: {recommendations}")