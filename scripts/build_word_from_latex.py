from pathlib import Path
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "reports" / "JM1" / "LaTeX"
OUT = ROOT / "reports" / "JM1" / "Conference_Paper.docx"
BLUE = "183A56"
TEAL = "177E89"
LIGHT = "EAF1F5"
GRAY = "4F5D68"

doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.5)
sec.page_height = Inches(11)
sec.top_margin = Inches(.62)
sec.bottom_margin = Inches(.62)
sec.left_margin = Inches(.68)
sec.right_margin = Inches(.68)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(8.8)
normal.font.color.rgb = RGBColor.from_string("202830")
normal.paragraph_format.space_after = Pt(3.5)
normal.paragraph_format.line_spacing = 1.04
for style_name, size in [("Heading 1", 10.5), ("Heading 2", 9.2)]:
    st = styles[style_name]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor.from_string(BLUE if style_name == "Heading 1" else TEAL)
    st.paragraph_format.space_before = Pt(7 if style_name == "Heading 1" else 5)
    st.paragraph_format.space_after = Pt(2.5)
    st.paragraph_format.keep_with_next = True

def set_font(run, size=None, bold=None, italic=None, color=None, name="Times New Roman"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)
    return run

def para(text, align=None, after=3.5, before=0, size=8.8, bold=False, italic=False):
    p = doc.add_paragraph()
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.line_spacing = 1.04
    set_font(p.add_run(text), size=size, bold=bold, italic=italic)
    return p

def heading(text, level=1):
    return doc.add_heading(text, level=level)

def shade(cell, fill):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(sh)

def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))

def add_table(caption, headers, rows, widths, font_size=7.4):
    cp = doc.add_paragraph()
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(2)
    cp.paragraph_format.keep_with_next = True
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(cp.add_run(caption), size=7.5, bold=True, color=BLUE)
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.style = "Table Grid"
    for j, label in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.width = Inches(widths[j])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(str(label)), size=font_size, bold=True, color="FFFFFF")
        shade(cell, BLUE)
    no_split(t.rows[0])
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        no_split(t.rows[-1])
        for j, value in enumerate(row):
            c = cells[j]
            c.width = Inches(widths[j])
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            set_font(p.add_run(str(value)), size=font_size)
            if i % 2: shade(c, LIGHT)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(1)
    spacer.paragraph_format.line_spacing = 1.0
    return t

def add_figure(path, caption, width=3.35):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(4)
    cap.paragraph_format.keep_together = True
    set_font(cap.add_run(caption), size=7.3, italic=True, color=GRAY)

# Full-width conference title and abstract block.
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(7)
p.paragraph_format.keep_with_next = True
set_font(p.add_run("Software Defect Prediction in JM1: A Comparison of Decision Tree, K-Nearest Neighbors, and XGBoost"), size=20, bold=True, color="000000")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(10)
set_font(p.add_run("Aditya Dubey"), size=11.5, bold=True)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
p.paragraph_format.line_spacing = 1.0
set_font(p.add_run("Abstract—"), size=8.7, bold=True)
set_font(p.add_run("Software defect prediction can help prioritize modules for code review, but imbalanced defect labels make accuracy alone unreliable. This paper compares a class-balanced Decision Tree, five-nearest-neighbor (KNN), and XGBoost classifiers on the JM1 software metrics dataset. The dataset contains 7,782 modules with 21 numeric predictors; 21.5% are labeled defective. We used a stratified 80/20 train/test split (random seed 42) and evaluated the held-out 1,557 modules. XGBoost achieved the highest ROC-AUC (0.659) and top-decile lift (2.03), capturing 68 of 335 test defects among the 156 highest-risk modules. The Decision Tree achieved the highest default-threshold recall (56.7%), while KNN achieved the highest accuracy (75.5%) but detected only 18.8% of defects. All models had limited discrimination and fell below the 78.5% accuracy of the all-non-defective baseline. These single-split results are descriptive and do not establish statistical superiority."), size=8.7)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(9)
p.paragraph_format.line_spacing = 1.0
set_font(p.add_run("Index Terms—"), size=8.5, bold=True)
set_font(p.add_run("software defect prediction, JM1, XGBoost, decision tree, K-nearest neighbors, ROC-AUC, lift analysis"), size=8.5, italic=True)

# Switch to two-column conference body after the full-width abstract.
body_sec = doc.add_section(WD_SECTION.CONTINUOUS)
body_sec.page_width = Inches(8.5)
body_sec.page_height = Inches(11)
body_sec.top_margin = Inches(.62)
body_sec.bottom_margin = Inches(.62)
body_sec.left_margin = Inches(.68)
body_sec.right_margin = Inches(.68)
cols = body_sec._sectPr.find(qn("w:cols"))
if cols is None:
    cols = OxmlElement("w:cols")
    body_sec._sectPr.append(cols)
cols.set(qn("w:num"), "2")
cols.set(qn("w:space"), "480")
cols.set(qn("w:sep"), "0")

heading("I. INTRODUCTION", 1)
para("Software modules vary in size and complexity. Static software metrics summarize some of these properties and can be used to estimate whether a module is defective. Defect prediction is a binary classification problem: a model learns from labeled modules and predicts labels or risk scores for new modules.")
para("The DefectData repository collects software metric datasets for empirical software engineering research. Its JM1 dataset contains 7,782 modules, 21 predictors, and a defective-module rate of approximately 21.5% [1]. In this imbalanced setting, a classifier that predicts mostly non-defective modules may achieve apparently high accuracy while missing defects. This study compares a Decision Tree, KNN, and XGBoost using defect-class precision and recall, F1, ROC-AUC, confusion matrices, and risk-ranked inspection lift.")
para("Research question: How effectively do these three classifiers identify defective JM1 modules, and which offers the most useful risk ranking for prioritizing manual review?", bold=True)

heading("II. DATASET AND PREPARATION", 1)
para("The JM1 ARFF file was obtained from the DefectData repository [1], [2]. Each row represents a software module. The final attribute is the binary defect target; the remaining 21 attributes are numeric software metrics.")
add_table("TABLE I. JM1 DATASET AND SPLIT SUMMARY", ["Quantity", "Value"], [
    ["Modules / predictors", "7,782 / 21"],
    ["Defective modules", "1,672 (21.5%)"],
    ["Non-defective modules", "6,110 (78.5%)"],
    ["Missing feature values", "0"],
    ["Exact duplicate rows", "0"],
    ["Training / test modules", "6,225 / 1,557"],
    ["Test defects / non-defects", "335 / 1,222"],
], [2.05, 1.35], 7.5)
para("No records required removal for missingness or duplication. We retained the numeric measurements without discretization. The stratified split used 80% of the data for training and 20% for testing, with random seed 42. All preprocessing was fit only on training data. Median imputation and standard scaling were included in the KNN pipeline; imputation is a safeguard because no missing feature values were found. Decision Tree and XGBoost used unscaled feature values.")

heading("A. Descriptive Statistics and Correlation", 2)
para("LOC_TOTAL is right-skewed: its mean is 46.25, median 26, standard deviation 80.58, variance 6,492.36, skewness 15.47, and excess kurtosis 488.22. The large difference between its mean and median reflects a long upper tail.")
para("Selected metric pairs show high association. Pearson correlation is 0.956 between LOC_TOTAL and HALSTEAD_VOLUME, and 0.969 between BRANCH_COUNT and CYCLOMATIC_COMPLEXITY. Spearman rank correlation for the latter pair is 0.996. These are descriptive associations, not evidence of causation; correlated metrics can also share model importance.")

heading("III. METHODS", 1)
heading("A. Decision Tree", 2)
para("The Decision Tree recursively partitions the metric space into groups with more homogeneous target labels. We used Gini impurity, maximum depth 6, minimum leaf size 10, and balanced class weights. The tree reached depth 6 and had 48 leaves. Class weighting increases the contribution of the minority class during training [3].")
heading("B. K-Nearest Neighbors", 2)
para("KNN assigns each test module the majority label among its five nearest training examples under Euclidean distance. Since feature scales differ, the pipeline applied median imputation and standard scaling before distance calculations. We used uniform neighbor weights and k=5 [4].")
heading("C. XGBoost", 2)
para("XGBoost builds a sequence of regularized decision trees, where each new tree improves the ensemble's remaining prediction errors [5]. The classifier used 300 estimators, maximum depth 4, learning rate 0.05, row subsampling 0.8, feature subsampling 0.8, and L2 regularization of 1. To account for imbalance, scale_pos_weight was set to the ratio of non-defective to defective training modules, 4888/1337 approximately 3.657. The settings were fixed before evaluating the test set; no hyperparameter search was conducted.")
heading("D. Evaluation", 2)
para("We report accuracy, defective-class precision, recall, and F1 at the default 0.5 probability threshold. ROC-AUC summarizes ranking across classification thresholds; 0.5 corresponds to random ranking [6]. We also rank modules by estimated defect risk and calculate top-decile lift as the defect rate among the highest-risk 10% divided by the defect rate in the full test set. The top decile contains ceil(0.10 x 1,557)=156 modules. A majority-class baseline that predicts every module as non-defective is included for accuracy context.")

heading("IV. RESULTS", 1)
heading("A. Overall Performance", 2)
para("Table II summarizes test-set results. XGBoost has the highest ROC-AUC (0.659) and top-decile lift (2.03). The Decision Tree has the highest defect recall (56.7%) at the default threshold. KNN has higher accuracy than the other learned models, but its recall is only 18.8%. The majority-class baseline reaches 78.5% accuracy and zero recall, so all three classifiers fall below it on accuracy.")
add_table("TABLE II. PERFORMANCE ON THE HELD-OUT JM1 TEST SET", ["Model", "Acc. / Prec.", "Recall / F1", "AUC / Lift"], [
    ["Decision Tree", "62.6 / 30.3%", "56.7% / .395", ".643 / 1.85"],
    ["KNN (k=5)", "75.5 / 36.6%", "18.8% / .249", ".617 / 1.67"],
    ["XGBoost", "66.7 / 32.9%", "52.8% / .405", ".659 / 2.03"],
    ["Majority baseline", "78.5 / --", "0.0% / .000", "-- / 1.00"],
], [1.10, .90, .87, .85], 6.8)
para("Accuracy, precision, and recall are percentages; F1, AUC, and lift are unitless. The baseline demonstrates why accuracy alone is inadequate for an imbalanced target.")

heading("B. Confusion Matrices", 2)
para("Table III gives the counts with actual classes as rows and predicted classes as columns. XGBoost identified 177 defective modules, compared with 190 for the Decision Tree and 63 for KNN. The Decision Tree's higher recall is accompanied by 438 false positives. XGBoost produced 361 false positives and 158 missed defects.")
add_table("TABLE III. CONFUSION COUNTS (TP/FN AND FP/TN)", ["Model", "TP / FN", "FP / TN"], [
    ["Decision Tree", "190 / 145", "438 / 784"],
    ["KNN (k=5)", "63 / 272", "109 / 1,113"],
    ["XGBoost", "177 / 158", "361 / 861"],
], [1.55, 1.05, 1.1], 7.1)

heading("C. ROC and Risk-Ranked Inspection", 2)
para("Fig. 1 shows ROC curves. XGBoost's AUC advantage over the Decision Tree is modest (0.659 versus 0.643); one test split is insufficient to establish whether the difference is statistically significant. Fig. 2 shows cumulative gains when modules are reviewed from highest to lowest predicted risk.")
para("Within the highest-risk 10% (156 modules), XGBoost captured 68 of 335 defects (20.3% of all test defects), giving 2.03x lift. The Decision Tree captured 62 defects (18.5%, 1.85x lift), and KNN captured 56 (16.7%, 1.67x lift). XGBoost therefore provides the most enriched top-decile review group in this split, although the gain over the other models is limited.")
add_figure(PROJECT / "figures" / "roc_curve.png", "Fig. 1. ROC curves on the held-out JM1 test set.")
add_figure(PROJECT / "figures" / "cumulative_gains.png", "Fig. 2. Cumulative fraction of test defects captured by reviewing modules in descending predicted-risk order.")

heading("D. Feature Importance", 2)
para("The Decision Tree's five leading impurity-based features were LOC_TOTAL (0.394), LOC_BLANK (0.122), LOC_EXECUTABLE (0.088), HALSTEAD_EFFORT (0.075), and HALSTEAD_CONTENT (0.054). XGBoost's five leading gain-based importances were LOC_TOTAL (0.103), LOC_BLANK (0.078), NUM_UNIQUE_OPERANDS (0.060), LOC_EXECUTABLE (0.056), and HALSTEAD_VOLUME (0.050). Importance values are model-specific split summaries, not causal effects. Because metrics are correlated, importance may be divided among related features.")

# All result tables and figures above are inline before interpretation/conclusion.
heading("V. DISCUSSION", 1)
para("The three models present different operating trade-offs. XGBoost provides the strongest overall ranking by ROC-AUC and top-decile lift; the Decision Tree detects more defects using the default threshold. KNN's 75.5% accuracy is below the all-non-defective baseline and coexists with low defect recall, illustrating why accuracy should not be used alone for an imbalanced target.")
para("For limited manual review capacity, risk ranking may be more useful than a fixed default label threshold. XGBoost is the strongest candidate of these tested configurations for prioritizing the top decile, but its test-set performance is still modest. The results should be treated as educational baselines rather than evidence of production readiness.")
heading("A. Limitations and Statistical Significance", 2)
para("Only JM1 and one stratified holdout split were analyzed. We did not perform cross-validation, hyperparameter tuning, external validation, or a hypothesis test; no p-value or statistical superiority claim is reported. Scores are descriptive for this split and may vary across splits and projects. The benchmark labels and static metrics may not transfer to a current software team. Correlation and feature importance are not interpreted causally.")

heading("VI. CONCLUSION", 1)
para("On this JM1 holdout, XGBoost achieved the strongest defect-risk ranking (ROC-AUC 0.659; top-decile lift 2.03), while the class-balanced Decision Tree achieved the highest default-threshold recall (56.7%). KNN had low recall (18.8%) and did not exceed the majority-class accuracy baseline. All models show limited predictive quality. Repeated validation, threshold selection based on review costs, and evaluation on independent projects are needed before practical use.")
heading("REPRODUCIBILITY", 1)
para("The split used train_test_split(test_size=0.20, stratify=y, random_state=42). The analysis ran with scikit-learn 1.7.2 and XGBoost 3.4.1. All reported metrics were computed from the repository's JM1 ARFF file.")

heading("REFERENCES", 1)
refs = [
    "[1] klainfo, “DefectData: An R Package of Software Metric Datasets,” repository README. [Online]. Available: https://github.com/klainfo/DefectData",
    "[2] klainfo, “DefectData Data Loading Function,” JM1 source loading and target definition. [Online]. Available: https://github.com/klainfo/DefectData/blob/master/R/loadData.R",
    "[3] scikit-learn developers, “DecisionTreeClassifier Documentation.” [Online]. Available: https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html",
    "[4] scikit-learn developers, “KNeighborsClassifier Documentation.” [Online]. Available: https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html",
    "[5] T. Chen and C. Guestrin, “XGBoost: A Scalable Tree Boosting System,” in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.",
    "[6] T. Fawcett, “An Introduction to ROC Analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006, doi: 10.1016/j.patrec.2005.10.010.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(.12)
    p.paragraph_format.first_line_indent = Inches(-.12)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run(ref), size=7.0)

# Remove inherited borders from built-in title style; title uses direct styling above.
title_style = styles["Title"]
title_style.font.color.rgb = RGBColor.from_string("000000")
title_style.font.underline = False
tpr = title_style._element.get_or_add_pPr()
for border in list(tpr.findall(qn("w:pBdr"))):
    tpr.remove(border)

doc.core_properties.title = "Software Defect Prediction in JM1"
doc.core_properties.author = "Aditya Dubey"
doc.core_properties.subject = "Conference-style comparison of Decision Tree, KNN, and XGBoost"
doc.save(OUT)
print(OUT)
