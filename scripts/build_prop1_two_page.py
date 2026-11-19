from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "PROP1" / "Two_Page_Report.docx"
FIG_DIR = ROOT / "results" / "PROP1" / "figures"
ROC = FIG_DIR / "roc_curve.png"
GAINS = FIG_DIR / "cumulative_gains.png"
NAVY, TEAL, PALE, INK, MUTED = "173A56", "167D87", "EAF1F4", "202830", "56636D"

def font(run, size=9.1, bold=False, italic=False, color=INK, face="Cambria"):
    run.font.name = face
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), face)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), face)
    run.font.size = Pt(size)
    run.bold, run.italic = bold, italic
    run.font.color.rgb = RGBColor.from_string(color)

def shade(cell, color):
    el = OxmlElement("w:shd"); el.set(qn("w:fill"), color); cell._tc.get_or_add_tcPr().append(el)

def no_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

def para(doc, text, size=9.1, after=4, before=0, align=None, keep=False, color=INK, italic=False):
    p = doc.add_paragraph()
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.line_spacing = 1.04
    p.paragraph_format.keep_together = keep
    font(p.add_run(text), size, color=color, italic=italic)
    return p

def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(7 if level == 1 else 4)
    p.paragraph_format.space_after = Pt(2.4)
    font(p.add_run(text), 11.2 if level == 1 else 9.6, True, color=NAVY if level == 1 else TEAL)
    return p

def table(doc, caption, headers, rows, widths, size=7.7):
    cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(2); cap.paragraph_format.space_after = Pt(2); cap.paragraph_format.keep_with_next = True
    font(cap.add_run(caption), 7.8, True, color=NAVY, face="Arial")
    t = doc.add_table(rows=1, cols=len(headers)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False; t.style = "Table Grid"
    for j, val in enumerate(headers):
        c=t.rows[0].cells[j]; c.width=Inches(widths[j]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        c.text=""; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(0)
        font(p.add_run(val), size, True, color="FFFFFF", face="Arial"); shade(c,NAVY)
    no_split(t.rows[0])
    for i,row in enumerate(rows):
        cells=t.add_row().cells; no_split(t.rows[-1])
        for j,val in enumerate(row):
            c=cells[j]; c.width=Inches(widths[j]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; c.text=""
            p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
            font(p.add_run(str(val)),size, color=INK, face="Arial")
            if i%2: shade(c,PALE)
    para(doc,"",size=2,after=0)
    return t

def main():
    d=Document(); s=d.sections[0]
    s.page_width,s.page_height=Inches(8.5),Inches(11)
    s.top_margin=s.bottom_margin=Inches(.55); s.left_margin=s.right_margin=Inches(.68)
    s.header_distance=Inches(.26); s.footer_distance=Inches(.28)
    normal=d.styles["Normal"]; normal.font.name="Cambria"; normal.font.size=Pt(9.1)
    normal.paragraph_format.space_after=Pt(4); normal.paragraph_format.line_spacing=1.04
    # Quiet running header and a centered page number provide consistent alignment.
    h=s.header.paragraphs[0]; h.alignment=WD_ALIGN_PARAGRAPH.RIGHT; h.paragraph_format.space_after=Pt(0)
    font(h.add_run("PROP-1  |  SOFTWARE DEFECT PREDICTION"),7.2,True,color=MUTED,face="Arial")
    f=s.footer.paragraphs[0]; f.alignment=WD_ALIGN_PARAGRAPH.CENTER
    font(f.add_run("Aditya Dubey  •  "),7.5,color=MUTED,face="Arial")
    fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); f._p.append(fld)
    d.core_properties.author="Aditya Dubey"; d.core_properties.title="Software Defect Prediction in PROP-1"
    d.core_properties.subject="Two-page analysis of PROP-1 using XGBoost and baseline classifiers"

    title=d.add_paragraph(); title.alignment=WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before=Pt(2); title.paragraph_format.space_after=Pt(3)
    font(title.add_run("Software Defect Prediction in PROP-1"),20,True,color=NAVY)
    sub=d.add_paragraph(); sub.alignment=WD_ALIGN_PARAGRAPH.CENTER; sub.paragraph_format.space_after=Pt(3)
    font(sub.add_run("A grouped evaluation of Decision Tree, KNN, and XGBoost"),11.2,color=TEAL)
    by=d.add_paragraph(); by.alignment=WD_ALIGN_PARAGRAPH.CENTER; by.paragraph_format.space_after=Pt(6)
    font(by.add_run("Aditya Dubey"),9.2,True,color=MUTED,face="Arial")

    heading(d,"Abstract")
    para(d,"This report evaluates whether static object-oriented software metrics can help identify defective modules in PROP-1. The dataset contains 18,471 records and 20 numeric predictors; 14.82% of records are labeled defective. To limit information leakage from repeated metric patterns, identical feature vectors were assigned to the same side of a stratified group split. On the resulting 3,611-record test fold, XGBoost achieved the strongest overall ranking (ROC-AUC 0.819) and the highest top-decile lift (3.33). A class-balanced Decision Tree found the greatest proportion of defects at the default threshold (recall 78.1%). Results are promising for prioritization but remain descriptive of one holdout fold.",size=9.0,after=3)

    heading(d,"1. Introduction")
    para(d,"Software teams cannot inspect every module with equal effort. Defect prediction uses historical labels and code measurements to estimate which modules may deserve earlier review. PROP-1 provides CKJM-style measures of size, coupling, cohesion, inheritance, and complexity. The task here is binary classification: a record is defective when its bug count is greater than zero. Since defective records are the minority, a high accuracy score alone could hide poor defect detection.")

    heading(d,"2. Dataset and preparation")
    para(d,"The PROP-1 file has 18,471 observations, 20 numeric software metrics, and 2,738 defective labels. The remaining 15,733 records are non-defective, giving a 14.82% defect prevalence. The fields Name and version were excluded because they identify modules or releases rather than describe module properties. No metric values were missing, so no imputation was required. Metrics were kept in their original units for the tree models; KNN used median imputation as a safeguard and standard scaling because distance calculations are sensitive to feature scale.")
    para(d,"Repeated values required special care. There are 3,337 repeated full rows, and 9,799 rows belong to repeated 20-metric vectors; 661 vectors appear with both labels. Without a unique module identifier, these rows cannot safely be assumed to be erroneous duplicates. They were retained, while identical vectors were grouped during splitting to prevent the same pattern from appearing in both training and test partitions.")
    table(d,"TABLE 1. DATA PROFILE AND EVALUATION SPLIT",["Measure","Value"],[
        ["Rows and numeric predictors","18,471; 20"],["Defective / non-defective","2,738 (14.82%) / 15,733"],
        ["Missing metric cells","0"],["Training / test rows","14,860 / 3,611"],
        ["Test fold labels","566 defective; 3,045 non-defective"],
    ],[3.7,3.45],7.8)

    heading(d,"3. Analysis method")
    para(d,"A shuffled, stratified five-fold group split (random seed 42) supplied the first fold as the holdout set. This yielded 14,860 training and 3,611 test observations. Grouping was based on the complete vector of 20 metrics; label stratification preserved a test prevalence (15.7%) reasonably close to the dataset rate. No test-fold records were used to fit preprocessing or models.")
    para(d,"Three supervised classifiers were compared. The Decision Tree used Gini splitting, depth 6, minimum leaf size 10, and balanced class weights. KNN used five Euclidean neighbors after standard scaling. XGBoost combined 300 shallow trees (depth 4, learning rate 0.05) with row and feature subsampling of 0.8, L2 regularization, and a positive-class weight of 5.842. Hyperparameters were fixed without test-set tuning. Predictions at probability 0.5 were assessed with accuracy, defective-class precision, recall, and F1. ROC-AUC evaluates ranking across thresholds; top-decile lift asks how enriched the highest-risk 10% is for defects compared with the test-set average.")

    heading(d,"4. Descriptive profile")
    para(d,"The lines-of-code metric (loc) has a mean of 206.63 but a median of 73, with standard deviation 420.07, skewness 6.11, and excess kurtosis 56.57. This long right tail means a small number of very large modules influence the mean and variance. The Pearson correlation between loc and weighted methods per class (wmc) is 0.622. Maximum and average cyclomatic complexity (max_cc and avg_cc) have Pearson correlation 0.796 and Spearman correlation 0.934, showing a strong monotonic association. These correlations are descriptive and do not show that one metric causes defects.")

    d.add_page_break()
    # Page two intentionally keeps all outcome tables and figures together, followed by conclusion and references.
    heading(d,"5. Results")
    para(d,"Table 2 shows that XGBoost had the highest F1 (0.478), ROC-AUC (0.819), and top-decile lift (3.33). The Decision Tree achieved the highest recall (78.1%), detecting 442 of the 566 test defects, but it also generated many false alarms. KNN was the most conservative model: it had the highest precision among fitted models (48.6%) and fewest false positives, but detected only 32.7% of defects. Its accuracy (84.0%) was slightly below the 84.3% majority-class baseline, which predicts every record as non-defective.",size=8.9,after=3)
    table(d,"TABLE 2. HOLDOUT PERFORMANCE (DEFECT CLASS IS POSITIVE)",["Model","Accuracy","Precision","Recall","F1","AUC","Top-10% lift"],[
        ["Decision Tree","62.7%","26.5%","78.1%","0.396","0.778","2.93"],
        ["KNN (k=5)","84.0%","48.6%","32.7%","0.391","0.745","3.15"],
        ["XGBoost","75.0%","35.5%","72.8%","0.478","0.819","3.33"],
        ["Majority baseline","84.3%","—","0.0%","0.000","—","1.00"],
    ],[1.62,.82,.82,.72,.65,.62,1.05],7.1)
    para(d,"In the confusion counts, XGBoost produced 412 true positives, 154 missed defects, 747 false positives, and 2,298 true negatives. The Decision Tree found 30 more defects than XGBoost, at the cost of 477 additional false positives. KNN produced only 196 false positives but missed 381 defects. Thus, the preferred model depends on the review team's tolerance for missed defects versus unnecessary inspections.",size=8.7,after=2)
    para(d,"At a review capacity of roughly one tenth of the test fold (362 modules), XGBoost ranked 189 defects in that group, compared with 179 for KNN and 166 for the Decision Tree. XGBoost's top-decile defect rate was 3.33 times the overall test rate. The ROC and cumulative-gains charts visualize these ranking differences; they complement the fixed-threshold scores rather than replacing them.",size=8.7,after=1)

    # Two aligned figure cells keep the graphic row balanced and captions attached.
    ft=d.add_table(rows=1,cols=2); ft.alignment=WD_TABLE_ALIGNMENT.CENTER; ft.autofit=False
    for c in ft.rows[0].cells: c.width=Inches(3.55); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for cell,img,caption in [(ft.cell(0,0),ROC,"Fig. 1. ROC curves (AUC in legend)."),(ft.cell(0,1),GAINS,"Fig. 2. Defects captured by risk rank.")]:
        p=cell.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(1)
        p.add_run().add_picture(str(img),width=Inches(3.25))
        cp=cell.add_paragraph(); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; cp.paragraph_format.space_after=Pt(0)
        font(cp.add_run(caption),7.1,italic=True,color=MUTED,face="Arial")
    no_split(ft.rows[0])

    heading(d,"6. Interpretation and limitations")
    para(d,"XGBoost is the strongest of the tested models when the objective is to rank modules for limited manual inspection. The Decision Tree is a reasonable alternative when catching as many defects as possible at a fixed threshold matters more than false alarms. The majority baseline's high accuracy reinforces why recall, F1, AUC, confusion counts, and lift should be read alongside accuracy for this imbalanced dataset. XGBoost's leading gain features were ce, cbo, cam, npm, and loc; these model-based importance scores are not causal explanations.",size=8.5,after=2)
    para(d,"The study uses one grouped holdout fold, one project dataset, and fixed model settings. It does not include repeated grouped cross-validation, parameter search, external validation, or hypothesis testing. Therefore, the observed AUC differences are not evidence of statistical significance, and no p-value or claim of model superiority is reported. Repeating grouped evaluation across folds and validating on another project would provide stronger evidence.",size=8.5,after=2)
    heading(d,"7. Conclusion")
    para(d,"For this PROP-1 holdout, XGBoost delivered the best overall risk ranking (AUC 0.819; top-decile lift 3.33), while the Decision Tree recovered the largest share of defects at the default threshold (recall 78.1%). KNN reduced false alarms but missed more defects. These results support using risk scores to prioritize inspection, with the final threshold chosen according to review capacity and the cost of missed defects. Further grouped validation is needed before generalizing beyond this dataset.",size=8.5,after=2)
    heading(d,"References",1)
    refs=[
        "[1] klainfo, DefectData: An R Package of Defect Prediction Datasets, PROP-1 profile. github.com/klainfo/DefectData.",
        "[2] T. Chen and C. Guestrin, “XGBoost: A Scalable Tree Boosting System,” Proc. KDD, 2016, pp. 785–794, doi:10.1145/2939672.2939785.",
        "[3] T. Fawcett, “An Introduction to ROC Analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006, doi:10.1016/j.patrec.2005.10.010.",
    ]
    for r in refs:
        p=d.add_paragraph(); p.paragraph_format.left_indent=Inches(.14); p.paragraph_format.first_line_indent=Inches(-.14); p.paragraph_format.space_after=Pt(1); p.paragraph_format.line_spacing=1.0
        font(p.add_run(r),7.0,color=INK,face="Arial")
    d.save(OUT)
    print(OUT)

if __name__=="__main__": main()
