
import streamlit as st
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ==========================================
# 1. 頁面基本設定
# ==========================================
st.set_page_config(page_title="HK Salaries Tax Calculator", layout="centered")

# ==========================================
# 2. 稅款計算引擎
# ==========================================
def calculate_tax(net_chargeable_income, net_income):
    progressive_tax = 0.0
    temp_prog = net_chargeable_income
    
    # 累進稅率階梯保持不變
    tax_brackets = [
        {"limit": 50000, "rate": 0.02},
        {"limit": 50000, "rate": 0.06},
        {"limit": 50000, "rate": 0.10},
        {"limit": 50000, "rate": 0.14},
        {"limit": float('inf'), "rate": 0.17}
    ]
    
    for bracket in tax_brackets:
        if temp_prog > 0:
            step = min(temp_prog, bracket["limit"])
            progressive_tax += step * bracket["rate"]
            temp_prog -= step
        else:
            break

    # 標準稅率 (首 $5,000,000 @ 15%，餘額 @ 16%) 適用於 25/26 及 26/27
    standard_tax = 0.0
    if net_income <= 5000000:
        standard_tax = net_income * 0.15
    else:
        standard_tax = (5000000 * 0.15) + ((net_income - 5000000) * 0.16)

    payable_tax = min(progressive_tax, standard_tax)
    return payable_tax, progressive_tax, standard_tax

# ==========================================
# 3. 中英雙語 PDF 生成引擎 
# ==========================================
def generate_pdf(selected_year, user_name, marital_status, income, total_deductions, total_allowance, current_year_tax, provisional_tax, total_tax_assessed, provisional_tax_paid, balance_payable):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    pdfmetrics.registerFont(UnicodeCIDFont('MSung-Light'))
    font_name = 'MSung-Light'
    
    c.setFont(font_name, 18)
    c.drawString(50, 750, f"Hong Kong Salaries & Provisional Tax Summary ({selected_year})")
    c.drawString(50, 725, f"(香港薪俸稅及暫繳稅計算摘要 - {selected_year})")
    
    c.setFont(font_name, 14)
    c.drawString(50, 680, "1. Personal Information (個人資料)")
    c.setFont(font_name, 12)
    name_str = user_name if user_name else "Taxpayer (納稅人)"
    c.drawString(50, 660, f"Name (姓名): {name_str}")
    c.drawString(50, 640, f"Marital Status (婚姻狀況): {marital_status}")
    
    c.setFont(font_name, 14)
    c.drawString(50, 600, "2. Income & Deductions (入息及扣除額)")
    c.setFont(font_name, 12)
    c.drawString(50, 580, f"Total Income (總入息): HKD {income:,.2f}")
    c.drawString(50, 560, f"Total Deductions Claimed (總申索扣除額): HKD {total_deductions:,.2f}")
    
    c.setFont(font_name, 14)
    c.drawString(50, 520, "3. Allowances (免稅額)")
    c.setFont(font_name, 12)
    c.drawString(50, 500, f"Total Allowances Claimed (總申索免稅額): HKD {total_allowance:,.2f}")
    
    c.setFont(font_name, 16)
    c.drawString(50, 450, "--- Final Tax Calculation (最終稅款計算) ---")
    c.setFont(font_name, 12)
    c.drawString(50, 420, f"Current Year Tax (本年度稅款): HKD {current_year_tax:,.2f}")
    c.drawString(50, 400, f"Next Year Provisional Tax (下年度暫繳稅): HKD {provisional_tax:,.2f}")
    c.drawString(50, 380, f"Total Tax Assessed (評定總稅款): HKD {total_tax_assessed:,.2f}")
    
    c.drawString(50, 360, f"Less: Provisional Tax Paid (扣減已繳交之暫繳稅): - HKD {provisional_tax_paid:,.2f}")
    
    c.setFont(font_name, 16)
    if balance_payable >= 0:
        c.drawString(50, 310, f"BALANCE PAYABLE (應繳總結欠): HKD {balance_payable:,.2f}")
    else:
        c.drawString(50, 310, f"TAX REFUND (退還稅款): HKD {abs(balance_payable):,.2f}")
    
    c.setFont(font_name, 10)
    c.drawString(50, 60, "* This is an estimated calculation based on the provided inputs.")
    c.drawString(50, 45, "  (此乃基於您提供的資料作出的初步估算。)")
    c.drawString(50, 30, "* Please refer to the official Inland Revenue Department (IRD) assessment for actual tax bills.")
    c.drawString(50, 15, "  (實際稅款請以香港稅務局發出的評稅通知書為準。)")
    
    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# 4. 主程式 (Streamlit 網頁介面)
# ==========================================
def main():
    st.title("🇭🇰 HK Salaries & Provisional Tax Calculator") 
    st.markdown("---")
    
    # --- 新增：選擇課稅年度 ---
    st.header("📅 Year of Assessment (課稅年度)")
    selected_year = st.radio("Select Year of Assessment (請選擇):", ["2025/26", "2026/27"], horizontal=True)
    
    # 根據年份動態設定免稅額及扣除額上限
    if selected_year == "2025/26":
        basic_allowance_rate = 132000.0
        married_allowance_rate = 264000.0
        child_allowance_rate = 130000.0
        parent_allowance_rate = 50000.0
        elderly_care_max = 100000.0
    else: # 2026/27 增強版
        basic_allowance_rate = 145000.0
        married_allowance_rate = 290000.0
        child_allowance_rate = 140000.0
        parent_allowance_rate = 55000.0
        elderly_care_max = 110000.0
    
    st.markdown("---")
    st.header("👤 1. Personal Information (個人資料)")
    user_name = st.text_input("User Name (用戶名稱):")
    marital_status = st.radio(f"Marital Status (婚姻狀況) [單身: ${basic_allowance_rate:,.0f} / 已婚: ${married_allowance_rate:,.0f}]:", ["Single (單身)", "Married (已婚)"])
    
    col_dep1, col_dep2 = st.columns(2)
    with col_dep1:
        num_children = st.number_input(f"Number of Dependent Children (供養子女) [每名 ${child_allowance_rate:,.0f}]:", min_value=0, value=0, step=1)
    with col_dep2:
        num_parents = st.number_input(f"Number of Dependent Parents 60+ (供養父母) [每名 ${parent_allowance_rate:,.0f}]:", min_value=0, value=0, step=1)

    st.header("💰 2. Income & Deductions (入息及扣除額)")
    income = st.number_input("Total Income (總入息) [HKD]:", min_value=0.0, value=300000.0, step=1000.0)
    
    st.subheader("Detailed Deductions (詳細扣除額)")
    mpf = st.number_input("1. MPF Contributions (強積金供款) [Max $18,000]:", min_value=0.0, max_value=18000.0, value=15000.0, step=100.0)
    self_education = st.number_input("2. Self-Education Expenses (個人進修開支) [Max $100,000]:", min_value=0.0, max_value=100000.0, value=0.0, step=1000.0)
    
    donation_input = st.number_input("3. Approved Charitable Donations (認可慈善捐款):", min_value=0.0, value=0.0, step=1000.0)
    donation_cap = income * 0.35 
    actual_donation = min(donation_input, donation_cap)
    
    home_housing = st.number_input("4. Home Loan Interest / Domestic Rents (居所貸款利息 / 租金) [Max $120,000]:", min_value=0.0, max_value=120000.0, value=0.0, step=1000.0)
    # 長者照顧開支上限會根據年份自動調整
    elderly_care = st.number_input(f"5. Elderly Residential Care Expenses (長者住宿照顧) [Max ${elderly_care_max:,.0f}]:", min_value=0.0, max_value=elderly_care_max, value=0.0, step=1000.0)
    vhis = st.number_input("6. VHIS Policy Premiums (自願醫保計劃保費) [Max $8,000 per insured]:", min_value=0.0, value=0.0, step=1000.0)
    annuity_tvc = st.number_input("7. Annuity Premiums & TVC (合資格延期年金 / TVC) [Max $60,000]:", min_value=0.0, max_value=60000.0, value=0.0, step=1000.0)
    
    total_deductions = mpf + actual_donation + self_education + home_housing + elderly_care + vhis + annuity_tvc

    st.header("✂️ 3. One-off Tax Reduction (稅款寬減)")
    tax_reduction_limit = st.number_input("Tax Reduction Rebate [HKD] (預設為 $0):", min_value=0.0, value=0.0, step=1000.0)

    st.header("⏳ 4. Provisional Tax Paid (已繳交之暫繳稅)")
    provisional_tax_paid = st.number_input("Provisional Tax Paid for the Year (本年度已繳交) [HKD]:", min_value=0.0, value=0.0, step=1000.0)

    # --- 核心運算 ---
    # 根據已選年份動態計算免稅額
    base_allowance = married_allowance_rate if marital_status == "Married (已婚)" else basic_allowance_rate
    child_allowance = num_children * child_allowance_rate
    parent_allowance = num_parents * parent_allowance_rate
    total_allowance = base_allowance + child_allowance + parent_allowance

    net_income = max(0.0, income - total_deductions)
    net_chargeable_income = max(0.0, net_income - total_allowance)
        
    payable_tax_before_reduction, prog_tax, std_tax = calculate_tax(net_chargeable_income, net_income)
    
    current_year_tax = max(0.0, payable_tax_before_reduction - tax_reduction_limit)
    provisional_tax = payable_tax_before_reduction
    total_tax_assessed = current_year_tax + provisional_tax

    balance_payable = total_tax_assessed - provisional_tax_paid

    # --- 顯示結果 ---
    st.markdown("---")
    if user_name:
        st.header(f"📊 Tax Summary for {user_name} ({selected_year})")
    else:
        st.header(f"📊 Tax Summary ({selected_year})")
        
    st.write(f"**Total Deductions (總扣除額):** ${total_deductions:,.2f}")
    st.write(f"**Total Allowances (總免稅額):** ${total_allowance:,.2f}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Year Tax (本年度)", f"${current_year_tax:,.2f}")
    with col2:
        st.metric("Next Year Prov. (下年度)", f"${provisional_tax:,.2f}")
    with col3:
        st.metric("Less: Tax Paid (扣減已繳稅)", f"-${provisional_tax_paid:,.2f}")
    with col4:
        if balance_payable >= 0:
            st.metric("💰 Balance Payable (應繳結欠)", f"${balance_payable:,.2f}")
        else:
            st.metric("💰 Tax Refund (退款)", f"${abs(balance_payable):,.2f}")
            
    # --- 匯出 PDF 按鈕 ---
    st.markdown("---")
    st.header("🖨️ Export to PDF (匯出報告)")
    
    pdf_buffer = generate_pdf(selected_year, user_name, marital_status, income, total_deductions, total_allowance, current_year_tax, provisional_tax, total_tax_assessed, provisional_tax_paid, balance_payable)
    file_name_str = f"Tax_Summary_{selected_year.replace('/','-')}_{user_name.replace(' ', '_')}.pdf" if user_name else f"HK_Tax_Summary_{selected_year.replace('/','-')}.pdf"
    
    st.download_button(
        label=f"📄 Download Tax Summary (下載 {selected_year} PDF 報表)",
        data=pdf_buffer,
        file_name=file_name_str,
        mime="application/pdf"
    )

if __name__ == "__main__": 
    main() 