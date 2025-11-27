import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

# Create synthetic data
X = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]])  # Hours studied
y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])  # Pass (1) or Fail (0)

# Visualize the data
plt.scatter(X, y, color='blue', label='Students')
plt.title('Student Exam Results')
plt.xlabel('Hours Studied')
plt.ylabel('Pass (1) or Fail (0)')
plt.xticks(np.arange(0, 12, 1))
plt.yticks([0, 1], ['Fail', 'Pass'])
plt.legend()
plt.grid()
plt.show()

# Create the logistic regression model
model = LogisticRegression()

# Train the model using the synthetic data
model.fit(X, y)

# Predict probability for a new student who studies 5.5 hours
new_data = np.array([[5.5]])
probability = model.predict_proba(new_data)[0][1]  # Probability of passing
prediction = model.predict(new_data)  # Predicted class (0 or 1)

print(f"Probability of passing for 5.5 hours studied: {probability:.2f}")
print(f"Predicted outcome (1 = Pass, 0 = Fail): {prediction[0]}")

# Create a range of hours for visualization
x_range = np.linspace(0, 11, 300).reshape(-1, 1)  # From 0 to 11 hours
y_prob = model.predict_proba(x_range)[:, 1]  # Get probability of passing

# Plot the data and the decision boundary
plt.scatter(X, y, color='blue', label='Students')
plt.plot(x_range, y_prob, color='red', label='Decision Boundary')
plt.title('Logistic Regression Decision Boundary')
plt.xlabel('Hours Studied')
plt.ylabel('Probability of Passing')
plt.xticks(np.arange(0, 12, 1))
plt.yticks(np.arange(0, 1.1, 0.1))
plt.legend()
plt.grid()
plt.show()
