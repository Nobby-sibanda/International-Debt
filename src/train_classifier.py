"""Predict IMF debt-distress risk (High/In distress vs Low/Moderate) from
World Bank debt-composition and macro features.

Two models are compared:
  - Logistic regression (scaled, L2-regularized) -- interpretable baseline.
  - Gradient-boosted trees -- captures nonlinear/interaction effects.

Given the small labeled sample (n=63, one country = one row), evaluation
leans on 5-fold stratified cross-validation rather than a single holdout
split, with a held-out test set reported alongside it for a confusion
matrix / ROC curve snapshot.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (RocCurveDisplay, auc, confusion_matrix,
                              roc_auc_score, roc_curve)
from sklearn.model_selection import (StratifiedKFold, cross_val_score,
                                      train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
    "debt_pct_gni", "debt_pct_gdp", "debt_service_pct_exports",
    "debt_service_pct_debt", "reserves_to_debt", "short_term_share",
    "public_ppg_share", "private_png_share", "multilateral_share",
    "debt_per_capita_usd", "gdp_per_capita_usd",
]
# `region` was tried too (see model card) but its 6 levels against n=63 add
# more noise than signal in cross-validation, so only income_level is kept.
CATEGORICAL_FEATURES = ["income_level"]
TARGET = "high_risk"


def make_preprocessor():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def feature_names(preprocessor):
    num_names = NUMERIC_FEATURES
    cat_names = list(
        preprocessor.named_transformers_["cat"]
        .named_steps["onehot"].get_feature_names_out(CATEGORICAL_FEATURES)
    )
    return num_names + cat_names


def main():
    df = pd.read_csv("data/labeled_features.csv")
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.3),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=50, max_depth=2, learning_rate=0.05, random_state=42
        ),
    }

    metrics = {"n_labeled": len(df), "n_high_risk": int(y.sum()),
               "n_low_risk": int((1 - y).sum()), "features": NUMERIC_FEATURES,
               "models": {}}

    fig, ax = plt.subplots(figsize=(6, 5))

    for name, estimator in models.items():
        pipe = Pipeline([("prep", make_preprocessor()), ("clf", estimator)])

        cv_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")

        pipe.fit(X_train, y_train)
        proba_test = pipe.predict_proba(X_test)[:, 1]
        pred_test = pipe.predict(X_test)

        cm = confusion_matrix(y_test, pred_test)
        test_auc = roc_auc_score(y_test, proba_test)

        fpr, tpr, _ = roc_curve(y_test, proba_test)
        ax.plot(fpr, tpr, label=f"{name} (test AUC={test_auc:.2f})")

        prep = pipe.named_steps["prep"]
        clf = pipe.named_steps["clf"]
        names = feature_names(prep)
        if hasattr(clf, "coef_"):
            importances = dict(zip(names, clf.coef_[0].round(3).tolist()))
        else:
            importances = dict(zip(names, clf.feature_importances_.round(3).tolist()))
        importances = dict(sorted(importances.items(), key=lambda kv: -abs(kv[1])))

        metrics["models"][name] = {
            "cv_roc_auc_mean": round(cv_scores.mean(), 3),
            "cv_roc_auc_std": round(cv_scores.std(), 3),
            "cv_roc_auc_folds": [round(s, 3) for s in cv_scores],
            "test_roc_auc": round(test_auc, 3),
            "test_confusion_matrix": cm.tolist(),
            "test_confusion_matrix_labels": ["low/moderate risk", "high risk/distress"],
            "feature_importance": importances,
            "roc_fpr": [round(v, 4) for v in fpr.tolist()],
            "roc_tpr": [round(v, 4) for v in tpr.tolist()],
        }

        pd.to_pickle(pipe, f"models/classifier_{name}.pkl")

        print(f"\n{name}")
        print(f"  5-fold CV ROC-AUC: {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}")
        print(f"  Held-out test ROC-AUC: {test_auc:.3f}")
        print(f"  Confusion matrix (rows=actual, cols=predicted):\n{cm}")
        print("  Top features:", list(importances.items())[:5])

    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Debt-distress classifier -- ROC curve (held-out test set)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("models/figures/roc_curve.png", dpi=150)

    # Confusion matrices, side by side.
    fig_cm, axes_cm = plt.subplots(1, 2, figsize=(9, 4))
    for axc, (name, m) in zip(axes_cm, metrics["models"].items()):
        cm = np.array(m["test_confusion_matrix"])
        axc.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            axc.text(j, i, str(v), ha="center", va="center", fontsize=14)
        axc.set_xticks([0, 1]); axc.set_yticks([0, 1])
        axc.set_xticklabels(["low/mod", "high/distress"])
        axc.set_yticklabels(["low/mod", "high/distress"])
        axc.set_xlabel("Predicted"); axc.set_ylabel("Actual")
        axc.set_title(name)
    fig_cm.tight_layout()
    fig_cm.savefig("models/figures/confusion_matrices.png", dpi=150)

    # Feature importance for the logistic regression (signed coefficients).
    lr_importance = metrics["models"]["logistic_regression"]["feature_importance"]
    top = dict(list(lr_importance.items())[:10])
    fig_fi, ax_fi = plt.subplots(figsize=(7, 5))
    colors = ["#c0392b" if v > 0 else "#2980b9" for v in top.values()]
    ax_fi.barh(list(top.keys())[::-1], list(top.values())[::-1], color=colors[::-1])
    ax_fi.set_xlabel("Logistic regression coefficient (standardized features)")
    ax_fi.set_title("Top predictors of high debt-distress risk")
    fig_fi.tight_layout()
    fig_fi.savefig("models/figures/feature_importance.png", dpi=150)

    with open("models/classifier_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved models/classifier_*.pkl, models/classifier_metrics.json, "
          "models/figures/roc_curve.png")


if __name__ == "__main__":
    main()
