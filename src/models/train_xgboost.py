import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data/processed/player_data.csv")

# Drop unnecessary columns
df = df.drop(columns=["steam_id", "last_logoff"])

# Split
X = df.drop(columns=["churn"])
y = df["churn"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y   # 🔥 ADD THIS
)

# Train XGBoost
model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42
)

model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluate
print("\nXGBoost Performance:\n")
print(classification_report(y_test, y_pred))
# Get feature importance
importance = model.feature_importances_
features = X.columns

# Print nicely
print("\nFeature Importance:\n")
for f, imp in zip(features, importance):
    print(f"{f}: {imp:.4f}")

# Plot
plt.figure(figsize=(8, 5))
plt.barh(features, importance)
plt.xlabel("Importance Score")
plt.title("Feature Importance (XGBoost)")
plt.show()
