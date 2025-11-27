import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from collections import defaultdict, Counter
import random

class VideoRecommendationSystem:
    def __init__(self, n_users, n_videos, n_features):
        self.n_users = n_users
        self.n_videos = n_videos
        self.n_features = n_features
        
        # Candidate Generation: Matrix Factorization
        self.user_embeddings = np.random.randn(n_users, n_features) * 0.01
        self.video_embeddings = np.random.randn(n_videos, n_features) * 0.01
        
        # Ranking: Neural Network
        self.ranking_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000)
        
        self.interactions = defaultdict(list)
        self.scaler = StandardScaler()
        self.video_popularity = Counter()
        
    def train_candidate_model(self, interactions, epochs=5, learning_rate=0.01):
        for _ in range(epochs):
            for user_id, video_id, minutes_watched in interactions:
                self.interactions[user_id].append((video_id, minutes_watched))
                self.video_popularity[video_id] += 1
                
                # Compute error
                pred = np.dot(self.user_embeddings[user_id], self.video_embeddings[video_id])
                error = minutes_watched - pred
                
                # Update embeddings
                self.user_embeddings[user_id] += learning_rate * error * self.video_embeddings[video_id]
                self.video_embeddings[video_id] += learning_rate * error * self.user_embeddings[user_id]
        
        # Normalize embeddings
        self.user_embeddings /= np.linalg.norm(self.user_embeddings, axis=1)[:, np.newaxis]
        self.video_embeddings /= np.linalg.norm(self.video_embeddings, axis=1)[:, np.newaxis]
    
    def generate_candidates(self, user_id, n_candidates=100):
        similarities = cosine_similarity([self.user_embeddings[user_id]], self.video_embeddings)[0]
        watched_videos = set(video_id for video_id, _ in self.interactions[user_id])
        
        # Sort videos by similarity, excluding watched ones
        sorted_videos = sorted([(i, sim) for i, sim in enumerate(similarities) if i not in watched_videos], 
                               key=lambda x: x[1], reverse=True)
        
        return [video_id for video_id, _ in sorted_videos[:n_candidates]]
    
    def prepare_ranking_features(self, user_id, video_id):
        user_embedding = self.user_embeddings[user_id]
        video_embedding = self.video_embeddings[video_id]
        
        user_watch_count = len(self.interactions[user_id])
        video_popularity = self.video_popularity[video_id]
        
        return np.concatenate([user_embedding, video_embedding, [user_watch_count, video_popularity]])
    
    def train_ranking_model(self, interactions):
        X = []
        y = []
        
        for user_id, video_id, minutes_watched in interactions:
            features = self.prepare_ranking_features(user_id, video_id)
            X.append(features)
            y.append(1 if minutes_watched > 0 else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        self.scaler = StandardScaler().fit(X)
        X_scaled = self.scaler.transform(X)
        self.ranking_model.fit(X_scaled, y)
    
    def rank_candidates(self, user_id, candidates):
        features = np.array([self.prepare_ranking_features(user_id, video_id) for video_id in candidates])
        features_scaled = self.scaler.transform(features)
        probabilities = self.ranking_model.predict_proba(features_scaled)[:, 1]
        
        return [x for _, x in sorted(zip(probabilities, candidates), reverse=True)]
    
    def recommend(self, user_id, n_recommendations=10):
        candidates = self.generate_candidates(user_id)
        ranked_candidates = self.rank_candidates(user_id, candidates)
        return ranked_candidates[:n_recommendations]
    
    def evaluate(self, test_interactions):
        precision_sum = recall_sum = 0
        n_users = len(set(user_id for user_id, _, _ in test_interactions))
        
        user_test_videos = defaultdict(list)
        for user_id, video_id, _ in test_interactions:
            user_test_videos[user_id].append(video_id)
        
        for user_id, true_videos in user_test_videos.items():
            if len(true_videos) > 0:
                predicted = set(self.recommend(user_id, n_recommendations=len(true_videos)))
                true_videos = set(true_videos)
                
                intersection = len(predicted.intersection(true_videos))
                precision = intersection / len(predicted) if len(predicted) > 0 else 0
                recall = intersection / len(true_videos) if len(true_videos) > 0 else 0
                
                precision_sum += precision
                recall_sum += recall
        
        return precision_sum / n_users, recall_sum / n_users

if __name__ == "__main__":
    # Example usage
    n_users, n_videos, n_features = 1000, 10000, 50
    recommender = VideoRecommendationSystem(n_users, n_videos, n_features)

    # Generate more realistic interactions
    interactions = [(user_id, video_id, random.randint(0, 60)) 
                    for user_id in range(n_users) 
                    for video_id in random.sample(range(n_videos), random.randint(5, 20))]

    # Split interactions into train and test
    random.shuffle(interactions)
    split = int(0.8 * len(interactions))
    train_interactions = interactions[:split]
    test_interactions = interactions[split:]

    # Train the models
    recommender.train_candidate_model(train_interactions)
    recommender.train_ranking_model(train_interactions)

    # Evaluate the model
    precision, recall = recommender.evaluate(test_interactions)
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")

    # Example recommendation
    user_id = 0
    recommendations = recommender.recommend(user_id)
    print(f"Recommendations for user {user_id}: {recommendations}")