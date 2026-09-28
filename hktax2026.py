import io
import re
from datetime import datetime
import streamlit as st
import config

# ReportLab PDF Engine
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ==========================================
# 1. Page Configuration & Styling
# ==========================================
st.set_page_config(
    page_title="香港薪俸稅及暫繳稅計算器 2026",
    layout="centered",
    page_icon="🇭🇰"
)

st.markdown("""
    <style>
    .main-header {
        text-align: center;
        font-weight: bold;
        padding-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. PDF Report Generator Engine
# ==========================================
def generate_pdf(res):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    pdfmetrics.registerFont(UnicodeCIDFont('MSung-Light'))
    font_name = 'MSung-Light'
    
    c.setFont(font_name, 16)
    c.drawString(50, 750, f"香港薪俸稅計算摘要報告 ({res['year']})")
    c.drawString(50, 730, f"HK Salaries Tax Summary Report ({res['year']})")
    
    c.setFont(font_name, 11)
    c.drawString(50, 690, f"納稅人姓名 (Taxpayer Name): {res['taxpayer_name']}")
    c.drawString(50, 670, f"課稅年度 (Tax Year): {res['year']}")
    c.drawString(50, 650, f"婚姻狀況 (Marital Status): {res['marital_status']}")
    
    c.setFont(font_name, 13)
    c.drawString(50, 610, "計算結果明細 (Calculation Breakdown)")
    c.setFont(font_name, 11)
    
    items = [
        ("總收入 (Gross Income)", f"HKD ${res['gross_income']:,.2f}"),
        ("扣除額總額 (Total Deductions)", f"HKD ${res['total_deductions']:,.2f}"),
        ("入息淨額 (Net Income)", f"HKD ${res['net_income']:,.2f}"),
        ("免稅額總額 (Total Allowances)", f"HKD ${res['total_allowances']:,.2f}"),
        ("應課稅入息實額 (Net Chargeable Income)", f"HKD ${res['net_chargeable_income']:,.2f}"),
        ("計稅方法 (Calculation Method)", f"{res['tax_method']}"),
        ("本年度應繳薪俸稅 (Salaries Tax)", f"HKD ${res['final_tax']:,.2f}"),
        ("下一年度暫繳稅 (Provisional Tax)", f"HKD ${res['provisional_tax']:,.2f}"),
        ("預計總應繳稅款 (Total Estimated Tax)", f"HKD ${res['total_tax']:,.2f}")
    ]
    
    y = 580
    for label, val in items:
        c.drawString(50, y, f"{label}: {val}")
        y -= 22
        
    c.setFont(font_name, 9)
    c.drawString(50, 50, "* 此乃基於您輸入資料作出的估算，實際稅款請以香港稅務局發出的評稅通知書為準。")
    c.drawString(50, 38, "  (This is an estimated calculation based on user input. Please refer to official IRD assessments.)")
    
    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# 3. Tax Engine Logic
# ==========================================
def calculate_tax(taxpayer_name, year, marital_status, gross_income, children_count, newborn_count,
                  parents_60, parents_60_live, parents_55, parents_55_live,
                  mpf, self_edu, home_loan, vhis, tvc, elderly_care, donations):
    
    # Safe retrieval from config
    tax_cfg = getattr(config, 'TAX_CONFIG', {})
    cfg = tax_cfg.get(year, tax_cfg.get('2026/27', {}))
    
    if not cfg:
        st.error("無法載入稅率設定，請檢查 config.py 是否存在 TAX_CONFIG 字典。")
        return None

    # 1. Deductions
    mpf_d = min(mpf, cfg['DEDUCTIONS_CAP']['MPF'])
    edu_d = min(self_edu, cfg['DEDUCTIONS_CAP']['SELF_EDU'])
    loan_d = min(home_loan, cfg['DEDUCTIONS_CAP']['HOME_LOAN_INTEREST'])
    vhis_d = min(vhis, cfg['DEDUCTIONS_CAP']['VHIS'])
    tvc_d = min(tvc, cfg['DEDUCTIONS_CAP']['TVC'])
    care_d = min(elderly_care, cfg['DEDUCTIONS_CAP']['ELDERLY_CARE'])
    
    inc_after_ded = max(0.0, gross_income - mpf_d - edu_d - loan_d - vhis_d - tvc_d - care_d)
    max_don = inc_after_ded * cfg['DEDUCTIONS_CAP']['CHARITABLE_DONATIONS_RATIO']
    don_d = min(donations, max_don)
    
    total_deductions = mpf_d + edu_d + loan_d + vhis_d + tvc_d + care_d + don_d
    net_income = max(0.0, gross_income - total_deductions)
    
    # 2. Allowances
    allow_cfg = cfg['ALLOWANCES']
    pers_allow = allow_cfg['MARRIED'] if "已婚" in marital_status or "Married" in marital_status else allow_cfg['BASIC']
    child_allow = (children_count * allow_cfg['CHILD_BASIC']) + (newborn_count * allow_cfg['CHILD_NEWBORN_ADDITIONAL'])
    parent_allow = (
        (parents_60 * allow_cfg['PARENT_60_ABOVE_BASIC']) +
        (parents_60_live * allow_cfg['PARENT_60_ABOVE_RESIDING']) +
        (parents_55 * allow_cfg['PARENT_55_59_BASIC']) +
        (parents_55_live * allow_cfg['PARENT_55_59_RESIDING'])
    )
    
    total_allowances = pers_allow + child_allow + parent_allow
    net_chargeable_income = max(0.0, net_income - total_allowances)
    
    # 3. Progressive Tax
    prog_tax = 0.0
    rem = net_chargeable_income
    for band_amount, rate in cfg['PROGRESSIVE_BANDS'][:-1]:
        if rem > band_amount:
            prog_tax += band_amount * rate
            rem -= band_amount
        else:
            prog_tax += rem * rate
            rem = 0.0
            break
    if rem > 0:
        prog_tax += rem * cfg['PROGRESSIVE_BANDS'][-1][1]
        
    # 4. Standard Rate Tax
    std_tiers = cfg['STANDARD_RATE_TIERS']
    if net_income <= std_tiers[0][0]:
        std_tax = net_income * std_tiers[0][1]
    else:
        std_tax = (std_tiers[0][0] * std_tiers[0][1]) + ((net_income - std_tiers[0][0]) * std_tiers[1][1])
        
    final_tax = min(prog_tax, std_tax)
    tax_method = "累進稅率 (Progressive Rate)" if prog_tax <= std_tax else "標準稅率 (Standard Rate)"
    
    return {
        'taxpayer_name': taxpayer_name,
        'year': year,
        'marital_status': marital_status,
        'gross_income': gross_income,
        'total_deductions': total_deductions,
        'net_income': net_income,
        'total_allowances': total_allowances,
        'net_chargeable_income': net_chargeable_income,
        'final_tax': final_tax,
        'provisional_tax': final_tax,
        'total_tax': final_tax * 2,
        'tax_method': tax_method
    }

# ==========================================
# 4. Main Web App Layout
# ==========================================
def main():
    st.markdown("<h2 class='main-header'>香港薪俸稅及暫繳稅計算器</h2>", unsafe_allow_html=True)
    
    # 取得 config 設定
    tax_cfg = getattr(config, 'TAX_CONFIG', {})
    
    with st.form("hktax_form"):
        # 1. 基本資料
        with st.container(border=True):
            st.markdown("#### 1. 基本資料與總收入")
            col1, col2 = st.columns(2)
            
            with col1:
                taxpayer_name = st.text_input("納稅人姓名:", value="Chan Tai Man")
                year = st.selectbox("課稅年度:", ["2026/27", "2025/26"])
                
            cfg_year = tax_cfg.get(year, tax_cfg.get('2026/27', {}))
            basic_amt = cfg_year.get('ALLOWANCES', {}).get('BASIC', 145000)
            married_amt = cfg_year.get('ALLOWANCES', {}).get('MARRIED', 290000)
            
            with col2:
                marital_status = st.selectbox(
                    "婚姻狀況:",
                    [
                        f"單身/分居/離婚/喪偶 (基本免稅額: ${basic_amt:,.0f})",
                        f"已婚 (Married) (已婚人士免稅額: ${married_amt:,.0f})"
                    ]
                )
                gross_income = st.number_input("全年總收入 (HKD):", min_value=0.0, value=600000.0, step=10000.0)

        # 2. 免稅額
        with st.container(border=True):
            st.markdown("#### 2. 免稅額資料 (數量/人數)")
            c1, c2 = st.columns(2)
            with c1:
                children_count = st.number_input("一般子女數量:", min_value=0, value=0)
                parents_60 = st.number_input("供養 60歲或以上 父母/祖父母人數:", min_value=0, value=0)
                parents_55 = st.number_input("供養 55-59歲 父母/祖父母人數:", min_value=0, value=0)
            with c2:
                newborn_count = st.number_input("本年度出生子女數量:", min_value=0, value=0)
                parents_60_live = st.number_input("其中同住人數 (60歲或以上):", min_value=0, value=0)
                parents_55_live = st.number_input("其中同住人數 (55-59歲):", min_value=0, value=0)

        # 3. 扣除額
        with st.container(border=True):
            st.markdown("#### 3. 扣除額項目 (HKD)")
            d1, d2 = st.columns(2)
            with d1:
                mpf = st.number_input("MPF 強制性供款:", min_value=0.0, value=18000.0)
                self_edu = st.number_input("個人進修開支:", min_value=0.0, value=0.0)
                home_loan = st.number_input("居所貸款利息 / 租金:", min_value=0.0, value=0.0)
                vhis = st.number_input("自願醫保 (VHIS):", min_value=0.0, value=0.0)
            with d2:
                tvc = st.number_input("合資格延期年金 (TVC):", min_value=0.0, value=0.0)
                elderly_care = st.number_input("長者住宿照顧開支:", min_value=0.0, value=0.0)
                donations = st.number_input("認可慈善捐款:", min_value=0.0, value=0.0)

        # 表單提交按鈕 (明確放在 st.form 區塊內部的最末端)
        btn_calc = st.form_submit_button("開始計算稅款", type="primary")

    # 4. 結果顯示區塊 (表單外部)
    if btn_calc or 'calc_res' in st.session_state:
        if btn_calc:
            st.session_state.calc_res = calculate_tax(
                taxpayer_name, year, marital_status, gross_income, children_count, newborn_count,
                parents_60, parents_60_live, parents_55, parents_55_live,
                mpf, self_edu, home_loan, vhis, tvc, elderly_care, donations
            )

        res = st.session_state.get('calc_res')

        if res:
            with st.container(border=True):
                st.markdown("#### 計算結果摘要")
                
                output_text = (
                    f"納稅人姓名 (Taxpayer Name): {res['taxpayer_name']}\n"
                    f"課稅年度 (Tax Year): {res['year']}\n"
                    f"--------------------------------------------------\n"
                    f"總收入 (Gross Income): HKD ${res['gross_income']:,.2f}\n"
                    f"扣除額總額 (Total Deductions): HKD ${res['total_deductions']:,.2f}\n"
                    f"入息淨額 (Net Income): HKD ${res['net_income']:,.2f}\n"
                    f"免稅額總額 (Total Allowances): HKD ${res['total_allowances']:,.2f}\n"
                    f"應課稅入息實額 (Net Chargeable Income): HKD ${res['net_chargeable_income']:,.2f}\n"
                    f"--------------------------------------------------\n"
                    f"計稅方法: {res['tax_method']}\n"
                    f"本年度應繳薪俸稅 (Salaries Tax Payable): HKD ${res['final_tax']:,.2f}\n"
                    f"估計下一年度暫繳稅 (Provisional Tax): HKD ${res['provisional_tax']:,.2f}\n"
                    f"預計總應繳稅款總額 (Total Estimated Tax): HKD ${res['total_tax']:,.2f}"
                )
                
                st.code(output_text, language="text")

                safe_name = re.sub(r'[\\/*?:"<>|]', '_', res['taxpayer_name']).replace(' ', '_')
                curr_date = datetime.now().strftime("%Y%m%d")
                pdf_filename = f"{safe_name}_{curr_date}.pdf"
                
                pdf_data = generate_pdf(res)

                st.download_button(
                    label="匯出 PDF 報告",
                    data=pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()