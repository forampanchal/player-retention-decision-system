import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report


# Load dataset
df = pd.read_csv("data/processed/player_data.csv")

# Drop non-useful columns
df = df.drop(columns=["steam_id", "last_logoff"])

# Features and target
X = df.drop(columns=["churn"])
y = df["churn"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluation
print("\nModel Performance:\n")
print(classification_report(y_test, y_pred))
