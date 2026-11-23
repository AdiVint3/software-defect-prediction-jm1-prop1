from pathlib import Path
import csv
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'MultiDataset_20x10'
RES = ROOT / 'results' / 'MultiDataset_20x10'
FIG = RES / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
DOC_FIG = ROOT / 'tmp' / 'docx_figures'
DOC_FIG.mkdir(parents=True, exist_ok=True)

def read_csv(name):
    with (RES / name).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

scores = sorted(read_csv('overall_macro_summary.csv'), key=lambda r: float(r['roc_auc_macro_mean']), reverse=True)
datasets = read_csv('dataset_inventory.csv')
conf = read_csv('overall_pooled_confusion_summary.csv')
baseline = read_csv('majority_baseline_macro_summary.csv')[0]
def pct(x): return f'{float(x)*100:.1f}%'
def num(x): return f'{float(x):.3f}'

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), color); tcPr.append(shd)

def set_cell(cell, text, bold=False, color=None, size=8):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(str(text)); r.bold = bold; r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def style_table(table, header=True, size=8):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Light Shading Accent 1'
    for ri, row in enumerate(table.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs: run.font.size = Pt(size)
            if header and ri == 0:
                shade(cell, '174A67')
                for p in cell.paragraphs:
                    for run in p.runs: run.font.color.rgb = RGBColor(255,255,255); run.bold = True

def setup(doc, title, compact=False):
    sec = doc.sections[0]
    sec.top_margin = Inches(.62 if compact else .72); sec.bottom_margin = Inches(.62 if compact else .72)
    sec.left_margin = Inches(.66 if compact else .78); sec.right_margin = Inches(.66 if compact else .78)
    styles = doc.styles
    styles['Normal'].font.name = 'Aptos'; styles['Normal'].font.size = Pt(9 if compact else 10)
    styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos')
    styles['Normal'].paragraph_format.space_after = Pt(5)
    for s, size, col in [('Title', 22 if not compact else 18, '173B57'), ('Heading 1', 15 if not compact else 12, '174A67'), ('Heading 2', 11 if not compact else 10, '28768A')]:
        styles[s].font.name = 'Aptos Display'; styles[s].font.size = Pt(size); styles[s].font.color.rgb = RGBColor.from_string(col); styles[s].font.bold = True
        styles[s]._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos Display')
    p = sec.footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = p.add_run('Software Defect Prediction | 20 datasets | Aditya Dubey'); rr.font.size = Pt(8); rr.font.color.rgb = RGBColor(100,110,120)
    doc.add_heading(title, 0)

def para(doc, text, boldlead=None):
    p=doc.add_paragraph()
    if boldlead and text.startswith(boldlead): p.add_run(boldlead).bold=True; p.add_run(text[len(boldlead):])
    else: p.add_run(text)
    return p

def add_results_table(doc, compact=False):
    t=doc.add_table(rows=1, cols=7)
    for c, h in zip(t.rows[0].cells, ['Algorithm','Accuracy','Precision','Recall','F1','MCC','ROC-AUC']): set_cell(c,h,True,'FFFFFF',7 if compact else 8)
    for i,r in enumerate(scores):
        cells=t.add_row().cells
        vals=[r['model'],num(r['accuracy_macro_mean']),num(r['precision_macro_mean']),num(r['recall_macro_mean']),num(r['f1_macro_mean']),num(r['mcc_macro_mean']),num(r['roc_auc_macro_mean'])]
        for j,(c,v) in enumerate(zip(cells,vals)): set_cell(c,v,size=7 if compact else 8)
        if i==0:
            for c in cells: shade(c,'E7F2F4')
    style_table(t,True,7 if compact else 8)
    return t

def add_figure(doc, name, caption, width=6.25):
    if not (FIG/name).exists(): return
    optimized=DOC_FIG/(Path(name).stem+'.jpg')
    with Image.open(FIG/name) as image:
        image=image.convert('RGB'); image.thumbnail((1500,1100),Image.Resampling.LANCZOS)
        image.save(optimized,format='JPEG',quality=75,optimize=True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(optimized),width=Inches(width))
    cp=doc.add_paragraph(caption); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in cp.runs: r.italic=True; r.font.size=Pt(8)

# Full analytical report
d=Document(); setup(d,'Cross-Dataset Software Defect Prediction')
p=d.add_paragraph('Empirical comparison of ten classification algorithms across twenty public datasets'); p.runs[0].italic=True; p.runs[0].font.size=Pt(12)
para(d,'Prepared by Aditya Dubey | 23 November 2026')
d.add_heading('Executive summary',1)
para(d,'This study evaluates ten supervised classification approaches on 20 larger software defect datasets. Across the equal-weight macro averages, XGBoost achieved the highest ROC-AUC (0.798), F1 (0.485), and Matthews correlation coefficient (0.371). Random Forest produced the highest accuracy (0.837) and precision (0.511), while AdaBoost produced the highest recall (0.691). Because the majority-class baseline reached 0.812 accuracy while detecting no defective modules, accuracy alone gives an incomplete picture of performance.')
para(d,'The findings are descriptive: they summarize three grouped stratified folds per dataset using fixed model configurations. No hyperparameter search or significance test was performed. Performance varies substantially across datasets, and these results should be treated as comparative academic baselines rather than deployment evidence.')
d.add_heading('1. Introduction',1)
para(d,'Software defect prediction uses historical software metrics to estimate which modules are likely to contain defects. Such estimates can help prioritize review and testing when inspection resources are limited. The task is difficult because defect labels are often imbalanced, datasets differ in project context, and static metrics can be highly correlated. Prior research therefore evaluates multiple performance measures and validates models across projects rather than relying on accuracy alone [1,2].')
para(d,'This work asks: how do ten common classifiers compare across a collection of larger software defect datasets when measured with accuracy, precision, recall, F1, MCC, and ROC-AUC? The analysis extends earlier JM1 and PROP-1 experiments to 20 datasets, including those two, and adds seven methods to the original Decision Tree, KNN, and XGBoost comparison.')
d.add_heading('2. Data and preparation',1)
para(d,'Data were taken from the DefectData repository, which packages public software metric corpora for analysis [3]. From the available collection, datasets were screened to retain at least 50 defective and 50 non-defective observations; the 20 eligible datasets with the largest row counts were selected. The final collection contains 115,688 module records, 16,659 labeled defective (14.4% overall). Dataset sizes range from 872 to 23,014 records. Each source corpus uses its documented defect field; the target is converted to a binary label and identifier/target fields are excluded from predictors.')
para(d,'Numeric predictors were retained, and columns that were entirely missing were dropped. All 20 selected datasets had zero missing predictor cells. Model pipelines nevertheless included median imputation as a safeguard. Scaling was applied for distance-based, linear, and neural methods. Class imbalance was addressed through class weighting or balanced sampling, according to the model pipeline. Duplicate feature vectors were counted; identical feature vectors were kept in the same fold where the grouped split had adequate class support, reducing train/test leakage from repeated records.')
d.add_heading('Dataset inventory',2)
inv=d.add_table(rows=1,cols=5)
for c,h in zip(inv.rows[0].cells,['Dataset','Corpus','Rows','Features','Defect rate']): set_cell(c,h,True,'FFFFFF',8)
for r in datasets:
    cells=inv.add_row().cells
    for c,v in zip(cells,[r['dataset'],r['corpus'],f"{int(r['n_rows']):,}",r['n_features'],pct(r['defect_rate'])]): set_cell(c,v,size=7)
style_table(inv,True,7)
d.add_heading('3. Algorithms and evaluation',1)
para(d,'The compared classifiers were Decision Tree, five-nearest-neighbor (KNN), XGBoost, Random Forest, Linear SVM, Logistic Regression, PCA followed by Logistic Regression, AdaBoost, a feed-forward Neural Network using an MLP classifier, and Gaussian Naive Bayes. PCA is a dimensionality-reduction stage within a supervised pipeline, not a standalone classifier. A convolutional neural network was not used because the inputs are flat metric vectors without image-like spatial structure. Gaussian Mixture was omitted because it is an unsupervised clustering model and does not directly implement the requested supervised defect classification.')
para(d,'Each dataset was split into three stratified grouped folds with random seed 42. Identical feature vectors were assigned together where group constraints permitted; the inventory records the strategy for every dataset. The same folds were used across models. Classification metrics were computed at a fixed probability threshold of 0.5 (the Linear SVM uses its zero decision boundary). ROC-AUC was computed from continuous model scores. For each dataset, fold metrics were averaged; the macro summary then averages the 20 dataset means equally, so larger datasets do not dominate the headline comparison.')
para(d,'MCC summarizes binary classification quality using all four confusion-matrix cells and ranges from -1 to 1. ROC-AUC measures ranking quality across thresholds [4]. The majority-class baseline predicts every module as non-defective and is included to demonstrate the impact of label imbalance.')
d.add_heading('4. Results',1)
para(d,'Table 2 reports equal-weight macro averages across datasets. XGBoost had the strongest aggregate ranking performance by ROC-AUC and the best macro F1 and MCC. Random Forest’s high accuracy and precision came with lower recall, while AdaBoost favored recall. These trade-offs indicate that the preferred model depends on whether the review process values finding more defects or reducing false alarms.')
add_results_table(d)
para(d,f"The majority-class baseline reached {num(baseline['accuracy_macro_mean'])} macro accuracy, with zero precision, recall, F1, and MCC for the defect class. XGBoost’s accuracy was {num(scores[0]['accuracy_macro_mean'])}; it is therefore below this simple baseline on accuracy, despite stronger defect detection and ranking scores. This is expected under imbalance and supports reporting multiple metrics.")
add_figure(d,'model_performance_boxplots.png','Figure 1. Distribution of dataset-level model scores across the 20 datasets.',6.15)
add_figure(d,'roc_auc_heatmap.png','Figure 2. ROC-AUC by dataset and classifier; color values represent three-fold dataset means.',6.15)
add_figure(d,'f1_heatmap.png','Figure 3. Defect-class F1 by dataset and classifier; color values represent three-fold dataset means.',6.15)
d.add_heading('5. Feature importance',1)
para(d,'Random Forest impurity-based feature importance was aggregated after normalizing within each fitted model. The plot summarizes the leading features appearing across the datasets. Feature-importance scores are model-specific associations, not causal effects; different corpora use different metric schemas, and correlated predictors may divide or inflate importance.')
add_figure(d,'random_forest_feature_importance.png','Figure 4. Leading Random Forest features aggregated across datasets where those metrics were available.',6.0)
d.add_heading('6. Discussion',1)
para(d,'XGBoost’s leading ROC-AUC suggests the strongest average ability among these settings to rank defective modules above non-defective ones. Its lead over Random Forest is modest (0.798 versus 0.791), so it should not be interpreted as a statistically established advantage. Random Forest’s 0.837 accuracy is also close to the 0.812 majority baseline, and its recall is lower than several alternatives. AdaBoost offers a recall-oriented operating point, but its precision is lower. Threshold selection should therefore reflect the cost of missed defects relative to unnecessary inspections.')
para(d,'Dataset-level variation in the boxplots and heatmaps shows that no single algorithm is uniformly best. A macro average treats each dataset equally and answers a cross-dataset comparison question; it differs from a pooled row-level score, which weights large datasets more heavily. The report presents macro averages as the primary summary for that reason.')
d.add_heading('7. Limitations and reproducibility',1)
para(d,'The analysis is limited to 20 selected datasets from one repository and three folds per dataset. Configurations were not tuned, no external project validation was performed, and no paired statistical test was run. Fixed threshold metrics may not match a team’s review capacity. Group splitting limits identical-vector leakage but does not remove all project or temporal dependence. The MLP reached its 55-iteration training cap in some folds, so those scores reflect a bounded baseline rather than a fully converged network. The analysis uses the repository’s labels and metric definitions; differences in collection and labeling may affect cross-dataset comparability.')
para(d,'The complete inventory, fold-level scores, per-dataset summaries, baseline scores, figures, and Python benchmark script are included with the project. The run used scikit-learn 1.7.2 and XGBoost 3.4.1. The output README provides execution instructions and the dataset inventory identifies the exact selected files.')
d.add_heading('8. Conclusion',1)
para(d,'Across the selected 20 datasets, XGBoost had the highest macro ROC-AUC, F1, and MCC; Random Forest led on accuracy and precision; AdaBoost led on recall. These complementary results demonstrate why defect prediction should be assessed using multiple metrics and why accuracy is insufficient for imbalanced labels. Further work should tune decision thresholds to review costs, validate on independent projects, improve MLP convergence, and apply repeated paired statistical comparisons before making claims of model superiority.')
d.add_heading('References',1)
for ref in ['[1] T. Menzies, J. Greenwald, and A. Frank, “Data mining static code attributes to learn defect predictors,” IEEE Transactions on Software Engineering, vol. 33, no. 1, pp. 2–13, 2007.','[2] Y. Kamei et al., “A large-scale empirical study of just-in-time quality assurance,” IEEE Transactions on Software Engineering, vol. 39, no. 6, pp. 757–773, 2013.','[3] klainfo, “DefectData: Software defect datasets for empirical research,” GitHub repository. https://github.com/klainfo/DefectData (accessed Nov. 23, 2026).','[4] T. Fawcett, “An introduction to ROC analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006.','[5] T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016, pp. 785–794.']:
    p=d.add_paragraph(ref); p.paragraph_format.space_after=Pt(3); p.paragraph_format.left_indent=Inches(.18); p.paragraph_format.first_line_indent=Inches(-.18)
d.save(OUT/'Full_Analysis_Report.docx')

# Conference paper, concise academic manuscript
c=Document(); setup(c,'Cross-Dataset Software Defect Prediction',True)
p=c.add_paragraph('A Ten-Algorithm Empirical Comparison on Twenty Larger Public Datasets'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].italic=True
p=c.add_paragraph('Aditya Dubey'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
c.add_heading('Abstract',1)
para(c,'Software defect datasets are imbalanced, and accuracy can conceal weak detection of defective modules. We compare ten supervised classifiers across 20 larger datasets from the DefectData repository using three grouped stratified folds per dataset. The methods are Decision Tree, K-nearest neighbors, XGBoost, Random Forest, Linear SVM, Logistic Regression, PCA plus Logistic Regression, AdaBoost, a multilayer perceptron, and Gaussian Naive Bayes. We report accuracy, precision, recall, F1, Matthews correlation coefficient (MCC), and ROC-AUC. Equal-weight macro averages show that XGBoost achieved the highest ROC-AUC (0.798), F1 (0.485), and MCC (0.371); Random Forest had the highest accuracy (0.837) and precision (0.511); AdaBoost had the highest recall (0.691). A majority-class baseline achieved 0.812 accuracy but zero defect recall. Results are descriptive, with no hyperparameter search or significance test; they do not establish statistical superiority.')
p=c.add_paragraph('Index Terms—software defect prediction, classification, cross-dataset evaluation, XGBoost, MCC, ROC-AUC'); p.paragraph_format.space_after=Pt(4)
c.add_heading('I. Introduction',1)
para(c,'Software defect prediction estimates whether a software module is defective from code metrics. It can support review prioritization, but defect labels are commonly imbalanced and the cost of false negatives may exceed the cost of false positives. Consequently, accuracy alone is inadequate; evaluation should include minority-class measures and ranking metrics [1], [2].')
para(c,'We extend earlier JM1 and PROP-1 experiments to a 20-dataset comparison and add seven algorithms to the original Decision Tree, KNN, and XGBoost set. Our research question is how the ten methods compare on defect identification and ranking when evaluated consistently across a larger set of public data.')
c.add_heading('II. Data and Preparation',1)
para(c,'Datasets were obtained from the DefectData repository [3]. Eligible datasets required at least 50 defective and 50 non-defective records; the 20 largest eligible datasets by row count were selected. They include prop-1, prop-2, prop-3, prop-4, prop-5, JM1, PC3, PC4, PC5, eclipse-2.0, eclipse-2.1, eclipse-3.0, eclipse34_debug, eclipse34_swt, mylyn, pde, jdt, camel-1.4, camel-1.6, and xalan-2.6. Together they contain 115,688 records and 16,659 defects. The median dataset size is 1,486 records. Source-specific target definitions were retained; identifiers and target fields were excluded from predictors.')
para(c,'Predictors were numeric software metrics. Entirely missing features were removed; no selected dataset had missing feature cells. Median-imputation pipelines were retained as safeguards. Scaling was used for distance, linear, and neural classifiers. Imbalance handling was model-specific. Three stratified grouped folds (seed 42) were applied per dataset, keeping identical feature vectors within one fold when class group support allowed.')
c.add_heading('III. Methods',1)
para(c,'The ten classifiers were Decision Tree, KNN (k=5), XGBoost, Random Forest, Linear SVM, Logistic Regression, PCA plus Logistic Regression, AdaBoost, MLP Neural Network, and Gaussian Naive Bayes. PCA was applied as a train-fold-fitted preprocessing step in a supervised pipeline. A CNN was excluded because the inputs are tabular feature vectors without spatial structure; Gaussian Mixture was excluded because it is unsupervised and does not directly perform the requested binary classification.')
para(c,'We report accuracy, defect-class precision, recall, F1, MCC, and ROC-AUC. Hard-label measures use a fixed threshold of 0.5, except Linear SVM, which uses its zero decision boundary. ROC-AUC uses continuous scores [4]. Fold metrics were averaged per dataset, followed by an unweighted average across datasets. This macro procedure gives each dataset equal influence. A classifier that always predicts the non-defective class provides an accuracy baseline.')
c.add_heading('IV. Results',1)
para(c,'Table I gives the equal-weight macro averages. XGBoost led in ROC-AUC (0.798), F1 (0.485), and MCC (0.371). Random Forest reached the highest accuracy (0.837) and precision (0.511). AdaBoost had the highest recall (0.691), reflecting a more defect-sensitive but less precise operating point. The majority baseline achieved 0.812 accuracy with zero defect recall, illustrating the misleading nature of accuracy under class imbalance.')
add_results_table(c,True)
add_figure(c,'model_performance_boxplots.png','Fig. 1. Distribution of dataset-level performance scores across the 20 datasets.',5.9)
add_figure(c,'roc_auc_heatmap.png','Fig. 2. Three-fold ROC-AUC means by dataset and model.',5.9)
c.add_heading('V. Discussion',1)
para(c,'XGBoost has a modest ROC-AUC advantage over Random Forest (0.798 versus 0.791), but the study did not test whether this difference is statistically significant. Its lower accuracy than the majority baseline underscores the cost of emphasizing defect detection under imbalance. Random Forest may be useful when fewer false alarms are desired; AdaBoost may be preferable when missed defects are more costly. In practice, threshold selection should reflect inspection capacity and error costs.')
para(c,'The dataset-level plots show variation in model performance. There is no universally best model across all project corpora. Random Forest feature importance provides a descriptive summary of frequently useful software metrics, but correlated predictors and differing feature schemas limit direct interpretation as causal evidence.')
add_figure(c,'random_forest_feature_importance.png','Fig. 3. Leading aggregated Random Forest feature-importance scores.',5.6)
c.add_heading('VI. Limitations and Conclusion',1)
para(c,'This empirical comparison covers 20 datasets from one repository, fixed configurations, and three folds per dataset. No hyperparameter search, external validation, or significance testing was performed. The MLP reached its 55-iteration cap on some folds. Grouping identical feature vectors limits a source of leakage but cannot remove other project, version, or temporal dependencies. Results should be interpreted as educational baselines.')
para(c,'In summary, XGBoost ranked highest on macro ROC-AUC, F1, and MCC, Random Forest led on accuracy and precision, and AdaBoost led on recall. Multiple metrics are necessary to assess imbalanced defect prediction. Future work should tune thresholds and model settings, test on independent projects, and use paired repeated validation with statistical comparisons.')
c.add_heading('References',1)
for ref in ['[1] T. Menzies, J. Greenwald, and A. Frank, “Data mining static code attributes to learn defect predictors,” IEEE Trans. Software Eng., vol. 33, no. 1, pp. 2–13, 2007.','[2] Y. Kamei et al., “A large-scale empirical study of just-in-time quality assurance,” IEEE Trans. Software Eng., vol. 39, no. 6, pp. 757–773, 2013.','[3] klainfo, “DefectData,” GitHub. https://github.com/klainfo/DefectData.','[4] T. Fawcett, “An introduction to ROC analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006.','[5] T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” Proc. ACM SIGKDD, 2016, pp. 785–794.']:
    p=c.add_paragraph(ref); p.paragraph_format.space_after=Pt(2); p.paragraph_format.left_indent=Inches(.18); p.paragraph_format.first_line_indent=Inches(-.18)
c.save(OUT/'Conference_Paper.docx')
print('Created report and conference paper in',OUT)
