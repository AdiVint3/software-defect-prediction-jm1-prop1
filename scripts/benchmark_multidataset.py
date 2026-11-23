from __future__ import annotations
import csv, gzip, io, json, math, sys, warnings, time, os
from pathlib import Path
import numpy as np
from scipy.io import arff
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             matthews_corrcoef, roc_auc_score, confusion_matrix)
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier
os.environ.setdefault("LOKY_MAX_CPU_COUNT","2")

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'DefectData_source'
OUT=ROOT/'results'/'MultiDataset_20x10'
FIG=OUT/'figures'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
DATASETS=[
 ('prop-2','ck','ck/prop-2.csv'),('prop-1','ck','ck/prop-1.csv'),
 ('eclipse-3.0','eclipse','eclipse/eclipse-3.0.csv'),('prop-3','ck','ck/prop-3.csv'),
 ('prop-4','ck','ck/prop-4.csv'),('prop-5','ck','ck/prop-5.csv'),
 ('eclipse-2.1','eclipse','eclipse/eclipse-2.1.csv'),('JM1','mccabe','mccabe/JM1.arff'),
 ('eclipse-2.0','eclipse','eclipse/eclipse-2.0.csv'),
 ('mylyn','ambros','ambros/mylyn.csv'),('PC5','mccabe','mccabe/PC5.arff'),
 ('pde','ambros','ambros/pde.csv'),('eclipse34_swt','kim','kim/eclipse34_swt.arff'),
 ('PC4','mccabe','mccabe/PC4.arff'),('PC3','mccabe','mccabe/PC3.arff'),
 ('eclipse34_debug','kim','kim/eclipse34_debug.arff'),('jdt','ambros','ambros/jdt.csv'),
 ('camel-1.6','ck','ck/camel-1.6.csv'),('xalan-2.6','ck','ck/xalan-2.6.csv'),
 ('camel-1.4','ck','ck/camel-1.4.csv')]
CK=['wmc','dit','noc','cbo','rfc','lcom','ca','ce','npm','lcom3','loc','dam','moa','mfa','cam','ic','cbm','amc','max_cc','avg_cc']
ECL=['pre','ACD','FOUT_avg','FOUT_max','FOUT_sum','MLOC_avg','MLOC_max','MLOC_sum','NBD_avg','NBD_max','NBD_sum','NOF_avg','NOF_max','NOF_sum','NOI','NOM_avg','NOM_max','NOM_sum','NOT','NSF_avg','NSF_max','NSF_sum','NSM_avg','NSM_max','NSM_sum','PAR_avg','PAR_max','PAR_sum','TLOC','VG_avg','VG_max','VG_sum']
MCCABE_TARGETS={'JM1':'label','ar1':'defects','ar3':'defects','ar4':'defects','ar5':'defects','ar6':'defects','kc2':'problems'}

def num(v):
    try:
        z=float(v)
        return z if np.isfinite(z) else np.nan
    except (ValueError,TypeError): return np.nan

def read_data(did,corpus,relative):
    path=DATA/relative
    source_path=path if path.exists() else Path(str(path)+'.gz')
    compressed=None
    if not source_path.exists():
        parts=sorted(DATA.glob(relative+'.gz.part*'))
        if parts: compressed=b''.join(p.read_bytes() for p in parts)
        else: raise FileNotFoundError(f'Could not find {path}, its compressed form, or multipart compressed source')
    if path.suffix.lower()=='.arff':
        source_handle=(gzip.open(io.BytesIO(compressed),'rb') if compressed is not None else (gzip.open(source_path,'rb') if source_path.suffix.lower()=='.gz' else source_path.open('rb')))
        with source_handle as source:
            data,_=arff.loadarff(source)
        names=list(data.dtype.names)
        values={n:np.array([v.decode('utf-8') if isinstance(v,bytes) else v for v in data[n]],dtype=object) for n in names}
        target='isDefective' if corpus=='kim' else MCCABE_TARGETS.get(did,'Defective')
        if target not in values: raise ValueError(f'missing target {target}')
        if corpus=='kim':
            features=[n for n in names if n not in (target,'defect_num')]
            positives={'buggy','true','1','yes','y'}
        else:
            features=[n for n in names if n!=target]
            positives={'y','true','yes','1'}
        y=np.array([int(str(v).strip().lower() in positives) for v in values[target]],dtype=int)
        X=np.column_stack([[num(v) for v in values[n]] for n in features]).astype(float)
    else:
        delimiter=';' if corpus in ('eclipse','ambros') else ','
        opener=(lambda: gzip.open(io.BytesIO(compressed),'rt',encoding='utf-8-sig',newline='')) if compressed is not None else ((lambda: gzip.open(source_path,'rt',encoding='utf-8-sig',newline='')) if source_path.suffix.lower()=='.gz' else (lambda: source_path.open('r',encoding='utf-8-sig',newline='')))
        with opener() as f:
            reader=csv.reader(f,delimiter=delimiter)
            header=[h.strip() for h in next(reader)]
            rows=list(reader)
        values={k:np.array([row[i].strip() if i<len(row) else '' for row in rows],dtype=object) for i,k in enumerate(header)}
        if corpus=='ck':
            target='bug'; features=CK
            y=np.array([int(num(v)>0) for v in values[target]],dtype=int)
        elif corpus=='eclipse':
            target='post'; features=ECL
            y=np.array([int(num(v)>0) for v in values[target]],dtype=int)
        elif corpus=='ambros':
            target='bugs'; features=header[1:16]
            y=np.array([int(num(v)>0) for v in values[target]],dtype=int)
        else:
            raise ValueError(f'unsupported csv corpus {corpus}')
        X=np.column_stack([[num(v) for v in values[n]] for n in features]).astype(float)
    # Remove predictor columns that are entirely missing, then use train-only median imputation in each model pipeline.
    keep=np.any(np.isfinite(X),axis=0)
    dropped=[n for n,k in zip(features,keep) if not k]
    X=X[:,keep]; features=[n for n,k in zip(features,keep) if k]
    X[~np.isfinite(X)]=np.nan
    return X,y,features,dropped

def make_groups(X):
    # NaN values get one stable sentinel for exact-vector grouping.
    safe=np.nan_to_num(X,nan=-9.87654321e99,posinf=9.87654321e99,neginf=-9.87654321e99)
    _,g=np.unique(safe,axis=0,return_inverse=True)
    return g

def build_folds(X,y,groups):
    class_group_counts=[]
    for cls in (0,1):
        class_group_counts.append(len(np.unique(groups[y==cls])))
    use_groups=min(class_group_counts)>=3
    if use_groups:
        splitter=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42)
        folds=list(splitter.split(X,y,groups))
        if all(len(np.unique(y[te]))==2 for _,te in folds) and all(len(np.unique(y[tr]))==2 for tr,_ in folds):
            return folds,'StratifiedGroupKFold; identical feature vectors kept together',class_group_counts
    folds=list(StratifiedKFold(n_splits=3,shuffle=True,random_state=42).split(X,y))
    if not all(len(np.unique(y[te]))==2 and len(np.unique(y[tr]))==2 for tr,te in folds):
        raise ValueError('could not form five folds with both classes in train and test')
    return folds,'StratifiedKFold fallback; duplicate-feature groups not fully isolated',class_group_counts

def make_models(y_train, seed):
    pos=int(np.sum(y_train==1)); neg=int(np.sum(y_train==0)); pos_weight=neg/max(pos,1)
    return {
      'Decision Tree': (Pipeline([('impute',SimpleImputer(strategy='median')),('model',DecisionTreeClassifier(max_depth=6,min_samples_leaf=10,class_weight='balanced',random_state=seed))]),'prob'),
      'KNN (k=5)': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',KNeighborsClassifier(n_neighbors=5,weights='uniform',metric='minkowski',p=2))]),'prob'),
      'XGBoost': (Pipeline([('impute',SimpleImputer(strategy='median')),('model',XGBClassifier(n_estimators=120,max_depth=4,learning_rate=.05,subsample=.8,colsample_bytree=.8,reg_lambda=1.0,scale_pos_weight=pos_weight,eval_metric='logloss',tree_method='hist',n_jobs=2,random_state=seed,verbosity=0))]),'prob'),
      'Random Forest': (Pipeline([('impute',SimpleImputer(strategy='median')),('model',RandomForestClassifier(n_estimators=120,min_samples_leaf=2,class_weight='balanced_subsample',n_jobs=2,random_state=seed))]),'prob'),
      'Linear SVM': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LinearSVC(C=1.0,class_weight='balanced',random_state=seed,dual='auto',max_iter=10000))]),'decision'),
      'Logistic Regression': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=1500,class_weight='balanced',solver='liblinear',random_state=seed))]),'prob'),
      'PCA + Logistic Regression': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('pca',PCA(n_components=.95,svd_solver='full')),('model',LogisticRegression(max_iter=1500,class_weight='balanced',solver='liblinear',random_state=seed))]),'prob'),
      'AdaBoost': (Pipeline([('impute',SimpleImputer(strategy='median')),('model',AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1,random_state=seed),n_estimators=80,learning_rate=.5,random_state=seed))]),'weighted_prob'),
      'Neural Network (MLP)': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',MLPClassifier(hidden_layer_sizes=(32,16),activation='relu',alpha=.001,learning_rate_init=.001,batch_size=256,max_iter=55,early_stopping=True,validation_fraction=.15,n_iter_no_change=6,random_state=seed))]),'oversample_prob'),
      'Gaussian Naive Bayes': (Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',GaussianNB(priors=[.5,.5],var_smoothing=1e-8))]),'prob')
    }

def score_from(model, Xte, kind):
    if kind.endswith('prob'):
        scores=model.predict_proba(Xte)[:,1]
    else:
        scores=model.decision_function(Xte)
    if kind=='decision': preds=(scores>=0).astype(int)
    else: preds=(scores>=.5).astype(int)
    return preds,scores

def fit_one(model,kind,Xtr,ytr,Xte,seed):
    sample_weight=compute_sample_weight('balanced',ytr)
    fit_model=clone(model)
    if kind=='weighted_prob':
        fit_model.fit(Xtr,ytr,model__sample_weight=sample_weight)
    elif kind=='oversample_prob':
        rng=np.random.default_rng(seed)
        idx0=np.flatnonzero(ytr==0); idx1=np.flatnonzero(ytr==1)
        n=max(len(idx0),len(idx1))
        ii=np.concatenate([rng.choice(idx0,n,replace=len(idx0)<n),rng.choice(idx1,n,replace=len(idx1)<n)])
        rng.shuffle(ii)
        fit_model.fit(Xtr[ii],ytr[ii])
    else:
        fit_model.fit(Xtr,ytr)
    return fit_model

def metric_row(did,model_name,fold_i,yte,pred,scores):
    cm=confusion_matrix(yte,pred,labels=[1,0])
    tn,fp,fn,tp=int(cm[1,1]),int(cm[1,0]),int(cm[0,1]),int(cm[0,0])
    return {'dataset':did,'model':model_name,'fold':fold_i,'n_test':len(yte),'test_defects':int(yte.sum()),
            'accuracy':accuracy_score(yte,pred),'precision':precision_score(yte,pred,zero_division=0),
            'recall':recall_score(yte,pred,zero_division=0),'f1':f1_score(yte,pred,zero_division=0),
            'mcc':matthews_corrcoef(yte,pred),'roc_auc':roc_auc_score(yte,scores),
            'tp':tp,'fp':fp,'tn':tn,'fn':fn}

def save_csv(path,rows,fields=None):
    if not rows and fields is None:return
    if fields is None: fields=list(rows[0].keys())
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

start=time.time(); all_fold=[]; inventory=[]; importances=[]; failures=[]; baseline_fold=[]; model_order=None
selected_datasets=DATASETS[:int(os.environ.get('BENCH_LIMIT',len(DATASETS)))]
for di,(did,corpus,rel) in enumerate(selected_datasets,1):
    X,y,features,dropped=read_data(did,corpus,rel)
    counts=np.bincount(y,minlength=2)
    if counts.min()<50: raise ValueError(f'{did} fails minimum class support: {counts.tolist()}')
    groups=make_groups(X)
    folds,split_name,group_support=build_folds(X,y,groups)
    inventory.append({'dataset':did,'corpus':corpus,'source_file':rel,'n_rows':len(y),'n_features':len(features),
      'defective':int(y.sum()),'non_defective':int((1-y).sum()),'defect_rate':float(y.mean()),
      'missing_cells_before_imputation':int(np.isnan(X).sum()),'duplicate_feature_rows':int(len(y)-len(np.unique(groups))),
      'unique_feature_vectors':int(len(np.unique(groups))),'feature_columns_dropped_all_missing':';'.join(dropped),
      'split_strategy':split_name,'class_group_counts':';'.join(map(str,group_support))})
    print(f'[{di:02}/{len(selected_datasets)}] {did}: n={len(y)}, p={len(features)}, defects={counts[1]}, split={split_name}',flush=True)
    dataset_rows=[]
    for fold_i,(tr,te) in enumerate(folds,1):
        if len(np.unique(y[tr]))<2 or len(np.unique(y[te]))<2: raise ValueError(f'{did} fold {fold_i} lacks a class')
        baseline_label=int(np.mean(y[tr])>=0.5)
        bp=np.full(len(te),baseline_label,dtype=int)
        bcm=confusion_matrix(y[te],bp,labels=[1,0])
        baseline_fold.append({'dataset':did,'fold':fold_i,'n_test':len(te),'test_defects':int(y[te].sum()),'majority_class_predicted':baseline_label,'accuracy':accuracy_score(y[te],bp),'precision':precision_score(y[te],bp,zero_division=0),'recall':recall_score(y[te],bp,zero_division=0),'f1':f1_score(y[te],bp,zero_division=0),'mcc':matthews_corrcoef(y[te],bp),'roc_auc':'NA','tp':int(bcm[0,0]),'fn':int(bcm[0,1]),'fp':int(bcm[1,0]),'tn':int(bcm[1,1])})
        models=make_models(y[tr],42+fold_i)
        if model_order is None:model_order=list(models)
        fold_features=[]
        for model_name,(model,kind) in models.items():
            try:
                print(f'    fitting {model_name} fold {fold_i}',flush=True)
                fitted=fit_one(model,kind,X[tr],y[tr],X[te],42+fold_i)
                pred,scores=score_from(fitted,X[te],kind)
                row=metric_row(did,model_name,fold_i,y[te],pred,scores)
                row['split_strategy']=split_name
                dataset_rows.append(row); all_fold.append(row)
                save_csv(OUT/'fold_metrics.csv',all_fold)
                print(f'    done {model_name}: AUC={row["roc_auc"]:.3f} F1={row["f1"]:.3f}',flush=True)
                if model_name=='Random Forest':
                    rf=fitted.named_steps['model']
                    norm=rf.feature_importances_
                    total=norm.sum()
                    if total>0:
                        fold_features.extend({'dataset':did,'fold':fold_i,'feature':fn,'importance':float(v/total)} for fn,v in zip(features,norm))
            except Exception as e:
                failures.append({'dataset':did,'model':model_name,'fold':fold_i,'error':repr(e)})
                print(f'  ERROR {model_name} fold {fold_i}: {e}',flush=True)
        importances.extend(fold_features)
    save_csv(OUT/'fold_metrics.csv',all_fold)
    save_csv(OUT/'dataset_inventory.csv',inventory)
    save_csv(OUT/'model_failures.csv',failures,['dataset','model','fold','error'])
    if dataset_rows:
        print(f'  finished {did}: {len(dataset_rows)} model-fold scores; elapsed {time.time()-start:.1f}s',flush=True)

if failures:
    print(f'WARNING: {len(failures)} model fits failed; see model_failures.csv',flush=True)
# Aggregate folds within each dataset, then treat datasets equally for macro summaries.
metrics=['accuracy','precision','recall','f1','mcc','roc_auc']
dm={}
for row in all_fold: dm.setdefault((row['dataset'],row['model']),[]).append(row)
dataset_summary=[]
for (did,mod),rows in dm.items():
    item={'dataset':did,'model':mod,'folds_completed':len(rows)}
    for met in metrics:item[met]=float(np.mean([r[met] for r in rows]))
    dataset_summary.append(item)
summary=[]
for mod in (model_order or []):
    rr=[r for r in dataset_summary if r['model']==mod]
    item={'model':mod,'datasets_evaluated':len(rr)}
    for met in metrics:
        vals=np.array([r[met] for r in rr],dtype=float)
        item[met+'_macro_mean']=float(vals.mean()) if len(vals) else None
        item[met+'_macro_sd']=float(vals.std(ddof=1)) if len(vals)>1 else 0.0
    summary.append(item)
save_csv(OUT/'dataset_model_summary.csv',dataset_summary)
save_csv(OUT/'overall_macro_summary.csv',summary)
save_csv(OUT/'model_failures.csv',failures,['dataset','model','fold','error'])
# Non-algorithm majority-class reference, kept separate from the ten classifiers.
base_by={}
for row in baseline_fold:base_by.setdefault(row['dataset'],[]).append(row)
base_summary=[]
for did,rows in base_by.items():
 item={'dataset':did,'folds':len(rows)}
 for met in ('accuracy','precision','recall','f1','mcc'):item[met]=float(np.mean([r[met] for r in rows]))
 base_summary.append(item)
base_overall={'dataset_count':len(base_summary)}
for met in ('accuracy','precision','recall','f1','mcc'):
 vals=np.array([r[met] for r in base_summary],dtype=float)
 base_overall[met+'_macro_mean']=float(vals.mean());base_overall[met+'_macro_sd']=float(vals.std(ddof=1))
save_csv(OUT/'majority_baseline_fold_metrics.csv',baseline_fold)
save_csv(OUT/'majority_baseline_by_dataset.csv',base_summary)
save_csv(OUT/'majority_baseline_macro_summary.csv',[base_overall])
# One pooled score per algorithm across all held-out rows. The same system versions are kept as separate projects.
pooled=[]
for mod in (model_order or []):
    rr=[r for r in all_fold if r['model']==mod]
    if not rr:continue
    sums={k:sum(r[k] for r in rr) for k in ('tp','fp','tn','fn')}
    tp,fp,tn,fn=(sums['tp'],sums['fp'],sums['tn'],sums['fn'])
    pooled.append({'model':mod,'held_out_rows':sum(r['n_test'] for r in rr),
      'accuracy':(tp+tn)/(tp+fp+tn+fn),'precision':tp/(tp+fp) if tp+fp else 0,
      'recall':tp/(tp+fn) if tp+fn else 0,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0,
      'mcc':((tp*tn-fp*fn)/math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))) if (tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)>0 else 0,
      'roc_auc_pooled_unavailable':'Use per-dataset fold ROC AUC macro; scores are on different dataset scales.'})
save_csv(OUT/'overall_pooled_confusion_summary.csv',pooled)
# Average normalized Random Forest impurity importance across each dataset/fold and plot top features.
impmean={}
for r in importances: impmean.setdefault(r['feature'],[]).append(r['importance'])
imp_rows=sorted([{'feature':k,'mean_normalized_importance':float(np.mean(v)),'datasets_present':len(set(r['dataset'] for r in importances if r['feature']==k))} for k,v in impmean.items()],key=lambda x:x['mean_normalized_importance'],reverse=True)
save_csv(OUT/'random_forest_feature_importance.csv',imp_rows)
(OUT/'benchmark_summary.json').write_text(json.dumps({'scope':{'dataset_count':len(selected_datasets),'selection_criteria':'20 highest-row-count datasets from the repository after requiring at least 50 defective and 50 non-defective observations','model_count':len(model_order or []),'folds_per_dataset':3,'scoring':'fixed probability threshold 0.5; linear SVM uses zero decision boundary','metric_aggregation':'mean across folds within dataset, then unweighted macro mean across datasets','grouping':'identical numeric feature vectors assigned to one fold when group class support permits','random_state':42,'datasets':[d[0] for d in selected_datasets]},'models':model_order,'failures':failures,'dataset_inventory':inventory,'overall_macro':summary,'pooled_confusion':pooled,'majority_class_baseline_macro':base_overall,'feature_importance':imp_rows},indent=2))
# Figures: macro model metric distributions, dataset x model heatmaps, feature ranking.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':12,'axes.labelsize':9})
order=[d[0] for d in selected_datasets]
colors=['#345995','#03CEA4','#FB4D3D','#CA1551','#EAC435','#8D5A97','#4F6D7A','#F08A4B','#6A994E','#577590']
fig,axes=plt.subplots(1,3,figsize=(15,5.4),constrained_layout=True)
for ax,met,title in zip(axes,['roc_auc','f1','mcc'],['ROC AUC','F1 score','Matthews correlation']):
    data=[[r[met] for r in dataset_summary if r['model']==m] for m in (model_order or [])]
    bp=ax.boxplot(data,patch_artist=True,showmeans=True,meanline=True,medianprops={'color':'#222222','linewidth':1.2},whiskerprops={'color':'#506070'},capprops={'color':'#506070'},flierprops={'marker':'.','markersize':3,'markerfacecolor':'#7E8C99','markeredgecolor':'none'})
    for patch,c in zip(bp['boxes'],colors):patch.set_facecolor(c);patch.set_alpha(.75)
    ax.set_xticks(range(1,len(model_order or [])+1));ax.set_xticklabels(model_order,rotation=55,ha='right');ax.set_title(title);ax.set_ylabel('Dataset mean score (three grouped folds)');ax.grid(axis='y',alpha=.25);ax.set_ylim((-1,1) if met=='mcc' else (0,1))
fig.suptitle('Ten classifiers across 20 software defect datasets',fontsize=14,fontweight='bold')
fig.savefig(FIG/'model_performance_boxplots.png',dpi=220,bbox_inches='tight');plt.close(fig)
for met,title in [('roc_auc','ROC AUC by dataset and classifier'),('f1','F1 score by dataset and classifier')]:
    matrix=np.array([[next(r[met] for r in dataset_summary if r['dataset']==ds and r['model']==m) if any(r['dataset']==ds and r['model']==m for r in dataset_summary) else np.nan for m in (model_order or [])] for ds in order])
    fig,ax=plt.subplots(figsize=(14,9),constrained_layout=True)
    im=ax.imshow(matrix,aspect='auto',cmap='YlGnBu',vmin=0,vmax=1)
    ax.set_xticks(range(len(model_order or [])));ax.set_xticklabels(model_order,rotation=45,ha='right');ax.set_yticks(range(len(order)));ax.set_yticklabels(order)
    ax.set_title(title,fontweight='bold');ax.set_xlabel('Classifier');ax.set_ylabel('Dataset')
    for i in range(matrix.shape[0]):
     for j in range(matrix.shape[1]):
      if np.isfinite(matrix[i,j]):ax.text(j,i,f'{matrix[i,j]:.2f}',ha='center',va='center',fontsize=6.5,color='black' if matrix[i,j]<.62 else 'white')
    fig.colorbar(im,ax=ax,label='Dataset mean score');fig.savefig(FIG/f'{met}_heatmap.png',dpi=220,bbox_inches='tight');plt.close(fig)
if imp_rows:
    top=imp_rows[:20][::-1]
    fig,ax=plt.subplots(figsize=(9,7),constrained_layout=True)
    ax.barh([r['feature'] for r in top],[r['mean_normalized_importance'] for r in top],color='#167D8D')
    ax.set_xlabel('Mean normalized Random Forest impurity importance');ax.set_title('Most important software metrics across selected datasets',fontweight='bold');ax.grid(axis='x',alpha=.2)
    fig.savefig(FIG/'random_forest_feature_importance.png',dpi=220,bbox_inches='tight');plt.close(fig)
print('\nOVERALL MACRO SUMMARY (datasets equally weighted)',flush=True)
for r in summary:print(r['model'], 'AUC',round(r['roc_auc_macro_mean'],3),'F1',round(r['f1_macro_mean'],3),'MCC',round(r['mcc_macro_mean'],3),flush=True)
print(f'Completed {len(dataset_summary)} dataset-model summaries; {len(all_fold)} fold scores; {len(failures)} failures; elapsed {time.time()-start:.1f}s',flush=True)

