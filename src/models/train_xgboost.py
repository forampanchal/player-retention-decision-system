import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score
from xgboost import XGBClassifier

def train_and_evaluate():
    # Load data
    df = pd.read_csv("data/processed/player_data.csv")
    
    # Drop unnecessary/non-numerical columns
    df = df.drop(columns=["steam_id", "last_logoff"])
    
    # Optional: Fill NaN values if any slipped through
    df = df.fillna(0)
    
    # Split features and target
    X = df.drop(columns=["churn"])
    y = df["churn"]
    
    # Train-test split with stratify for imbalanced data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    # Calculate pos_weight for XGBoost to handle class imbalance (83% / 17%)
    scale_pos_weight = len(y_train[y_train == 0]) / max(1, len(y_train[y_train == 1]))
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        scale_pos_weight=scale_pos_weight,
        base_score=0.5
    )
    
    print("Training XGBoost Model...")
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Evaluate Accuracy and ROC-AUC
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    print("\n" + "="*40)
    print("           MODEL PERFORMANCE")
    print("="*40)
    print(f"Accuracy:      {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    
    print("\nConfusion Matrix:")
    print("True Negables (TN), False Positives (FP)")
    print("False Negatives (FN), True Positives (TP)")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Persistence: Save the model!
    os.makedirs('models', exist_ok=True)
    model_path = 'models/xgboost_churn_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel persistently saved to {model_path}!")

    # SHAP Explainability
    print("\nRunning SHAP (SHapley Additive exPlanations) analyzer...")
    # Using model agnostic Explainer to avoid XGBoost 2.1+ C-API parsing bug in SHAP
    explainer = shap.Explainer(model.predict, X_train)
    shap_values = explainer(X_train)
    
    # Disable Pyplot interactive mode for writing to a file seamlessly
    plt.ioff()
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_train, show=False)
    
    os.makedirs('notebooks', exist_ok=True)
    plt.savefig('notebooks/shap_feature_importance.png', bbox_inches='tight')
    print("SHAP Feature Importance scatter plot saved as 'notebooks/shap_feature_importance.png'")

if __name__ == "__main__":
    train_and_evaluate()
