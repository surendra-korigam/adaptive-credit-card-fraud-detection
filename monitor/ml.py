from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, StackingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, average_precision_score, confusion_matrix

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"/"creditcard.csv"
ART=ROOT/"artifacts"
ART.mkdir(exist_ok=True)
FEATURES=["Time"]+[f"V{i}" for i in range(1,29)]+["Amount"]

def train():
    if not DATA.exists():
        raise FileNotFoundError(f"Dataset missing: {DATA}. Download Kaggle ULB creditcard.csv and place it in data/")
    df=pd.read_csv(DATA)
    required=set(FEATURES+["Class"])
    if not required.issubset(df.columns):
        raise ValueError("CSV must be the ULB creditcard.csv with Time, V1..V28, Amount, Class columns.")
    df=df[FEATURES+["Class"]].dropna()
    X=df[FEATURES].astype("float32").values
    y=df["Class"].astype("int8").values
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    scaler=StandardScaler()
    Xtr=scaler.fit_transform(X_train)
    Xte=scaler.transform(X_test)
    # Class weighting makes the rare fraud class visible during fitting.
    estimators=[
      ("decision_tree",DecisionTreeClassifier(max_depth=12,min_samples_leaf=3,class_weight="balanced",random_state=42)),
      ("random_forest",RandomForestClassifier(n_estimators=100,max_depth=16,min_samples_leaf=2,
          class_weight="balanced_subsample",n_jobs=-1,random_state=42)),
      ("extra_trees",ExtraTreesClassifier(n_estimators=80,max_depth=16,min_samples_leaf=2,
          class_weight="balanced",n_jobs=-1,random_state=42))
    ]
    model=StackingClassifier(estimators=estimators,final_estimator=LogisticRegression(
        class_weight="balanced",max_iter=1000),stack_method="predict_proba",cv=3,n_jobs=-1)
    model.fit(Xtr,y_train)
    probs=model.predict_proba(Xte)[:,1]
    # Default threshold is intentionally conservative and can be adjusted in the UI later.
    preds=(probs>=0.5).astype(int)
    metrics={
      "rows":int(len(df)),"train_rows":int(len(y_train)),"test_rows":int(len(y_test)),
      "fraud_rows":int(y.sum()),"accuracy":float(accuracy_score(y_test,preds)),
      "precision":float(precision_score(y_test,preds,zero_division=0)),
      "recall":float(recall_score(y_test,preds,zero_division=0)),
      "f1":float(f1_score(y_test,preds,zero_division=0)),
      "pr_auc":float(average_precision_score(y_test,probs)),
      "confusion_matrix":confusion_matrix(y_test,preds).tolist(),
      "threshold":0.5
    }
    joblib.dump({"model":model,"scaler":scaler,"features":FEATURES,"metrics":metrics},ART/"fraud_model.joblib")
    (ART/"metrics.json").write_text(__import__("json").dumps(metrics,indent=2))
    return metrics

def load_artifact():
    p=ART/"fraud_model.joblib"
    if not p.exists(): return None
    return joblib.load(p)

def predict_row(row, bundle=None):
    bundle=bundle or load_artifact()
    if bundle is None: raise RuntimeError("Train the model first: python train_model.py")
    x=np.array([[float(row[c]) for c in bundle["features"]]],dtype="float32")
    p=float(bundle["model"].predict_proba(bundle["scaler"].transform(x))[0,1])
    decision="BLOCK" if p>=.5 else ("REVIEW" if p>=.2 else "APPROVE")
    return p,decision
