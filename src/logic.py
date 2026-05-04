import pandas as pd
import numpy as np
import hashlib
import os

# -------------------------------------------------------------------
# 1. Normalize merchant's names to streamline calculation by merchants 
# -------------------------------------------------------------------
def normalize_merchant_names (df, column_name):
    """Normalize major merchants names"""
    # Mapping merchandise names
    clean_map: dict[str, str] = {                         
    r'^(amazon|amzn).*': 'amazon',
    r'^(temu).*': 'temu',
    r'^(wal|wal)[-.]?mart.*': 'walmart',
    r'^shein.*': 'shein'
    }
    
    df['description'] = df[column_name].fillna('').str.lower().replace(clean_map, regex=True)
    
    # Remove remaining numbers and extra spaces
    df['description'] = (
        df['description']
        .str.replace(r'\d+', '', regex=True) # Remove ID numbers
        .str.replace(r'[*#_]', ' ', regex=True) # Remove common bank separators
        .str.strip() # Remove trailing spaces
    )
    return df

# -------------------------------------------------------------------
# 2. Normalise the amount sign across accounts
# -------------------------------------------------------------------
mapping_keywords_to_account = [
    {'account': 'Wealthsimple Credit Card', 'inflow': 'refund settled|payment', 'outflow': 'purchase'},
    {'account': 'Scotia Credit Card', 'inflow': 'credit', 'outflow': 'debit'}
]
                 
def normalize_amount_sign (df, inflow_pattern, outflow_pattern):
    """Normalise dollar sign """

    # Double check - Convert to numeric (float) immediately
    # errors='coerce' handles any stray '$' or ',' by turning them into NaN
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0).astype(float)
    
    # Condition 1: Purchases (Force Negative)
    is_outflow = df["transaction_label"].str.contains(outflow_pattern, case=False, na=False)

    # Condition 2: Refunds/ Payments (Force Positive)
    is_inflow = df["transaction_label"].str.contains(inflow_pattern, case=False, na=False)

    df['amount'] = np.select(
        [is_outflow, is_inflow], 
        [-df['amount'].abs(), df['amount'].abs()], 
        default=df['amount']
    ) 
    
    return df

# -------------------------------------------------------------------
# 3. Clean and transform Wealthsimple credit card
# -------------------------------------------------------------------
def clean_and_transform_ws_cc (df): 
    """
    - cast correct datatypes
    - normalise merchants name to make summarise of transactions per merchants clean and tidy
    - rename, add, keep only columns needed 
    - Apply business logic 
    Args: dataframe 
    Return: dataframe
    """   

    # -------------------------------------------------------------------------
    # 1. Cast transaction_date to datetime 
    # -------------------------------------------------------------------------
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # -------------------------------------------------------------------------
    # 2. Normalize major merchants name
    # -------------------------------------------------------------------------
    df = normalize_merchant_names(df, 'details')
    # ------------------------------------------------------------------------- 
    # 3. Rename cols and keep only columns that are needed
    # -------------------------------------------------------------------------
    df.rename(columns={'type': 'transaction_label'}, 
                        inplace=True)

    columns_to_keep = ['transaction_date', 
                       'transaction_label', 
                       'description', 
                       'amount', 
                       'currency', 
                       'source_name', 
                       'load_timestamp', 
                       'transaction_id']
    
    df = df [columns_to_keep].copy()
    # -------------------------------------------------------------------------
    # 4. Define Masks
    # -------------------------------------------------------------------------
    # Lifecyle transaction
    refund_initiated = df['transaction_label'].str.contains('refund initiated', case=False, na=False)
    
    refund_settled_processing = (df['transaction_label'].str.contains('refund settled', case=False, na=False)) & \
                                 (df['amount'] > 0)
    
    refund_settled_final = (df['transaction_label'].str.contains('refund settled', case=False, na=False)) & \
                            (df['amount'] < 0)
    
    refund_mask = refund_initiated | refund_settled_final | refund_settled_processing 

    processing_mask = refund_initiated| refund_settled_processing

    # Credit card payment
    credit_payment_mask = (df['transaction_label'].str.contains('payment', case=False, na=False)) & \
                            (df['description'].str.contains('from chequing account', case=False, na=False))

    # -------------------------------------------------------------------------
    # 5. Apply masks
    # -------------------------------------------------------------------------
    df['is_refund'] = False
    df.loc[refund_mask, 'is_refund'] = True 

    df['transaction_type'] = 'Expense'
    df.loc[credit_payment_mask, 'transaction_type'] = 'Transfer'

    df['is_final'] = True 
    df.loc[processing_mask, 'is_final'] = False

    # -------------------------------------------------------------------------
    # 6. Keep only transactions that have been processed and drop `is_final` col
    # -------------------------------------------------------------------------
    df = df.loc[df['is_final']].drop(columns=['is_final'])

    # -------------------------------------------------------------------------
    # # 7. Normalise dollar sign 
    # # -------------------------------------------------------------------------
    # df = normalize_amount_sign(df, 
    #                           inflow_pattern=mapping_keywords_to_account[0]['inflow'], 
    #                           outflow_pattern=mapping_keywords_to_account[0]['outflow'])
    # # -------------------------------------------------------------------------
    # 8. Add new columns 
    # -------------------------------------------------------------------------
    df['is_transfer'] = False
    df['is_recurring'] = False
    df['is_reimbursed'] = False
    
    return df

# -------------------------------------------------------------------
# 4. Clean and transform Scotia credit card account
# -------------------------------------------------------------------
def clean_and_transform_scotia_cc (df): 
    """
    - cast correct datatypes
    - rename, add, keep only columns needed 
    - Apply business logic
    Args: dataframe 
    Return: dataframe
    """   
    # -------------------------------------------------------------------------
    # 1. Cast date to datetime 
    # -------------------------------------------------------------------------
    df['Date'] = pd.to_datetime(df['Date'])

    # -------------------------------------------------------------------------
    # 2. Normalize major merchants name
    # -------------------------------------------------------------------------
    df = normalize_merchant_names(df, 'Description')

    # -------------------------------------------------------------------------
    # 3. Rename cols and keep only columns that are needed
    # -------------------------------------------------------------------------
    df.rename(columns={'Date': 'transaction_date', 
                        #'Description': 'description', 
                        'Amount': 'amount', 
                        'Type of Transaction': 'transaction_label'},
                        inplace=True)
    columns_to_keep = ['transaction_date', 
                       'transaction_label', 
                       'description', 
                       'amount',  
                       'source_name', 
                       'load_timestamp', 
                       'transaction_id']
    
    df = df[columns_to_keep].copy()
    
    # -------------------------------------------------------------------------
    # 4. Define masks   
    # -------------------------------------------------------------------------
    # Credit card payment mask   
    bank_name = 'rbc|royal bank of canada'
    credit_payment_mask = (df['description'].str.contains(bank_name, case=False, na=False)) & \
                    (df['transaction_label'].str.contains('credit', case=False, na=False))
    
    # Refund mask 
    refund_mask = (df['transaction_label'].str.contains('credit', case=False, na=False)) & \
                    (~df['description'].str.contains(bank_name, case=False, na= False))
    
    # Cash back mask
    cashback_mask = (df['transaction_label'].str.contains('credit', case=False, na=False)) & \
                    (df['description'].str.contains('cash back', case=False, na=False))
    
    # -------------------------------------------------------------------------
    # 5. Apply masks
    # -------------------------------------------------------------------------
    df['is_transfer'] = False
    df.loc[credit_payment_mask, 'is_transfer'] = True

    df['is_refund'] = False 
    df.loc[refund_mask, 'is_refund'] = True

    df['transaction_type'] = 'Expense' 
    df.loc[credit_payment_mask, 'transaction_type'] = 'Transfer'
    df.loc[cashback_mask, 'transaction_type'] = 'Income'

    # -------------------------------------------------------------------------
    # 6. Normalise dollar sign 
    # -------------------------------------------------------------------------
    # df = normalize_amount_sign (df, 
    #                             inflow_pattern=mapping_keywords_to_account[1]['inflow'], 
    #                             outflow_pattern=mapping_keywords_to_account[1]['outflow'])

    # -------------------------------------------------------------------------
    # 7. Add new columns
    # -------------------------------------------------------------------------
    df['currency'] = 'CAD'
    df['is_reimbursed'] = False 
    df['is_recurring'] = False 
    
    return df

# -------------------------------------------------------------------
# 5. Clean and transform Wealthsimple cheque account
# -------------------------------------------------------------------
def clean_and_transform_ws_cheque_acc (df):
    """
    - cast correct datatypes
    - rename, add, keep only columns needed 
    - Apply business logic 
    Args: dataframe  
    Return: dataframe
    """   
    # 0. Check if the DataFrame is empty or missing the 'date' column
    if df.empty or 'date' not in df.columns:
        return df  # Just return it as-is and move on

    # -----------------------------------------------------------
    # 1. Cast date to datetime 
    # -----------------------------------------------------------
    df['date'] = pd.to_datetime(df['date'])

    # -----------------------------------------------------------
    # 2. Normalize major merchants name
    # -----------------------------------------------------------
    df = normalize_merchant_names(df, 'description')
    
    # -----------------------------------------------------------
    # 3. Rename cols and keep only columns that are needed
    # -----------------------------------------------------------
    df.rename(columns={'date': 'transaction_date', 
                        'transaction': 'transaction_label'}, 
                        inplace=True)
    columns_to_keep = ['transaction_date', 
                       'transaction_label', 
                       'description', 
                       'amount', 
                       'currency', 
                       'source_name', 
                       'load_timestamp', 
                       'transaction_id']
    
    df = df[columns_to_keep].copy() 

    # -----------------------------------------------------------
    # 4. Define Masks
    # -----------------------------------------------------------
    # Reimbursement mask
    reimbursement_mask = (df['transaction_label'] =='AFT_IN') & \
                        (df['description'].str.contains('rbc insurance', case=False, na=False))
    
    # Currency exchange mask 
    money_exchange_mask = (df['transaction_label']=='AFT_IN') & \
                        (df['description'].str.contains('kbfx', case=False, na=False))
    
    # Refund mask 
    refund_mask = (df['transaction_label'] =='SPEND_REFUND')

    # Income mask
    emp_income_sources = "employer this|employer that|direct deposit from canada"
    emp_income_mask = (df['transaction_label']=='AFT_IN') & \
                    (df['description'].str.contains(emp_income_sources, case=False, na=False))

    other_income_mask = df['transaction_label'].str.contains('int|cashback|e_trfin', case=False, na=False)

    income_mask = emp_income_mask | other_income_mask | reimbursement_mask

    # Transfer between accounts mask
    transfer_mask = (df['description'].str.contains('transfer in|transfer out| etransfer out| interac| withdrawal', case=False, na=False))

    # Credit card payment mask
    credit_card_pattern = 'Online bill payment|VISA-SCOTIABANK|SCOTIALINE|VISA-TD|VISA-TORONTO DOMINION'

    credit_payment_mask = (df['transaction_label'] == 'OBP_OUT') & \
                        (df['description'].str.contains(credit_card_pattern, case=False, na=False))
    
    # Automated pre-authorised payment
    recurring_mask = (df['description'].str.contains('wre|canwise|coe edmtaxes|epcor|telus|shaw|roger|public mobile|lucky mobile',
                                                    case=False, na=False)) & \
                    (df['transaction_label'] == 'AFT_OUT') # automated transfer out
    
    # -----------------------------------------------------------
    # 5. Apply Masks
    # -----------------------------------------------------------
    df['is_refund'] = False  # Default
    df.loc[refund_mask, 'is_refund'] = True

    df['transaction_type'] = 'Expense' # Default
    df.loc[income_mask, 'transaction_type'] = 'Income'
    df.loc[money_exchange_mask, 'transaction_type'] = 'Transfer'
    df.loc[transfer_mask, 'transaction_type'] = 'Transfer'
    df.loc[credit_payment_mask, 'transaction_type'] = 'Transfer'

    df['is_reimbursed'] = False 
    df.loc[reimbursement_mask, 'is_reimbursed'] = True 

    df['is_transfer'] = False
    df.loc[money_exchange_mask, 'is_transfer'] = True 
    df.loc[transfer_mask, 'is_transfer'] = True
    df.loc[credit_payment_mask, 'is_transfer'] = True 

    df['is_recurring'] = False 
    df.loc[recurring_mask, 'is_recurring'] = True

    return df
