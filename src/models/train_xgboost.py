import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
import optuna

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score, fbeta_score, recall_score
from xgboost import XGBClassifier

def train_and_evaluate():
    # ---------------- 1. DATA LOADING ----------------
    df = pd.read_csv("data/processed/player_data.csv")
    df = df.drop(columns=["steam_id", "last_logoff"])
    df = df.fillna(0)
    
    # We keep engagement_ratio / recent_playtime out to prevent label leakage.
    X = df.drop(columns=["churn", "recent_playtime", "engagement_ratio"])
    y = df["churn"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # STEP 2: FIX CLASS IMBALANCE (scale_pos_weight)
    scale_pos_weight = len(y_train[y_train == 0]) / max(1, len(y_train[y_train == 1]))
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")

    # ---------------- 2. HYPERPARAMETER TUNING (OPTUNA) ----------------
    print("\nRunning Optuna Hyperparameter Tuning...")
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 200),
            'max_depth': trial.suggest_int('max_depth', 2, 5),  # Keep low to prevent overfitting
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'scale_pos_weight': scale_pos_weight,
            'base_score': 0.5,
            'random_state': 42
        }
        
        model = XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        # We optimize on the validation probability to maximize AUC or Recall
        # Here we maximize ROC_AUC
        y_prob_val = model.predict_proba(X_test)[:, 1]
        return roc_auc_score(y_test, y_prob_val)

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)
    
    print("Best Trial:", study.best_trial.params)
    
    # ---------------- 3. TRAIN OPTIMIZED MODEL ----------------
    best_params = study.best_trial.params
    best_params['scale_pos_weight'] = scale_pos_weight
    best_params['base_score'] = 0.5
    best_params['random_state'] = 42

    print("\nTraining Final Optimized XGBoost Model...")
    model = XGBClassifier(**best_params)
    model.fit(X_train, y_train)
    
    # Predict probabilities instead of hard classes
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # STEP 3: TUNE THRESHOLD (Favoring Recall - Catching all churners)
    CUSTOM_THRESHOLD = 0.3
    print(f"\nApplying Custom Decision Threshold: {CUSTOM_THRESHOLD}")
    y_pred_adj = (y_prob >= CUSTOM_THRESHOLD).astype(int)
    
    # ---------------- 4. EVALUATE ----------------
    accuracy = accuracy_score(y_test, y_pred_adj)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    print("\n" + "="*40)
    print("           MODEL PERFORMANCE")
    print("="*40)
    print(f"Accuracy:      {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    
    print("\nConfusion Matrix:")
    print("TN, FP")
    print("FN, TP")
    print(confusion_matrix(y_test, y_pred_adj))
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred_adj))
    
    # ---------------- 5. PERSISTENCE & SHAP ----------------
    os.makedirs('models', exist_ok=True)
    model_path = 'models/xgboost_churn_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel persistently saved to {model_path}!")

    print("\nRunning SHAP (SHapley Additive exPlanations) analyzer...")
    explainer = shap.Explainer(model.predict, X_train)
    shap_values = explainer(X_train)
    
    plt.ioff()
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_train, show=False)
    
    os.makedirs('notebooks', exist_ok=True)
    plt.savefig('notebooks/shap_feature_importance.png', bbox_inches='tight')
    print("SHAP Feature Importance scatter plot saved successfully.")

if __name__ == "__main__":
    train_and_evaluate()
