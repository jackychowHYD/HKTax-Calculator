# Hong Kong Salaries Tax Configuration

TAX_CONFIG = {
    "2025/26": {
        "ALLOWANCES": {
            "BASIC": 132000,
            "MARRIED": 264000,
            "CHILD_BASIC": 130000,
            "CHILD_NEWBORN_ADDITIONAL": 130000,
            "PARENT_60_ABOVE_BASIC": 50000,
            "PARENT_60_ABOVE_RESIDING": 50000,
            "PARENT_55_59_BASIC": 25000,
            "PARENT_55_59_RESIDING": 25000,
            "DISABLED_DEPENDANT": 75000,  # 傷殘受養人免稅額
        },
        "DEDUCTIONS_CAP": {
            "MPF": 18000,
            "SELF_EDU": 100000,
            "HOME_LOAN_INTEREST": 100000,
            "VHIS": 8000,
            "TVC": 60000,
            "ELDERLY_CARE": 100000,
            "CHARITABLE_DONATIONS_RATIO": 0.35,
        },
        "PROGRESSIVE_BANDS": [(50000, 0.02), (50000, 0.06), (50000, 0.10), (50000, 0.14), (float('inf'), 0.17)],
        "STANDARD_RATE_TIERS": [(5000000, 0.15), (float('inf'), 0.16)]
    },
    "2026/27": {
        "ALLOWANCES": {
            "BASIC": 145000,
            "MARRIED": 290000,
            "CHILD_BASIC": 140000,
            "CHILD_NEWBORN_ADDITIONAL": 140000,
            "PARENT_60_ABOVE_BASIC": 55000,
            "PARENT_60_ABOVE_RESIDING": 55000,
            "PARENT_55_59_BASIC": 27500,
            "PARENT_55_59_RESIDING": 27500,
            "DISABLED_DEPENDANT": 75000,  # 傷殘受養人免稅額
        },
        "DEDUCTIONS_CAP": {
            "MPF": 18000,
            "SELF_EDU": 100000,
            "HOME_LOAN_INTEREST": 100000,
            "VHIS": 8000,
            "TVC": 60000,
            "ELDERLY_CARE": 110000,
            "CHARITABLE_DONATIONS_RATIO": 0.35,
        },
        "PROGRESSIVE_BANDS": [(50000, 0.02), (50000, 0.06), (50000, 0.10), (50000, 0.14), (float('inf'), 0.17)],
        "STANDARD_RATE_TIERS": [(5000000, 0.15), (float('inf'), 0.16)]
    }
}