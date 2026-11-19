import csv, json, re
from pathlib import Path
import numpy as np
import sys
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, roc_curve, classification_report)
from sklearn.inspection import permutation_importance

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'/'JM1'; RESULTS.mkdir(parents=True, exist_ok=True)
arff=ROOT/'data'/'JM1.arff'
attrs=[]; rows=[]; in_data=False
for line in arff.read_text(encoding='utf-8').splitlines():
    line=line.strip()
    if not line or line.startswith('%'): continue
    if not in_data:
        if line.lower().startswith('@attribute'):
            m=re.match(r"@attribute\s+(['\"]?)([^\s'\"]+)\1\s+(.+)",line,re.I)
            attrs.append((m.group(2),m.group(3)))
        if line.lower()=='@data': in_data=True
    else:
        rows.append(next(csv.reader([line])))
cols=[a[0] for a in attrs]
arr=np.array(rows,dtype=object)
y=np.array([1 if str(v).strip().lower() in ('y','true','yes','1') else 0 for v in arr[:,-1]], dtype=int)
X=np.array([[float(v) if v not in ('?','') else np.nan for v in row[:-1]] for row in arr],dtype=float)
feature_names=cols[:-1]
missing=int(np.isnan(X).sum()); dup=int(len(X)-len({tuple(row) for row in arr.tolist()}))
train_idx,test_idx=train_test_split(np.arange(len(y)),test_size=.2,random_state=42,stratify=y)
Xtr,Xte=X[train_idx],X[test_idx]; ytr,yte=y[train_idx],y[test_idx]
models={
 'Decision Tree': DecisionTreeClassifier(max_depth=6,min_samples_leaf=10,class_weight='balanced',random_state=42),
 'KNN (k=5)': Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('knn',KNeighborsClassifier(n_neighbors=5,weights='uniform',metric='minkowski',p=2))]),
 'XGBoost': XGBClassifier(n_estimators=300,max_depth=4,learning_rate=0.05,subsample=0.8,
     colsample_bytree=0.8,reg_lambda=1.0,scale_pos_weight=float((ytr==0).sum()/(ytr==1).sum()),
     eval_metric='logloss',tree_method='hist',n_jobs=4,random_state=42)
}
results={}; fitted={}
for name,model in models.items():
    model.fit(Xtr,ytr); fitted[name]=model
    pred=model.predict(Xte)
    prob=model.predict_proba(Xte)[:,1]
    cm=confusion_matrix(yte,pred,labels=[1,0])
    fpr,tpr,thresholds=roc_curve(yte,prob)
    # top decile by estimated risk; gains = fraction of all defects in highest-scored 10% / 10%
    n=max(1,int(np.ceil(.1*len(yte))))
    top=np.argsort(prob)[::-1][:n]
    captured=int(yte[top].sum()); total=int(yte.sum())
    ordered=np.argsort(prob)[::-1]
    cumulative=[]
    for decile in range(1,11):
      end=min(len(yte),int(np.ceil(decile*len(yte)/10)))
      cumulative.append({'population_fraction':end/len(yte),'defects_captured_fraction':float(yte[ordered[:end]].sum()/total) if total else 0})
    results[name]={
      'confusion_matrix_labels':['Defective','Non-defective'],
      'confusion_matrix':cm.tolist(),
      'accuracy':float(accuracy_score(yte,pred)),
      'precision':float(precision_score(yte,pred,zero_division=0)),
      'recall':float(recall_score(yte,pred,zero_division=0)),
      'f1':float(f1_score(yte,pred,zero_division=0)),
      'auc':float(roc_auc_score(yte,prob)),
      'test_support':len(yte), 'predicted_positive':int(pred.sum()),
      'top_decile_n':n,'top_decile_defects_captured':captured,'test_defects':total,
      'top_decile_recall':captured/total if total else 0,
      'top_decile_lift':(captured/n)/(total/len(yte)) if total else 0,
      'cumulative_gains':cumulative,
      'roc':{'fpr':fpr.tolist(),'tpr':tpr.tolist()}
    }

# descriptive summary and Pearson rank correlation summaries on training data only
summaries={}
for j,name in enumerate(feature_names):
    vals=X[:,j]; vals=vals[np.isfinite(vals)]
    if len(vals):
        summaries[name]={'mean':float(np.mean(vals)),'median':float(np.median(vals)),'sd':float(np.std(vals,ddof=1)),
                         'variance':float(np.var(vals,ddof=1)), 'skewness':float(np.mean(((vals-np.mean(vals))/np.std(vals))**3)),
                         'kurtosis_excess':float(np.mean(((vals-np.mean(vals))/np.std(vals))**4)-3)}
    else: summaries[name]={}
# correlation among selected metrics; Pearson and Spearman (rank-transform)
selected=['LOC_TOTAL','BRANCH_COUNT','CYCLOMATIC_COMPLEXITY','HALSTEAD_VOLUME','NUM_OPERANDS']
correlations={}
for method in ('pearson','spearman'):
    mat=np.column_stack([X[:,feature_names.index(f)] for f in selected])
    if method=='spearman':
        from scipy.stats import rankdata
        mat=np.column_stack([rankdata(mat[:,i],nan_policy='omit') for i in range(mat.shape[1])])
    correlations[method]=np.corrcoef(mat,rowvar=False).tolist()

out={'dataset':{'name':'JM1','source':'klainfo/DefectData inst/extdata/terapromise/mccabe/JM1.arff',
      'n_rows':len(y),'n_features':len(feature_names),'class_counts':{'defective':int(y.sum()),'non_defective':int((1-y).sum())},
      'defect_rate':float(y.mean()),'missing_feature_cells':missing,'duplicate_rows':dup,'feature_names':feature_names,
      'train_n':len(train_idx),'test_n':len(test_idx),'train_defects':int(ytr.sum()),'test_defects':int(yte.sum()),
      'seed':42,'test_size':.2},'metrics':results,'descriptives':summaries,'correlation_features':selected,'correlations':correlations}
import sklearn, xgboost
out['software_versions']={'scikit_learn':sklearn.__version__,'xgboost':xgboost.__version__}
for name,model in fitted.items():
    if name=='Decision Tree':
      out['decision_tree']={'depth':model.get_depth(),'leaves':model.get_n_leaves(),
        'top_features':sorted(zip(feature_names,model.feature_importances_.tolist()),key=lambda x:x[1],reverse=True)[:10]}
    if name=='XGBoost':
      out['xgboost']={'parameters':model.get_params(),
        'top_features':sorted(zip(feature_names,model.feature_importances_.tolist()),key=lambda x:x[1],reverse=True)[:10]}
(RESULTS/'analysis_results.json').write_text(json.dumps(out,indent=2,default=lambda v: v.item() if hasattr(v,'item') else str(v)))
print(json.dumps(out['dataset'],indent=2))
print(json.dumps(out['metrics'],indent=2))
print(json.dumps(out['decision_tree'],indent=2,default=lambda v: v.item() if hasattr(v,'item') else str(v)))
print('descriptive LOC_TOTAL',summaries['LOC_TOTAL'])
print('corr matrix',json.dumps(out['correlations'],indent=2))
