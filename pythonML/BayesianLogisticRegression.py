import numpy as np
import matplotlib.pyplot as plt
import pymc3 as pm

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

# Build Bayesian Logistic Regression Model
with pm.Model() as model:
    # Priors for unknown model parameters
    alpha = pm.Normal('alpha', mu=0, sigma=1)  # Intercept
    beta = pm.Normal('beta', mu=0, sigma=1)  # Coefficient for hours studied

    # Logistic regression model
    mu = pm.invlogit(alpha + beta * X.flatten())

    # Likelihood (sampling distribution) of observations
    y_obs = pm.Bernoulli('y_obs', p=mu, observed=y)

    # Perform inference
    trace = pm.sample(2000, return_inferencedata=False)  # Sample from the posterior

# Predict for a new student who studies 5.5 hours
new_data = np.array([[5.5]])

# Calculate the posterior predictive probability
with model:
    pm.set_data({'X': new_data.flatten()})
    pred = pm.sample_posterior_predictive(trace)
    pred_prob = np.mean(pred['y_obs'], axis=0)

print(f"Probability of passing for 5.5 hours studied: {pred_prob[0]:.2f}")

# Plot posterior distributions of the parameters
pm.plot_trace(trace)
plt.show()

# Plot decision boundary
x_range = np.linspace(0, 11, 100)
mu = np.mean(trace['alpha']) + np.mean(trace['beta']) * x_range
probabilities = 1 / (1 + np.exp(-mu))

plt.scatter(X, y, color='blue', label='Students')
plt.plot(x_range, probabilities, color='red', label='Decision Boundary')
plt.title('Bayesian Logistic Regression Decision Boundary')
plt.xlabel('Hours Studied')
plt.ylabel('Probability of Passing')
plt.xticks(np.arange(0, 12, 1))
plt.yticks(np.arange(0, 1.1, 0.1))
plt.legend()
plt.grid()
plt.show()
