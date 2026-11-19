from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "PROP1"
OUT.mkdir(parents=True, exist_ok=True)
FIG_DIR = ROOT / "results" / "PROP1" / "figures"
FIG_ROC = FIG_DIR / "roc_curve.png"
FIG_GAINS = FIG_DIR / "cumulative_gains.png"
DATA = json.loads((ROOT / "results" / "PROP1" / "prop1_analysis.json").read_text())
D, M = DATA["dataset"], DATA["metrics"]
BLUE, TEAL, LIGHT, GRAY = "183A56", "177E89", "EAF1F5", "4F5D68"

def set_font(run, size=9.5, bold=None, italic=None, color=None, name="Times New Roman"):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rpr.rFonts.set(qn("w:ascii"), name)
    rpr.rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)
    return run

def strip_title_borders(style):
    ppr = style._element.get_or_add_pPr()
    for b in list(ppr.findall(qn("w:pBdr"))): ppr.remove(b)
    style.font.color.rgb = RGBColor.from_string("000000")
    style.font.underline = False

def make_base(two_col=False, header="PROP-1 SOFTWARE DEFECT PREDICTION"):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin, sec.bottom_margin = Inches(.66), Inches(.66)
    sec.left_margin, sec.right_margin = Inches(.70), Inches(.70)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Times New Roman", Pt(9.4 if two_col else 10.3)
    normal.font.color.rgb = RGBColor.from_string("202830")
    normal.paragraph_format.space_after = Pt(5 if not two_col else 3.5)
    normal.paragraph_format.line_spacing = 1.05 if two_col else 1.1
    for n, size in [("Heading 1", 14 if not two_col else 10.4), ("Heading 2", 11.5 if not two_col else 9.2)]:
        s = doc.styles[n]
        s.font.name, s.font.size, s.font.bold = "Times New Roman", Pt(size), True
        s.font.color.rgb = RGBColor.from_string(BLUE if n == "Heading 1" else TEAL)
        s.paragraph_format.space_before = Pt(10 if n == "Heading 1" else 6)
        s.paragraph_format.space_after = Pt(4 if n == "Heading 1" else 2.5)
        s.paragraph_format.keep_with_next = True
    strip_title_borders(doc.styles["Title"])
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.paragraph_format.space_after = Pt(0)
    set_font(hp.add_run(header), size=7.3, bold=True, color=GRAY, name="Arial")
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(fp.add_run("PROP-1 classification study  •  "), size=7.5, color=GRAY)
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE"); fp._p.append(fld)
    doc.core_properties.author = "Aditya Dubey"
    doc.core_properties.subject = "PROP-1 software defect prediction"
    return doc

def add_para(doc, text, size=None, after=None, before=0, bold=False, italic=False, align=None, keep=False):
    p = doc.add_paragraph()
    if align is not None: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if before: p.paragraph_format.space_before = Pt(before)
    if keep: p.paragraph_format.keep_together = True
    set_font(p.add_run(text), size=size or 9.4, bold=bold, italic=italic)
    return p

def add_heading(doc, text, level=1):
    return doc.add_heading(text, level=level)

def shade(cell, fill):
    sh = OxmlElement("w:shd"); sh.set(qn("w:fill"), fill); cell._tc.get_or_add_tcPr().append(sh)

def no_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

def add_table(doc, caption, headers, rows, widths, size=8.2):
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(2); cp.paragraph_format.space_after = Pt(3)
    cp.paragraph_format.keep_with_next = True
    set_font(cp.add_run(caption), size=8.1, bold=True, color=BLUE)
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]; c.width = Inches(widths[j]); c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        c.text = ""; p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        set_font(p.add_run(str(h)), size=size, bold=True, color="FFFFFF"); shade(c, BLUE)
    no_split(t.rows[0])
    for i, row in enumerate(rows):
        cells = t.add_row().cells; no_split(t.rows[-1])
        for j, val in enumerate(row):
            c = cells[j]; c.width = Inches(widths[j]); c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            c.text = ""; p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            set_font(p.add_run(str(val)), size=size)
            if i % 2: shade(c, LIGHT)
    spacer = doc.add_paragraph(); spacer.paragraph_format.space_after = Pt(1); spacer.paragraph_format.line_spacing = 1.0
    return t

def add_figure(doc, path, caption, width):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(path), width=Inches(width))
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(5); cp.paragraph_format.keep_together = True
    set_font(cp.add_run(caption), size=7.6, italic=True, color=GRAY)

def add_refs(doc, compact=False):
    refs = [
        "[1] klainfo, “DefectData: An R Package of Defect Prediction Datasets,” PROP-1 dataset profile. [Online]. Available: https://github.com/klainfo/DefectData/blob/master/README.md",
        "[2] klainfo, “DefectData Data Loading Function,” CK dataset loading and bug-count target definition. [Online]. Available: https://github.com/klainfo/DefectData/blob/master/R/loadData.R",
        "[3] scikit-learn developers, “DecisionTreeClassifier Documentation.” [Online]. Available: https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html",
        "[4] scikit-learn developers, “KNeighborsClassifier Documentation.” [Online]. Available: https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html",
        "[5] T. Chen and C. Guestrin, “XGBoost: A Scalable Tree Boosting System,” in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.",
        "[6] T. Fawcett, “An Introduction to ROC Analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006, doi: 10.1016/j.patrec.2005.10.010.",
    ]
    for ref in refs:
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(.16 if not compact else .1)
        p.paragraph_format.first_line_indent = Inches(-.16 if not compact else -.1)
        p.paragraph_format.space_after = Pt(3 if not compact else 1.5); p.paragraph_format.line_spacing = 1.0
        set_font(p.add_run(ref), size=7.3 if not compact else 6.8)

def add_metrics_table(doc, compact=False):
    if compact:
        add_table(doc, "TABLE II. PERFORMANCE ON THE GROUPED TEST FOLD",
            ["Model", "Acc. / Prec.", "Recall / F1", "AUC / Lift"], [
                ["Decision Tree", "62.7 / 26.5%", "78.1% / .396", ".778 / 2.93"],
                ["KNN (k=5)", "84.0 / 48.6%", "32.7% / .391", ".745 / 3.15"],
                ["XGBoost", "75.0 / 35.5%", "72.8% / .478", ".819 / 3.33"],
                ["Majority baseline", "84.3 / --", "0.0% / .000", "-- / 1.00"],
            ], [1.05, .82, .82, .75], 6.6)
        add_para(doc, "Accuracy, precision, and recall are percentages; F1, AUC, and lift are unitless.", size=7.2, after=3)
    else:
        add_table(doc, "Table 3. Holdout performance comparison", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Top-decile lift"], [
            ["Decision Tree", "62.7%", "26.5%", "78.1%", "0.396", "0.778", "2.93×"],
            ["KNN (k=5)", "84.0%", "48.6%", "32.7%", "0.391", "0.745", "3.15×"],
            ["XGBoost", "75.0%", "35.5%", "72.8%", "0.478", "0.819", "3.33×"],
            ["Majority baseline", "84.3%", "—", "0.0%", "0.000", "—", "1.00×"],
        ], [1.42, .82, .82, .78, .62, .82, 1.05], 7.7)

def add_confusion(doc, compact=False):
    if compact:
        add_table(doc, "TABLE III. CONFUSION COUNTS (TP/FN, FP/TN)", ["Model", "TP / FN", "FP / TN"], [
            ["Decision Tree", "442 / 124", "1,224 / 1,821"],
            ["KNN (k=5)", "185 / 381", "196 / 2,849"],
            ["XGBoost", "412 / 154", "747 / 2,298"],
        ], [1.25, 1.0, 1.1], 7.0)
    else:
        add_table(doc, "Table 4. Confusion matrices; entries show TP, FN, FP, TN", ["Model", "TP", "FN", "FP", "TN"], [
            ["Decision Tree", 442, 124, "1,224", "1,821"],
            ["KNN (k=5)", 185, 381, 196, "2,849"],
            ["XGBoost", 412, 154, 747, "2,298"],
        ], [1.75, .85, .85, .95, 1.0], 8)

def create_full_report():
    doc = make_base(False, "DATA ANALYTICS  |  PROP-1 DEFECT PREDICTION")
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(5)
    set_font(title.add_run("Software Defect Prediction in PROP-1"), size=23, bold=True)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(5)
    set_font(p.add_run("Comparing Decision Tree, K-Nearest Neighbors, and XGBoost"), size=13, color=GRAY)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(12)
    set_font(p.add_run("Aditya Dubey  |  Data Analytics Assignment"), size=10.5, bold=True, color=TEAL)

    add_heading(doc, "Abstract", 1)
    add_para(doc, "This study compares a class-balanced Decision Tree, five-neighbor KNN, and XGBoost for predicting defective modules in PROP-1. The source dataset contains 18,471 observations, 20 numeric metrics, and a 14.82% defect rate. Because identical metric vectors recur frequently, the evaluation uses a grouped, stratified holdout so identical feature vectors remain together. On 3,611 test observations, XGBoost achieved the highest ROC-AUC (0.819), F1 (0.478), and top-decile lift (3.33), while the Decision Tree achieved the highest recall (78.1%). KNN had the highest accuracy among fitted models (84.0%), but this remained below the 84.3% majority-class baseline. Results are descriptive for one grouped split; no statistical superiority claim is made.", size=10.2)
    add_para(doc, "Keywords: PROP-1, software defect prediction, XGBoost, Decision Tree, KNN, grouped validation, ROC-AUC, lift", size=9.4, italic=True, after=7)

    add_heading(doc, "1. Introduction", 1)
    add_para(doc, "Static software metrics summarize characteristics such as module size, coupling, and complexity. These measurements can support a model that ranks software modules by defect risk, helping teams decide where to spend limited review effort. PROP-1 is part of the PROMISE CK dataset collection in DefectData. The repository profile lists 18,471 modules, 2,738 defective modules, and 20 predictors [1].")
    add_para(doc, "The target is imbalanced: 85.2% of records are non-defective. Accuracy can therefore be misleading if a model favors the majority class. This report compares a Decision Tree, KNN, and XGBoost using precision, recall, F1, ROC-AUC, confusion matrices, and top-decile lift. The main question is which model gives the most useful risk ranking for defect review.")

    add_heading(doc, "2. Dataset and Preparation", 1)
    add_para(doc, "The PROP-1 CSV contains the fields Name, version, 20 software metrics, and bug. Per the DefectData loading function, the positive label is bug > 0 [2]. Name and version identify the dataset/version and were excluded as predictors. The remaining 20 numeric metrics were used. No feature values were missing.")
    add_table(doc, "Table 1. PROP-1 dataset summary", ["Quantity", "Value"], [
        ["Rows / predictors", "18,471 / 20"],
        ["Defective / non-defective", "2,738 / 15,733"],
        ["Defect prevalence", "14.82%"],
        ["Missing metric values", "0"],
        ["Exact repeated full rows", "3,337"],
        ["Unique metric vectors", "8,672"],
        ["Repeated metric-vector rows", "9,799"],
        ["Feature vectors with mixed labels", "661"],
        ["Training / test observations", "14,860 / 3,611"],
        ["Test defects / non-defects", "566 / 3,045"],
    ], [3.4, 2.4], 8.7)
    add_para(doc, "The CSV does not provide a unique module identifier, so repeated full rows were retained rather than assumed to be data-entry errors. Identical metric vectors were kept in the same partition, reducing leakage from repeated patterns. The first fold of a shuffled, stratified five-fold group split (random seed 42) was used. This fold contains 19.6% of the data and has 15.7% defective labels, close to the full-data prevalence of 14.8%.")

    add_heading(doc, "2.1 Descriptive Statistics and Correlation", 2)
    add_para(doc, "The loc metric is right-skewed: mean 206.63, median 73, standard deviation 420.07, variance 176,461.30, skewness 6.11, and excess kurtosis 56.57. The mean substantially exceeds the median because a small number of modules have very high LOC values.")
    add_table(doc, "Table 2. Selected metric statistics", ["Metric", "Mean", "Median", "Std. dev.", "Skew", "Excess kurtosis"], [
        ["loc", "206.63", "73", "420.07", "6.11", "56.57"],
        ["wmc", "6.54", "4", "8.50", "4.43", "33.92"],
        ["avg_cc", "1.53", "1", "1.61", "3.60", "24.70"],
    ], [1.2, .9, .9, 1.0, .7, 1.2], 7.6)
    add_para(doc, "Pearson correlation is 0.622 between loc and wmc and 0.796 between max_cc and avg_cc. Spearman correlation for max_cc and avg_cc is 0.934, indicating a strong monotonic relationship. Correlations describe association, not causation; related metrics can share feature importance.")

    add_heading(doc, "3. Methods", 1)
    add_heading(doc, "3.1 Grouped train/test design", 2)
    add_para(doc, "Rows were separated with StratifiedGroupKFold using five folds, shuffle enabled, and random_state 42. Groups were formed from identical 20-metric feature vectors, so the same vector could not occur in both training and test data. The first fold was held out for evaluation. This group-aware split addresses a leakage risk created by the repeated metric patterns. All learned preprocessing was fit on the training partition.")
    add_heading(doc, "3.2 Decision Tree", 2)
    add_para(doc, "The Decision Tree recursively partitions the metric space to form groups with more homogeneous labels. We used Gini impurity, max_depth=6, min_samples_leaf=10, and balanced class weights. The fitted tree reached depth 6 and had 48 leaves. Balanced weighting increases the minority class contribution during training [3].")
    add_heading(doc, "3.3 K-nearest neighbors", 2)
    add_para(doc, "KNN predicts the majority label among the five closest training examples using Euclidean distance. Since metrics have different scales, median imputation and standard scaling were applied in a training-fitted pipeline, followed by uniform-weight KNN with k=5 [4]. Imputation is included as a safeguard; no feature values were missing.")
    add_heading(doc, "3.4 XGBoost", 2)
    add_para(doc, "XGBoost builds an ensemble of decision trees sequentially, with each stage reducing the remaining prediction errors while regularization limits model complexity [5]. The model used 300 estimators, maximum depth 4, learning rate 0.05, row subsampling 0.8, feature subsampling 0.8, and L2 regularization of 1. The positive class weight was set to the training non-defective/defective ratio, 12,688/2,172 = 5.842. Settings were fixed before test evaluation; no hyperparameter search was performed.")
    add_heading(doc, "3.5 Evaluation", 2)
    add_para(doc, "Accuracy is the fraction of correct labels; precision is the share of predicted defects that are truly defective; recall is the share of actual defects detected; F1 is their harmonic mean. ROC-AUC measures ranking across thresholds, where 0.5 is random ranking [6]. For lift analysis, rows are ranked by model risk; top-decile lift divides the defective rate in the highest-risk 10% by the test-fold defect rate. The top decile contains ceil(0.10 × 3,611) = 362 observations.")

    add_heading(doc, "4. Results", 1)
    add_para(doc, "The 3,611-observation test fold contains 566 defective and 3,045 non-defective cases. Table 3 compares each model at the default 0.5 threshold. XGBoost has the highest F1, ROC-AUC, and top-decile lift. The Decision Tree has the highest recall. KNN has the highest accuracy among the learned models, but all learned models fall below the 84.3% all-non-defective baseline.")
    add_metrics_table(doc)
    add_heading(doc, "4.1 Confusion Matrices", 2)
    add_para(doc, "Table 4 shows true positives (TP), false negatives (FN), false positives (FP), and true negatives (TN). The Decision Tree identified 442 defects and missed 124, with 1,224 false alarms. XGBoost identified 412 defects and missed 154, with 747 false alarms. KNN produced only 196 false alarms, but missed 381 of 566 defects.")
    add_confusion(doc)
    add_heading(doc, "4.2 ROC and Risk-ranked Inspection", 2)
    add_para(doc, "The ROC curves show the highest AUC for XGBoost (0.819), followed by Decision Tree (0.778) and KNN (0.745). In the highest-risk 10% of the test set, XGBoost captured 189 of 566 defects (33.4%; 3.33× lift), KNN captured 179 (31.6%; 3.15×), and the Decision Tree captured 166 (29.3%; 2.93×). The gains are useful for comparing review prioritization, but performance remains imperfect.")
    add_figure(doc, FIG_ROC, "Figure 1. ROC curves on the grouped PROP-1 test fold.", 6.2)
    add_figure(doc, FIG_GAINS, "Figure 2. Cumulative defects captured as review expands from highest to lower predicted risk.", 6.2)
    add_heading(doc, "4.3 Feature Importance", 2)
    add_table(doc, "Table 5. Leading XGBoost gain importances", ["Rank", "Metric", "Importance"], [
        [1, "ce", "0.156"], [2, "cbo", "0.111"], [3, "cam", "0.083"], [4, "npm", "0.054"], [5, "loc", "0.046"],
    ], [.8, 3.0, 1.2], 8.3)
    add_para(doc, "XGBoost gain importance summarizes how much features contribute to improvements in tree splits. These model-specific values are not causal evidence. Correlated metrics may share importance.")

    add_heading(doc, "5. Discussion", 1)
    add_para(doc, "XGBoost offers the strongest overall ranking by ROC-AUC, F1, and top-decile lift. The Decision Tree has higher default-threshold recall and therefore finds more defects at the cost of additional false positives. KNN has the best precision and accuracy among learned models, but low recall means it misses many defects. The all-non-defective baseline accuracy is 84.3%; KNN is slightly below it, while the two class-weighted tree methods trade accuracy for minority-class detection.")
    add_para(doc, "The group-aware split is important for this dataset because 9,799 observations share feature vectors with other rows and 661 feature-vector groups appear with both labels. Preventing identical vectors from crossing partitions makes the test score less likely to benefit from repeated patterns. The trade-off is that this one grouped fold may have different prevalence from the full dataset and should not be treated as a complete estimate of generalization.")
    add_heading(doc, "5.1 Limitations and Statistical Significance", 2)
    add_para(doc, "Only PROP-1 and one grouped test fold were analyzed. We did not perform repeated grouped cross-validation, hyperparameter tuning, external validation, or hypothesis testing; no p-value or statistical superiority claim is made. Results may vary across group splits. The lack of a unique module ID means repeated rows cannot be classified confidently as accidental duplicates or distinct modules with identical metrics. Results may not transfer to other projects, and the feature importances are not causal explanations.")

    add_heading(doc, "6. Conclusion", 1)
    add_para(doc, "On this grouped PROP-1 holdout, XGBoost was the strongest risk ranker, with ROC-AUC 0.819, F1 0.478, and top-decile lift 3.33. The class-balanced Decision Tree found the largest share of defects at the default threshold (78.1% recall). KNN produced fewer false alarms but missed more defects, and none of the models exceeded the majority-class accuracy baseline. For defect review, XGBoost is the most promising of the tested configurations, but additional grouped validation is needed before broader conclusions.")
    add_heading(doc, "Syllabus Topics Demonstrated", 1)
    add_table(doc, "Table 6. Course coverage in this study", ["Syllabus area", "Application"], [
        ["Data preparation", "CSV loading, target separation, identifier removal, missingness and repeated-row checks."],
        ["Statistics", "Mean, median, standard deviation, variance, skewness, excess kurtosis."],
        ["Correlation", "Pearson and Spearman correlations for selected metrics."],
        ["Supervised learning", "Decision Tree, KNN, and XGBoost classification."],
        ["Evaluation", "Confusion matrices, accuracy, precision, recall, F1, ROC-AUC, and lift."],
        ["Significance", "Explains p-values and inference; no test or significance claim was made."],
    ], [1.75, 4.6], 8)
    add_heading(doc, "References", 1)
    add_refs(doc)
    add_heading(doc, "Appendix A. Analysis Settings", 1)
    add_para(doc, "Software versions: scikit-learn 1.7.2 and XGBoost 3.4.1. The grouped split used StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42), first fold held out. The Decision Tree used max_depth=6, min_samples_leaf=10, class_weight=balanced, random_state=42. KNN used median imputation, StandardScaler, and five uniform-weight Euclidean neighbors. XGBoost used n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_lambda=1, scale_pos_weight=5.842, eval_metric=logloss, tree_method=hist, and random_state=42. Classification metrics used the default 0.5 threshold.")
    doc.core_properties.title = "Software Defect Prediction in PROP-1"
    path = OUT / "Full_Analysis_Report.docx"
    doc.save(path)
    return path

def create_conference_paper():
    doc = make_base(True, "PROP-1 DEFECT PREDICTION  |  CONFERENCE PAPER")
    title = doc.add_paragraph(style="Title"); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(6)
    set_font(title.add_run("Software Defect Prediction in PROP-1: Comparing Decision Tree, K-Nearest Neighbors, and XGBoost"), size=19.5, bold=True)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(7)
    set_font(p.add_run("Aditya Dubey"), size=11.5, bold=True)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4); p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run("Abstract—"), size=8.5, bold=True)
    set_font(p.add_run("Software defect prediction can help rank modules for review, but class imbalance and repeated metric patterns can inflate evaluation if related rows occur in both training and test partitions. This study compares a class-balanced Decision Tree, five-neighbor KNN, and XGBoost on PROP-1 from DefectData. The data contain 18,471 observations and 20 numeric CKJM metrics; a row is defective when bug count is greater than zero. We used the first fold of a shuffled stratified five-fold group split, grouping identical feature vectors. On 3,611 held-out observations, XGBoost achieved the highest ROC-AUC (0.819), F1 (0.478), and top-decile lift (3.33), capturing 189 of 566 defects in the highest-risk 362 observations. The Decision Tree had the highest recall (78.1%), while KNN had the highest learned-model accuracy (84.0%), just below the 84.3% all-non-defective baseline. Results are descriptive for one grouped holdout and do not establish statistical superiority."), size=8.5)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8); p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run("Index Terms—"), size=8.3, bold=True)
    set_font(p.add_run("PROP-1, defect prediction, XGBoost, Decision Tree, KNN, grouped validation, ROC-AUC, lift"), size=8.3, italic=True)
    body = doc.add_section(WD_SECTION.CONTINUOUS)
    body.page_width, body.page_height = Inches(8.5), Inches(11)
    body.top_margin = body.bottom_margin = Inches(.66)
    body.left_margin = body.right_margin = Inches(.70)
    cols = body._sectPr.find(qn("w:cols"))
    if cols is None: cols = OxmlElement("w:cols"); body._sectPr.append(cols)
    cols.set(qn("w:num"), "2"); cols.set(qn("w:space"), "430"); cols.set(qn("w:sep"), "0")

    add_heading(doc, "I. INTRODUCTION", 1)
    add_para(doc, "Static software metrics such as module size, coupling, and complexity can be used to estimate defect risk. The DefectData repository lists PROP-1 as a PROMISE CK dataset with 18,471 observations, 2,738 defective labels, and 20 predictors [1]. Since the target is imbalanced, this study compares Decision Tree, KNN, and XGBoost using precision, recall, F1, ROC-AUC, confusion matrices, and inspection lift.", size=8.6)
    add_para(doc, "Research question: Which of the three classifiers best ranks PROP-1 observations for defect review while balancing detected defects and false alarms?", size=8.6, bold=True)

    add_heading(doc, "II. DATASET AND PREPARATION", 1)
    add_para(doc, "The PROP-1 CSV has 18,471 rows, 20 numeric metrics, and a bug-count label. The repository loader defines a defective observation as bug > 0 [2]. Name and version were excluded from the model inputs. No metric values were missing.", size=8.6)
    add_table(doc, "TABLE I. DATA SUMMARY", ["Quantity", "Value"], [
        ["Rows / metrics", "18,471 / 20"], ["Defective / non-defective", "2,738 / 15,733"],
        ["Defect prevalence", "14.82%"], ["Missing values", "0"],
        ["Repeated full rows", "3,337"], ["Unique feature vectors", "8,672"],
        ["Mixed-label vectors", "661"], ["Train / test rows", "14,860 / 3,611"],
    ], [2.0, 1.4], 7.0)
    add_para(doc, "Repeated rows were retained because no unique module identifier is present. Identical feature vectors were grouped into the same partition to reduce train/test leakage. We used the first fold of StratifiedGroupKFold with five folds, shuffle enabled, and seed 42. The held-out fold contains 566 defects (15.7% prevalence).", size=8.4)
    add_heading(doc, "A. Descriptive Statistics", 2)
    add_para(doc, "The loc metric has mean 206.63, median 73, standard deviation 420.07, variance 176,461.30, skewness 6.11, and excess kurtosis 56.57. Pearson correlation is 0.622 for loc/wmc and 0.796 for max_cc/avg_cc; the Spearman correlation for max_cc/avg_cc is 0.934. These associations are not causal.", size=8.4)

    add_heading(doc, "III. METHODS", 1)
    add_heading(doc, "A. Decision Tree", 2)
    add_para(doc, "The Gini-based tree used maximum depth 6, minimum leaf size 10, balanced class weights, and random_state 42. The fitted model had depth 6 and 48 leaves [3].", size=8.4)
    add_heading(doc, "B. K-Nearest Neighbors", 2)
    add_para(doc, "KNN used five uniform-weight Euclidean neighbors. Median imputation and standard scaling were fit within a training-only pipeline before distance calculation [4].", size=8.4)
    add_heading(doc, "C. XGBoost", 2)
    add_para(doc, "XGBoost combines sequentially fitted, regularized trees [5]. We used 300 estimators, depth 4, learning rate 0.05, row and feature subsampling 0.8, L2 regularization 1, and scale_pos_weight=12,688/2,172=5.842. Settings were fixed before test scoring.", size=8.4)
    add_heading(doc, "D. Evaluation", 2)
    add_para(doc, "Metrics use the default 0.5 probability threshold. ROC-AUC evaluates ranking across thresholds [6]. Top-decile lift is the defect rate among the 10% highest-risk test rows divided by the full test-fold defect rate. The top decile contains 362 rows. The majority baseline predicts all observations as non-defective.", size=8.4)

    add_heading(doc, "IV. RESULTS", 1)
    add_heading(doc, "A. Overall Performance", 2)
    add_para(doc, "The test fold has 566 defective and 3,045 non-defective observations. XGBoost achieved the highest F1, ROC-AUC, and top-decile lift. The Decision Tree produced the highest recall, and KNN produced the highest accuracy among fitted models.", size=8.4)
    add_metrics_table(doc, compact=True)
    add_heading(doc, "B. Confusion Counts", 2)
    add_para(doc, "Table III reports true-positive/false-negative and false-positive/true-negative pairs. The Decision Tree detects 442 defects but has 1,224 false positives. XGBoost detects 412 defects with 747 false positives. KNN has only 196 false positives but misses 381 defects.", size=8.4)
    add_confusion(doc, compact=True)
    add_heading(doc, "C. ROC and Risk-Ranked Inspection", 2)
    add_para(doc, "XGBoost's ROC-AUC is 0.819, compared with 0.778 for the Decision Tree and 0.745 for KNN. In the highest-risk 10% (362 rows), XGBoost captured 189 defects (33.4%; 3.33× lift), KNN 179 (31.6%; 3.15×), and the Decision Tree 166 (29.3%; 2.93×). These differences are descriptive for one fold.", size=8.4)
    add_figure(doc, FIG_ROC, "Fig. 1. ROC curves on the grouped PROP-1 test fold.", 3.35)
    add_figure(doc, FIG_GAINS, "Fig. 2. Cumulative test defects captured by risk-ranked review.", 3.35)
    add_heading(doc, "D. Feature Importance", 2)
    add_para(doc, "XGBoost's leading gain importances were ce (0.156), cbo (0.111), cam (0.083), npm (0.054), and loc (0.046). These model-specific split summaries are not causal effects.", size=8.4)

    add_heading(doc, "V. DISCUSSION", 1)
    add_para(doc, "XGBoost provides the strongest ranking by ROC-AUC, F1, and top-decile lift. The Decision Tree finds more defects at the default threshold, and KNN generates fewer false alarms. All fitted models fall below the 84.3% accuracy of the all-non-defective baseline, so accuracy alone is inadequate for this imbalanced target.", size=8.4)
    add_para(doc, "Grouped evaluation reduces leakage from identical metric vectors, but one grouped fold does not quantify performance variability. The 661 feature vectors that occur with both labels also show that these metrics do not determine defect status unambiguously.", size=8.4)
    add_heading(doc, "A. LIMITATIONS AND SIGNIFICANCE", 2)
    add_para(doc, "Only one grouped test fold was evaluated. No hyperparameter tuning, external validation, or hypothesis test was performed, and no p-value or statistical superiority claim is made. Results may vary across folds and projects. The dataset has no module IDs, so repeated rows cannot be conclusively classified as accidental duplicates.", size=8.4)

    add_heading(doc, "VI. CONCLUSION", 1)
    add_para(doc, "XGBoost was the strongest PROP-1 risk ranker on this holdout (AUC 0.819; top-decile lift 3.33; F1 0.478). The Decision Tree had the highest recall (78.1%), while KNN produced the highest fitted-model accuracy but did not exceed the majority baseline. Multiple grouped folds and independent projects should be evaluated before broader conclusions.", size=8.4)
    add_heading(doc, "REPRODUCIBILITY", 1)
    add_para(doc, "The analysis used scikit-learn 1.7.2 and XGBoost 3.4.1. Identical feature vectors defined groups; the first split from StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42) was held out. The positive target is bug > 0; Name and version are excluded.", size=8.1)
    add_heading(doc, "REFERENCES", 1)
    add_refs(doc, compact=True)

    doc.core_properties.title = "Software Defect Prediction in PROP-1 Conference Paper"
    path = OUT / "Conference_Paper.docx"
    doc.save(path)
    return path

if __name__ == "__main__":
    print(create_full_report())
    print(create_conference_paper())
