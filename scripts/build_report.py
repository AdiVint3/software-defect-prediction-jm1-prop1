import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"JM1"; OUT.mkdir(parents=True, exist_ok=True)
FIG_DIR=ROOT/"results"/"JM1"/"figures"; FIG_DIR.mkdir(parents=True, exist_ok=True)
A=json.loads((ROOT/"results"/"JM1"/"analysis_results.json").read_text())
D=A["dataset"]; M=A["metrics"]; S=A["descriptives"]; BLUE="193653"; TEAL="177E89"; PALE="EAF1F6"; GRAY="5B6570"

# ROC and cumulative gains figures
fig,ax=plt.subplots(figsize=(7.2,4.4),dpi=190)
for name,color in [("Decision Tree","#177E89"),("KNN (k=5)","#D47A32"),("XGBoost","#7356A8")]:
 r=M[name]["roc"]; ax.plot(r["fpr"],r["tpr"],lw=2.5,color=color,label=f"{name} (AUC {M[name]['auc']:.3f})")
ax.plot([0,1],[0,1],ls="--",lw=1.2,color="#8C98A3",label="No-skill reference")
ax.set(xlim=(0,1),ylim=(0,1.02),xlabel="False positive rate",ylabel="True positive rate",title="ROC curves on the held-out JM1 test set")
ax.grid(color="#D9E0E5",lw=.65); ax.legend(frameon=False,loc="lower right",fontsize=8.5); fig.tight_layout()
fig.savefig(FIG_DIR/"roc_curve.png",bbox_inches="tight"); plt.close(fig)
fig,ax=plt.subplots(figsize=(7.2,4.2),dpi=190)
for name,color in [("Decision Tree","#177E89"),("KNN (k=5)","#D47A32"),("XGBoost","#7356A8")]:
 g=M[name]["cumulative_gains"]; x=[0]+[v["population_fraction"] for v in g]; y=[0]+[v["defects_captured_fraction"] for v in g]
 ax.plot(x,y,marker="o",ms=3.2,lw=2.1,color=color,label=name)
ax.plot([0,1],[0,1],ls="--",lw=1.2,color="#8C98A3",label="Random selection")
ax.set(xlim=(0,1),ylim=(0,1.02),xlabel="Fraction of modules reviewed (highest risk first)",ylabel="Fraction of test defects captured",title="Cumulative gains by risk-ranked inspection")
ax.grid(color="#D9E0E5",lw=.65); ax.legend(frameon=False,loc="lower right",fontsize=8.5); fig.tight_layout()
fig.savefig(FIG_DIR/"cumulative_gains.png",bbox_inches="tight"); plt.close(fig)

doc=Document(); sec=doc.sections[0]
sec.page_width=Inches(8.5); sec.page_height=Inches(11)
sec.top_margin=Inches(.72); sec.bottom_margin=Inches(.72); sec.left_margin=Inches(.82); sec.right_margin=Inches(.82)
styles=doc.styles
normal=styles["Normal"]; normal.font.name="Times New Roman"; normal.font.size=Pt(10.5); normal.font.color.rgb=RGBColor.from_string("202830")
normal.paragraph_format.space_after=Pt(6); normal.paragraph_format.line_spacing=1.12
for sty,size,color in [("Title",23,BLUE),("Heading 1",15,BLUE),("Heading 2",12,TEAL)]:
 s=styles[sty]; s.font.name="Times New Roman"; s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color)
 s.paragraph_format.space_before=Pt(11 if sty!="Title" else 0); s.paragraph_format.space_after=Pt(5); s.paragraph_format.keep_with_next=True
title_style=styles["Title"]
title_style.font.color.rgb=RGBColor.from_string("000000"); title_style.font.underline=False
title_ppr=title_style._element.get_or_add_pPr()
for border in list(title_ppr.findall(qn("w:pBdr"))): title_ppr.remove(border)
p=sec.header.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=p.add_run("DATA ANALYTICS  |  SOFTWARE DEFECT PREDICTION"); r.font.name="Arial"; r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string("547084")
p=sec.footer.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run("JM1 classification study  •  "); r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string("547084")
fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); p._p.append(fld)

def para(text="",bold_lead=None,italic=False):
 p=doc.add_paragraph()
 if bold_lead and text.startswith(bold_lead): p.add_run(bold_lead).bold=True; p.add_run(text[len(bold_lead):])
 else:
  r=p.add_run(text); r.italic=italic
 return p
def shade(cell,fill):
 sh=OxmlElement("w:shd"); sh.set(qn("w:fill"),fill); cell._tc.get_or_add_tcPr().append(sh)
def table(headers,rows,widths=None,size=8.5):
 t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False; t.style="Table Grid"
 for j,h in enumerate(headers):
  c=t.rows[0].cells[j]; c.text=""; r=c.paragraphs[0].add_run(str(h)); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string("FFFFFF"); shade(c,BLUE); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
 for i,row in enumerate(rows):
  cells=t.add_row().cells
  for j,val in enumerate(row):
   c=cells[j]; c.text=""; pp=c.paragraphs[0]; pp.paragraph_format.space_after=Pt(1); rr=pp.add_run(str(val)); rr.font.name="Times New Roman"; rr.font.size=Pt(size); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   if i%2: shade(c,PALE)
 if widths:
  for row in t.rows:
   for c,w in zip(row.cells,widths): c.width=Inches(w)
 doc.add_paragraph().paragraph_format.space_after=Pt(1)
 return t
def bullet(text):
 p=doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after=Pt(3); p.add_run(text)
def caption(text):
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(6); r=p.add_run(text); r.italic=True; r.font.size=Pt(8.5); r.font.color.rgb=RGBColor.from_string(GRAY)
def link(p,text,url):
 rel=p.part.relate_to(url,"http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",is_external=True)
 h=OxmlElement("w:hyperlink"); h.set(qn("r:id"),rel); run=OxmlElement("w:r"); pr=OxmlElement("w:rPr")
 col=OxmlElement("w:color"); col.set(qn("w:val"),TEAL); pr.append(col); u=OxmlElement("w:u"); u.set(qn("w:val"),"single"); pr.append(u)
 run.append(pr); tx=OxmlElement("w:t"); tx.text=text; run.append(tx); h.append(run); p._p.append(h)
def ref(n,author,title,detail,url):
 p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.26); p.paragraph_format.first_line_indent=Inches(-.26); p.paragraph_format.space_after=Pt(4)
 p.add_run(f"[{n}] {author} {title} {detail} "); link(p,"Source",url)

p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(38); r=p.add_run("SOFTWARE DEFECT PREDICTION"); r.font.name="Arial"; r.font.size=Pt(10); r.bold=True; r.font.color.rgb=RGBColor.from_string(TEAL)
doc.add_paragraph("Comparing Decision Tree, KNN, and XGBoost on JM1",style="Title")
p=doc.add_paragraph(); r=p.add_run("A supervised learning study using software metrics"); r.font.size=Pt(13); r.font.color.rgb=RGBColor.from_string("547084")
p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(10); p.add_run("Data Analytics Assignment Report").bold=True
para("Student: ______________________________")
para("Course / section: ________________________")
para("Date: 16 November 2026")

doc.add_heading("Abstract",level=1)
para(f"This study evaluates whether static software metrics can identify defect-prone modules in JM1. The data contain {D['n_rows']:,} modules, 21 numeric predictors, and a binary defect label; {D['class_counts']['defective']:,} modules are defective ({D['defect_rate']*100:.1f}%). A stratified 80/20 split (seed 42) compares a class-balanced Decision Tree, scaled five-neighbor KNN, and class-weighted XGBoost. XGBoost achieved {M['XGBoost']['accuracy']*100:.1f}% accuracy, {M['XGBoost']['precision']*100:.1f}% precision, {M['XGBoost']['recall']*100:.1f}% recall, F1 {M['XGBoost']['f1']:.3f}, and ROC-AUC {M['XGBoost']['auc']:.3f}. It captured {M['XGBoost']['top_decile_defects_captured']} test defects in the highest-risk decile ({M['XGBoost']['top_decile_lift']:.2f}× lift). XGBoost had the strongest ranking metrics of the three tested configurations, though results are modest and come from one holdout split; they do not establish statistical superiority.")
p=doc.add_paragraph(); p.add_run("Keywords: ").bold=True; p.add_run("software defect prediction; JM1; XGBoost; Decision Tree; K-nearest neighbors; ROC-AUC; lift")

doc.add_heading("1. Introduction",level=1)
para("Software modules differ in size, complexity, and internal structure. Static code metrics summarize some of these properties and can be used to predict whether a module is labeled defective. This is a binary classification problem: the model learns from modules with known labels and predicts a label for held-out modules. The DefectData repository collects software metric datasets for software engineering research and documents JM1 as a McCabe dataset with 7,782 modules, 21 predictors, and a 21.49% defective rate [1].")
para("The practical question is not simply whether a model is often correct. Defects are the minority class, so a model that mostly predicts non-defective could obtain high accuracy while failing to find defects. This report compares Decision Tree, KNN, and XGBoost classifiers, emphasizing defect recall, precision, F1, ROC-AUC, and inspection lift alongside accuracy.")
doc.add_heading("1.1 Research question",level=2)
para("How effectively do a Decision Tree, KNN, and XGBoost classify defective JM1 modules from static software metrics, and which model offers the more useful balance for defect screening?")

doc.add_heading("2. Dataset and preparation",level=1)
para("The analysis used the JM1 ARFF file distributed in the DefectData repository under inst/extdata/terapromise/mccabe. The target field is label, with Y mapped to defective (1) and N to non-defective (0), consistent with the repository loader, which identifies JM1’s target as label [2]. The predictor set contains 21 numeric code metrics, including LOC_TOTAL, BRANCH_COUNT, CYCLOMATIC_COMPLEXITY, Halstead measures, and operand/operator counts.")
table(["Dataset check","Observed result"],[
 ["Modules / predictors","7,782 / 21"],["Defective / non-defective","1,672 (21.5%) / 6,110 (78.5%)"],["Missing predictor values","0"],["Exact duplicate rows","0"],["Train / test rows","6,225 / 1,557 (stratified 80/20)"],["Test defective / non-defective","335 / 1,222"]],[2.25,4.15],8.7)
para("The downloaded dataset matches the counts stated in the repository summary. The target label was kept separate from predictors. No records or predictors needed removal for missingness or duplication. No discretization was applied: both methods accept numeric predictors, and converting continuous values to bins would discard information. No broad feature reduction was required for 21 predictors. KNN features were standardized using training-set means and standard deviations inside a pipeline; the Decision Tree used unscaled values. This prevents test data from influencing KNN scaling.")
doc.add_heading("2.1 Descriptive statistics and relationships",level=2)
para("LOC_TOTAL is strongly right-skewed: its mean is 46.25, median 26, standard deviation 80.58, variance 6,492.36, skewness 15.47, and excess kurtosis 488.22. The gap between mean and median and the large skewness indicate a long upper tail with a small number of very large modules. Standard deviation and variance quantify spread; skewness and kurtosis describe distribution shape.")
fs=["LOC_TOTAL","BRANCH_COUNT","CYCLOMATIC_COMPLEXITY","HALSTEAD_VOLUME"]
table(["Metric","Mean","Median","SD","Skew","Excess kurtosis"],[[f.replace("_"," "),f"{S[f]['mean']:.2f}",f"{S[f]['median']:.2f}",f"{S[f]['sd']:.2f}",f"{S[f]['skewness']:.2f}",f"{S[f]['kurtosis_excess']:.2f}"] for f in fs],[2.1,.83,.83,.83,.83,1.0],8)
pidx={f:i for i,f in enumerate(A["correlation_features"])}; P=A["correlations"]["pearson"]; R=A["correlations"]["spearman"]
para(f"Selected correlations are positive and high. Pearson correlation between LOC_TOTAL and HALSTEAD_VOLUME is {P[pidx['LOC_TOTAL']][pidx['HALSTEAD_VOLUME']]:.3f}; between BRANCH_COUNT and CYCLOMATIC_COMPLEXITY it is {P[pidx['BRANCH_COUNT']][pidx['CYCLOMATIC_COMPLEXITY']]:.3f}. Spearman rank correlation for BRANCH_COUNT and CYCLOMATIC_COMPLEXITY is {R[pidx['BRANCH_COUNT']][pidx['CYCLOMATIC_COMPLEXITY']]:.3f}, showing their ordering is nearly monotonic. Pearson summarizes linear association, while Spearman summarizes rank association. Correlation does not establish that a metric causes defects. Correlated predictors can share or redistribute tree importance.")

doc.add_heading("3. Methods",level=1)
doc.add_heading("3.1 Train/test design",level=2)
para("Rows were divided once into 80% training and 20% test data using stratification to preserve the defective proportion. The split used random seed 42. Model settings were fixed before scoring the test set; no cross-validation or hyperparameter search was conducted. A single holdout estimates performance for this split and does not quantify uncertainty across possible splits.")
doc.add_heading("3.2 Decision Tree",level=2)
para("A CART-style Decision Tree repeatedly splits the predictor space to form groups with increasingly similar class labels. The model used Gini impurity, maximum depth 6, minimum 10 training examples per leaf, and class_weight=balanced. Balanced weighting increases the training weight of the minority defect class to reduce the tendency to ignore it [3]. The fitted tree reached depth 6 and produced 48 leaves. The model is interpretable as metric threshold rules.")
doc.add_heading("3.3 K-nearest neighbors",level=2)
para("KNN assigns a module the majority class among its five nearest training modules under Euclidean distance. Since metrics use different scales, median imputation (a safeguard; no missing values were observed) and standard scaling were fit on training data before distance calculation. KNN does not learn a compact rule set, and its predictions depend on distance, scale, and neighborhood size.")
doc.add_heading("3.4 XGBoost",level=2)
para("XGBoost is a gradient-boosted tree ensemble. It builds trees sequentially, with each stage improving on remaining prediction errors while regularization limits model complexity. This run used 300 boosting rounds, maximum depth 4, learning rate 0.05, row and feature subsampling of 0.8, L2 regularization of 1, and a positive-class weight of 3.66 based on the training-set class ratio. These settings were fixed before evaluating the test set; no hyperparameter search was conducted [6].")
doc.add_heading("3.5 Evaluation measures",level=2)
para("Accuracy is the fraction of correct predictions. Precision is the fraction of predicted defects that are actually defective; recall is the fraction of actual defects detected. F1 is the harmonic mean of precision and recall. The ROC curve plots true-positive rate against false-positive rate as the score threshold changes; ROC-AUC summarizes ranking across thresholds, with 0.5 representing random ranking. ROC analysis is useful because accuracy alone can obscure minority-class failures [4]. Lift compares defect rate in a selected high-risk group with the test-set defect rate. A lift of 1.0 is random selection; values above 1 indicate enrichment.")

doc.add_heading("4. Results",level=1)
para("The held-out test set contained 335 defective and 1,222 non-defective modules. The three models show different trade-offs: XGBoost ranked modules best overall, while the Decision Tree retained the highest threshold-based recall.")
rows=[]
for name in ["Decision Tree","KNN (k=5)","XGBoost"]:
 x=M[name]; rows.append([name,f"{x['accuracy']*100:.1f}%",f"{x['precision']*100:.1f}%",f"{x['recall']*100:.1f}%",f"{x['f1']:.3f}",f"{x['auc']:.3f}",f"{x['top_decile_lift']:.2f}×"])
table(["Model","Accuracy","Precision","Recall","F1","ROC-AUC","Top-decile lift"],rows,[1.65,.8,.8,.8,.65,.85,1.0],8.1)
para(f"The majority-class baseline predicts every module as non-defective: 78.5% accuracy and 0% defect recall. All three models score below that accuracy, so accuracy alone does not support deployment. XGBoost has the highest ROC-AUC ({M['XGBoost']['auc']:.3f}) and top-decile lift ({M['XGBoost']['top_decile_lift']:.2f}×); the Decision Tree has the highest default-threshold recall ({M['Decision Tree']['recall']*100:.1f}%). XGBoost gives the strongest ranking of these tested configurations, but its advantage is modest and based on one split.")
doc.add_heading("4.1 Confusion matrices",level=2)
para("Rows show the actual class and columns show predicted class. The positive class is defective.")
table(["Model","Defective → defect","Defective → clear","Clear → defect","Clear → clear"],[[name,*[v for row in M[name]["confusion_matrix"] for v in row]] for name in ["Decision Tree","KNN (k=5)","XGBoost"]],[1.55,1.2,1.2,1.2,1.2],8.2)
para("Rows show actual classes (defective, then non-defective) and columns show predicted classes in the same order. XGBoost detects more defects than KNN while raising fewer false alarms than the Decision Tree. False positives remain substantial for the tree-based classifiers.")
doc.add_heading("4.2 ROC and inspection lift",level=2)
doc.add_picture(str(FIG_DIR/"roc_curve.png"),width=Inches(6.35)); caption("Figure 1. ROC curves from prediction scores on the held-out test data.")
para(f"AUC is {M['Decision Tree']['auc']:.3f} for the Decision Tree, {M['KNN (k=5)']['auc']:.3f} for KNN, and {M['XGBoost']['auc']:.3f} for XGBoost. All exceed random ranking (0.5), but the separation is limited. XGBoost’s lead is descriptive; one split is not enough to claim statistical significance.")
doc.add_picture(str(FIG_DIR/"cumulative_gains.png"),width=Inches(6.35)); caption("Figure 2. Cumulative fraction of test defects captured when reviewing modules in descending predicted-risk order.")
para(f"In the top 10% of risk-ranked modules (156 modules), the Decision Tree captured {M['Decision Tree']['top_decile_defects_captured']} defects ({M['Decision Tree']['top_decile_recall']*100:.1f}%; {M['Decision Tree']['top_decile_lift']:.2f}× lift), KNN captured {M['KNN (k=5)']['top_decile_defects_captured']} ({M['KNN (k=5)']['top_decile_recall']*100:.1f}%; {M['KNN (k=5)']['top_decile_lift']:.2f}×), and XGBoost captured {M['XGBoost']['top_decile_defects_captured']} ({M['XGBoost']['top_decile_recall']*100:.1f}%; {M['XGBoost']['top_decile_lift']:.2f}×). Review thresholds should reflect inspection capacity and defect consequences.")
doc.add_heading("4.3 Tree feature importance",level=2)
features=A["decision_tree"]["top_features"][:5]
table(["Rank","Metric","Tree impurity importance"],[[i+1,n,f"{v:.3f}"] for i,(n,v) in enumerate(features)],[.65,3.7,2.1],8.5)
para("LOC_TOTAL had the largest impurity-based importance (0.394), followed by LOC_BLANK (0.122), LOC_EXECUTABLE (0.088), HALSTEAD_EFFORT (0.075), and HALSTEAD_CONTENT (0.054). These are model-specific split contributions, not causal effects or proof that changing a metric would change defect risk. Correlated metrics may divide importance.")
doc.add_heading("4.4 XGBoost feature importance",level=2)
xfeatures=A["xgboost"]["top_features"][:5]
table(["Rank","Metric","XGBoost gain importance"],[[i+1,n,f"{v:.3f}"] for i,(n,v) in enumerate(xfeatures)],[.65,3.7,2.1],8.5)
para("XGBoost gain importance summarizes how much each feature contributed to improving its tree splits. It is model-specific and should not be interpreted as a causal effect. Importance can also be shared across correlated metrics.")

doc.add_heading("5. Discussion",level=1)
para(f"The main finding is the tradeoff between missed defects and false alarms. The Decision Tree has the highest recall ({M['Decision Tree']['recall']*100:.1f}%), while XGBoost has the highest ROC-AUC ({M['XGBoost']['auc']:.3f}) and top-decile lift ({M['XGBoost']['top_decile_lift']:.2f}×). XGBoost is the strongest overall screening ranker in this split, while the Decision Tree flags more defects at the default threshold. Each still produces substantial errors. If prioritizing limited manual reviews, XGBoost’s risk ranking may be useful to examine, but validation on repeated splits and independent projects is needed.")
para("The analysis demonstrates data collection and integration through a repository dataset, cleaning checks, target preparation, numerical transformation, descriptive statistics, Pearson and Spearman correlations, feature ranking, supervised classification, confusion matrices, ROC-AUC, and decile lift. Market-basket methods, clustering, discretization, and inferential tests were outside this study’s scope.")
doc.add_heading("5.1 Statistical significance and limitations",level=2)
para("No hypothesis test or p-value was calculated. Scores on one fixed split are descriptive estimates, not proof that one algorithm is statistically better in the population. Repeated stratified cross-validation could estimate score variability; a prespecified paired test would be needed for a significance claim. Correlations are descriptive and are not interpreted as causal.")
for b in ["Only JM1 and one stratified split were analyzed; performance may vary across projects, versions, and splits.","Model settings were fixed rather than tuned, and no external validation was performed.","JM1 labels and metrics come from a benchmark dataset; their practical meaning may not transfer to a current software team.","The tree uses class weighting, while KNN uses ordinary majority voting. This compares stated configurations, not optimized models.","Static metrics can be redundant, as shown by high correlations, and feature importance is not causal evidence."]: bullet(b)
doc.add_heading("6. Conclusion",level=1)
para(f"On this JM1 holdout, XGBoost provides the strongest ranking performance among the three evaluated configurations, with ROC-AUC {M['XGBoost']['auc']:.3f} and top-decile lift {M['XGBoost']['top_decile_lift']:.2f}×. The Decision Tree has higher recall at the default threshold ({M['Decision Tree']['recall']*100:.1f}% versus XGBoost’s {M['XGBoost']['recall']*100:.1f}%), while KNN has the lowest recall. All models have limited performance and remain educational baselines. Repeated validation, threshold selection based on review costs, and independent project evaluation are needed before practical use.")

doc.add_heading("Syllabus topics demonstrated",level=1)
table(["Syllabus area","Use in this report"],[
 ["Collection, cleaning, transformation","Loaded JM1 ARFF; checked missing/duplicate data; separated target; scaled KNN inputs."],
 ["Descriptive statistics","Mean, median, standard deviation, variance, skewness, and excess kurtosis."],
 ["Correlation","Pearson and Spearman correlations on selected metrics; association, not causation."],
 ["Supervised learning","Decision Tree, KNN, and XGBoost classification."],
 ["Classification evaluation","Confusion matrices, accuracy, precision, recall, F1, ROC curve, and AUC."],
 ["Lift / decile analysis","Risk-ranked review gains and top-decile lift."],
 ["Hypothesis testing","Explained significance and p-values; no test or significance claim made."]
],[2.15,4.25],8.2)

doc.add_heading("References",level=1)
ref(1,"klainfo.","DefectData: An R package of software metric datasets.","README dataset profile.","https://github.com/klainfo/DefectData/blob/master/README.md")
ref(2,"klainfo.","DefectData, loadData.R.","JM1 target and source-loading definition.","https://github.com/klainfo/DefectData/blob/master/R/loadData.R")
ref(3,"scikit-learn developers.","DecisionTreeClassifier documentation.","Class balancing and parameters.","https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html")
ref(4,"Fawcett, T. (2006).","An introduction to ROC analysis.","Pattern Recognition Letters, 27(8), 861–874. doi:10.1016/j.patrec.2005.10.010.","https://doi.org/10.1016/j.patrec.2005.10.010")
ref(5,"Pedregosa, F. et al. (2011).","Scikit-learn: Machine learning in Python.","Journal of Machine Learning Research, 12, 2825–2830.","https://jmlr.org/papers/v12/pedregosa11a.html")
ref(6,"Chen, T. and Guestrin, C. (2016).","XGBoost: A scalable tree boosting system.","Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785–794.","https://doi.org/10.1145/2939672.2939785")
doc.add_heading("Appendix A. Analysis settings",level=1)
para(f"The analysis used scikit-learn {A['software_versions']['scikit_learn']} and XGBoost {A['software_versions']['xgboost']}. DecisionTreeClassifier used random_state=42, max_depth=6, min_samples_leaf=10, class_weight=balanced. The KNN pipeline used median imputation, StandardScaler, and KNeighborsClassifier(n_neighbors=5, weights=uniform, Euclidean distance). XGBClassifier used 300 estimators, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_lambda=1, scale_pos_weight=3.66 (exact train ratio 3.657), eval_metric=logloss, tree_method=hist, and random_state=42. Data splitting used train_test_split(test_size=0.20, stratify=y, random_state=42). Classification metrics use the default 0.5 probability threshold. The top decile contained ceil(0.10 × 1,557) = 156 modules.")
para("The companion analysis script records the parsing, split, preprocessing, model parameters, and metric calculations. Numerical results were generated from the repository dataset file rather than copied from the repository summary.")
path=OUT/"JM1_Software_Defect_Prediction_Report_XGBoost.docx"; doc.save(path); print(path)
