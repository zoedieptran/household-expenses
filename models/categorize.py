#%%
# Categorize transactions using a mapping dictionary and regex patterns for better performance.
import re
import pandas as pd

mapping_transactions_dict = {
        # Housing & Property
        'wre': ('Housing', 'Rent'),
        'ttowne hoa': ('Housing', 'HOA'),
        'max insurance': ('Housing', 'Insurance'),
        'canwise': ('Housing', 'Mortgage'),
        'coe edmtaxes': ('Housing', 'Property tax'),
        'home depot': ('Housing', 'Maintenance'),
        'ikea': ('Housing', 'Furniture'),
        'taskrabbit': ('Housing', 'Maintenance'),
        'withdrawal': ('Housing', 'Down payment'),
        'landscape': ('Housing', 'Maintenance'),
        
        # Bills
        'epcor': ('Bills', 'Utilities'),
        'telus': ('Bills', 'Internet'),
        'shaw': ('Bills', 'Internet'),
        'roger': ('Bills', 'Internet'),
        'public mobile': ('Bills', 'Phone'),
        'lucky': ('Bills', 'Phone'),
        'coinamatic': ('Bills', 'Laundry'),
        'paypal  terwillegar': ('Bills', 'TCL membership'),
        'online bill payment': ('Bills', 'Credit card payment'),

        # Childcare
        'once upon a child': ('Childcare', 'Clothes') , 
        'daycare': ('Childcare', 'Daycare'), 
        'welcome ba': ('Childcare', 'Duola'),
        'brightest beginning': ('Childcare', 'Education'),
        
        
        # Food & Grocery (Typo-safe examples)
        'a mart': ('Food', 'Grocery'),
        'amart': ('Food', 'Grocery'),
        'hmart': ('Food', 'Grocery'),
        't&t supermarket': ('Food', 'Grocery'),
        'lucky supermarket': ('Food', 'Grocery'),
        'walmart': ('Food', 'Grocery'),
        'wal mart': ('Food', 'Grocery'),
        'costco': ('Food', 'Grocery'),
        'safeway': ('Food', 'Grocery'),
        'save on food': ('Food', 'Grocery'),
        'kalyna store': ('Food', 'Grocery'),
        'cobs bread': ('Food', 'Grocery'),
        'russian store': ('Food', 'Grocery'), 
        'sealand': ('Food', 'Grocery'),
        'freson bros': ('Food', 'Grocery'),
        'bulk': ('Food', 'Grocery'),
        
        # Take out
        'uber eat': ('Food', 'Take-out'),
        'doordash': ('Food', 'Take-out'),
        'skip the dishes': ('Food', 'Take-out'),

        # Dining/ Cafe
        'ghost by mediumrare': ('Food', 'Dining/Cafe'),
        'sq  kissa': ('Food', 'Dining/Cafe'),
        'whimsy bites': ('Food', 'Dining/Cafe'),
        'starbucks': ('Food', 'Dining/Cafe'),
        'tim hortons': ('Food', 'Dining/Cafe'),
        'mcdonald': ('Food', 'Dining/Cafe'),
        'pizza': ('Food', 'Dining/Cafe'), 
        'ami tea': ('Food', 'Dining/Cafe'), 
        'cafe': ('Food', 'Dining/Cafe'), 
        'pita': ('Food', 'Dining/Cafe'), 
        'che bong': ('Food', 'Dining/Cafe'), 
        'mary browns': ('Food', 'Dining/Cafe'), 
        'freshii': ('Food', 'Dining/Cafe'), 
        'deli': ('Food', 'Dining/Cafe'), 
        'tacos mexico' : ('Food', 'Dining/Cafe'), 
        'a&w' : ('Food', 'Dining/Cafe'), 
        'restaura' : ('Food', 'Dining/Cafe'), 
        'daily liquor' : ('Food', 'Dining/Cafe'),
        'pfanntastic pannenkoek ha' : ('Food', 'Dining/Cafe'),
        'made by marcus' : ('Food', 'Dining/Cafe'),
        'five guys' : ('Food', 'Dining/Cafe'), 
        'pho' : ('Food', 'Dining/Cafe'), 
        'bar' : ('Food', 'Dining/Cafe'),
        'eurest' : ('Food', 'Dining/Cafe'), 
        'snack vending': ('Food', 'Dining/Cafe'),
        'edo japan': ('Food', 'Dining/Cafe'),
        'wine & beyond': ('Food', 'Dining/Cafe'),
        'great taste chinese re' : ('Food', 'Dining/Cafe'),
        'tamarind vietnamese gr' : ('Food', 'Dining/Cafe'),

        # Transportation & Travel
        'transit': ('Transportation', 'Transit'),
        'bus': ('Transportation', 'Transit'),
        'uber': ('Transportation', 'Ride Share'),
        'lyft': ('Transportation', 'Ride Share'),
        'westjet': ('Travel', 'Flights'),
        'air canada': ('Travel', 'Flights'),
        'air bnb': ('Travel', 'Accommodation'),

        # Petcare:
        'veterinary': ('Petcare', 'Health exam'),
        'animal services': ('Petcare', 'Services'),

        # General merchandise
        'dollarama': ('Shopping', 'General'),
        'amazon': ('Shopping', 'General'),
        'amzn': ('Shopping', 'General'),
        'temu': ('Shopping', 'General'),

        'staples': ('Shopping', 'Supplies'),
        'wellca': ('Shopping', 'Supplies'),

        'shein': ('Shopping', 'Clothes'),
        'old navy': ('Shopping', 'Clothes'),
        'gap' : ('Shopping', 'Clothes'),
        'carters': ('Shopping', 'Clothes'),
        'baffin': ('Shopping', 'Clothes'),
        "marks": ('Shopping', 'Clothes'),
        'la vie en rose' : ('Shopping', 'Clothes'),

        # Healthcare:
        'dental': ('Healthcare', 'Dental'),
        'optometrist': ('Healthcare', 'Eye care'),
        'massage': ('Healthcare', 'Services'), 
        'physiotherapy': ('Healthcare', 'Services'), 
        'lifemark': ('Healthcare', 'Services'), 
        'azure wellness': ('Healthcare', 'Services'),

        'pharmacy': ('Healthcare', 'Medication'), 
        'drug': ('Healthcare', 'Medication'),
        'pharmasave': ('Healthcare', 'Medication'),

        'lifestyle brands': ('Healthcare', 'Device'),
        'drhos health': ('Healthcare', 'Device'),  
        

        # Personal
        'passport': ('Personal', 'Paperwork/ Services'),
        'visa': ('Personal', 'Paperwork/ Services'),
        'ircc': ('Personal', 'Paperwork/ Services'),
        'birth certs': ('Personal', 'Paperwork/ Services'),
        'notary': ('Personal', 'Paperwork/ Services'),
        'immigration canada': ('Personal', 'Paperwork/ Services'),
        'mojos licence & reg': ('Personal', 'Paperwork/ Services'),
        'ups store': ('Personal', 'Paperwork/ Services'),
        
        'insurance': ('Personal', 'Insurance'),
        'travel ins': ('Personal', 'Insurance'),

        'zoo': ('Personal', 'Entertainment'),
        'arts common': ('Personal', 'Entertainment'),
        'booster juice rec cent': ('Personal', 'Entertainment'),
        'muttart': ('Personal', 'Entertainment'),

        'subscr': ('Personal', 'Subscription'),
        'lk media': ('Personal', 'Subscription'),

        'adobe': ('Personal', 'Tools'),

        'lush': ('Shopping', 'Personal care'),
        'sleepout': ('Shopping', 'Personal care'),
        'tapegeeks': ('Shopping', 'Personal care'),

        'remitly': ('Personal', 'Send $ home'),

        'interac etransfer out': ('Misc', 'Misc'),

        # Transfers 
        'transfer in': ('Transfer', 'In'),
        'transfer out': ('Transfer', 'Out'),
        'direct deposit from kbfxcad' : ('Transfer', 'In'), 
        'royal bank of canada': ('Transfer', 'Credit card payment'),
        'rbc': ('Transfer', 'Credit card payment'),
        'from chequing account': ('Transfer', 'Credit card payment'),

        # Income 
        'interac etransfer received': ('Income', 'Paid back'),
        'direct deposit from northern': ('Income', 'Employment income'),
        'direct deposit from rbc insurance': ('Income', 'Insurance Reimbursement'), 
        'direct deposit from canada': ('Income', 'EI/CCE/Tax refund/Other benefits'),
        'interest earned': ('Income', 'Interest'),
        'cash back': ('Income', 'Cashback')
    }

def categorize_transactions (df, mapping_trans_dict):
    """
    Categorize transactions based on description using a regex pattern and a mapping dictionary.
    This function is optimized for performance by minimizing the number of passes through the DataFrame.
    Args:     df (pd.DataFrame): DataFrame containing a 'description' column to categorize.
     mapping_trans_dict (dict): A dictionary where keys are regex patterns to match in the description, and values are tuples of (category, subcategory).
    Returns:     pd.DataFrame: The input DataFrame with added 'category' and 'subcategory' columns based on the mapping.
    """
    # 1. Pre-clean the descriptions (Vectorized)
    df['clean_desc'] = (df['description']
                        .str.lower()
                        .replace(r'[^a-zA-Z0-9\s&]', '', regex=True)
                        .str.strip())

    # 2. Create a Regex Pattern from your keys
    # We sort keys by length (longest first) to ensure 'public mobile' matches before 'mobile'
    sorted_keywords = sorted(mapping_trans_dict.keys(), key=len, reverse=True)
    pattern = '|'.join(map(re.escape, sorted_keywords))

    # 3. Use str.extract to find the FIRST matching keyword in one pass
    # This replaces the entire 'for' loop from your previous version
    df['matched_keyword'] = df['clean_desc'].str.extract(f'({pattern})', expand=False)

    # 4. Map the matched keyword to its categories
    # This is an O(1) hash-map lookup
    # Map keywords to tuples. If no match, result is NaN.
    # We use .apply(lambda x: x if isinstance(x, tuple) else ('Uncategorized', 'Other'))
    # to ensure every single row becomes a tuple of length 2.
    results = df['matched_keyword'].map(mapping_trans_dict).apply(
        lambda x: x if isinstance(x, tuple) else ('Uncategorized', 'Other')
    )
    # results = df['matched_keyword'].map(mapping_dict)
    
    # 5. Apply results and fill defaults
    df[['category', 'subcategory']] = pd.DataFrame(results.tolist(), index=df.index)
    df['category'] = df['category'].fillna('Uncategorized')
    df['subcategory'] = df['subcategory'].fillna('Other')

    # 6. Clean up
    df = df.drop_duplicates(subset='transaction_id')
    df['year'] = df['transaction_date'].dt.year
    df['month'] = df['transaction_date'].dt.month

    cols_order = ['transaction_date', 
                    'year', 
                    'month',
                    'transaction_label', 
                    'description', 
                    'amount', 
                    'currency', 
                    'transaction_type',
                    'category',
                    'subcategory',
                    'is_transfer', 
                    'is_refund',
                    'is_reimbursed',
                    'is_recurring', 
                    'transaction_id',
                    'source_name',
                    'load_timestamp'
    ]
    df = df[cols_order]
    # return df.drop(columns=['clean_desc', 'matched_keyword'], errors='ignore') # in case these columns don't exist for some reason    
    return df 

# Call LLM API to
# 1. generate categorisation of uncategorised transactions, 
# 2. return the results as a list of dictionaries with the following format:
# [
#     {
#         "description": "SQ *GROCERY STORE 1234",
#         "category": "Groceries",
#         "source_name": "Chequing account-Monthly statement-2024-05-01.csv"
#     },
#     ...
# ]
# for me to review. 

# Update the cats and subcats
# 
# 1. Set up cat_subs map
# Extract unique categories
categories = set(cat for cat, sub in mapping_transactions_dict.values())

# Create the map using a dictionary comprehension
cat_subs_map = {
    cat: list(set(sub for c, sub in mapping_transactions_dict.values() if c == cat))
    for cat in categories
}
# print(cat_subs_map)

import os
import json
from google import genai
from pydantic import BaseModel
from typing import List

# Setup client (Free Tier Project)
api_key = "Your-API-key-here"
client = genai.Client(api_key=api_key)

def scrub_transaction(description):
    """
    Removes common personal patterns while keeping merchant data.
    """
    # 1. Remove common transaction IDs/Numbers (e.g., #1234, *9928)
    text = re.sub(r'[#\*]\d+', '', description)
    
    # 2. Remove common transfer names (like 'To Thang' or 'From Alex')
    # Use a set of names you want to protect
    sensitive_names = ["THANG", "ALEX"] 
    for name in sensitive_names:
        # This regex looks for the name even if it's surrounded by 
        # underscores, numbers, or special chars
        pattern = re.compile(rf'[^A-Z]?{name.upper()}[^A-Z]?', re.IGNORECASE)
        text = pattern.sub('[REDACTED]', text)
        
    # 3. Clean up extra spaces
    return " ".join(text.split()).strip()


class CategorizedResult(BaseModel):
    id: str
    description: str
    category: str
    subcategory: str
    reason: str

import re

# Create a "Response" wrapper
class CategorizationResponse(BaseModel):
    transactions: List[CategorizedResult]


def get_llm_suggestions(uncategorized_df):
    """Sends remaining items to Gemini for categorization suggestions."""
    if uncategorized_df.empty:
        return []

    # Prepare data for LLM
    batch = []
    for _, row in uncategorized_df.iterrows():
        batch.append({
            "id": str(row['transaction_id']), 
            "description": scrub_transaction(row['description'])
        })

    prompt = (
        "Analyze these financial transactions. Categorize them and provide a subcategory. "
        "Use logical names like 'Food', 'Shopping', 'Personal', 'Bills', etc. "
        f"Data: {json.dumps(batch)}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json", "response_schema": CategorizationResponse}
    )
    return response.parsed.transactions

def review_and_update(master_df, suggestions):
    """Step 3: User review loop."""
    print(f"\n--- Reviewing {len(suggestions)} LLM Suggestions ---")
    
    # Get sorted list of categories for the "dropdown"
    categories = sorted(cat_subs_map.keys())

    for item in suggestions:
        print(f"\n{'='*40}")
        print(f"Transaction: {item.description}")
        print(f"AI Suggested: {item.category} -> {item.subcategory}")
        print(f"Reason: {item.reason}")
        print(f"{'='*40}")
        
        # 1. Simplified choice: Only Approve or Edit
        choice = input("Action: [A]pprove or [E]dit? ").lower().strip()
        
        if choice == 'a' or choice == '':
            # Update master df with AI suggestion
            master_df.loc[master_df['transaction_id'] == item.id, ['category', 'subcategory']] = [item.category, item.subcategory]
            print("✅ Approved.")
            
        elif choice == 'e':
            # 2. Provide "Drop-down" for Category
            print("\nSelect Category:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat}")
            
            cat_idx = int(input("Enter number for Category: ")) - 1
            selected_cat = categories[cat_idx]
            
            # 3. Provide "Drop-down" for Subcategory based on Category choice
            subcategories = sorted(cat_subs_map[selected_cat])
            print(f"\nSelect Subcategory for {selected_cat}:")
            for i, sub in enumerate(subcategories, 1):
                print(f"{i}. {sub}")
                
            sub_idx = int(input("Enter number for Subcategory: ")) - 1
            selected_sub = subcategories[sub_idx]
            
            # Update master df with manual selection
            master_df.loc[master_df['transaction_id'] == item.id, ['category', 'subcategory']] = [selected_cat, selected_sub]
            print(f"✅ Updated to {selected_cat} -> {selected_sub}")
            
        else:
            print("Invalid input. Defaulting to Edit mode...")
            # (Optional: you could wrap this in a while loop to force a valid 'a' or 'e')
            
    return master_df





# %%
