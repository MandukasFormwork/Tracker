import streamlit as st
import pandas as pd
import datetime
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Mandukas Stock Loop Tracker", page_icon="🏗️", layout="wide")
st.title("🏗️ Mandukas Stock Loop Tracker")
st.markdown("### Physical Logbook Matching & Site Allocation System")

# --- MASTER CONFIG CONSTANTS ---
OVERRIDE_PASSWORD = "ADMIN"

# --- INITIALIZE DATABASE ---
if "locations" not in st.session_state:
    st.session_state.locations = ["Durban Yard", "Joburg Yard", "Umhlanga Ridge Project", "Ballito Junction Site", "Sandton Mall Job"]

if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = ["Kwikstage Standards 3.0m", "Kwikstage Ledgers 2.5m", "Steel Props Size 2", "H20 Timber Beams", "Formwork Plywood Boards"]

if "transfer_ledger" not in st.session_state:
    st.session_state.transfer_ledger = pd.DataFrame([
        {"Date & Time": "2026-11-05 08:30", "Doc Type": "HD (Hire Delivery)", "Ref Number": "HD-9821", "From": "Durban Yard", "To": "Umhlanga Ridge Project", "Item": "Steel Props Size 2", "Qty": 450, "Driver/Manager": "A. Khumalo"},
        {"Date & Time": "2026-11-05 14:15", "Doc Type": "HR (Hire Return)", "Ref Number": "HR-4402", "From": "Sandton Mall Job", "To": "Joburg Yard", "Item": "Kwikstage Standards 3.0m", "Qty": 150, "Driver/Manager": "J. Botha"},
        {"Date & Time": "2026-11-06 10:00", "Doc Type": "TRF (Transfer Note)", "Ref Number": "TRF-0911", "From": "Umhlanga Ridge Project", "To": "Ballito Junction Site", "Item": "Steel Props Size 2", "Qty": 200, "Driver/Manager": "S. Govender"}
    ])

# --- STOCK CALCULATION LOGIC ---
def get_site_balance(location, item):
    ledger = pd.DataFrame(st.session_state.transfer_ledger)
    if ledger.empty:
        return 0
    total_in = ledger[(ledger["To"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    total_out = ledger[(ledger["From"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    initial_stock = 10000 if "Yard" in location else 0
    return (initial_stock + total_in) - total_out

# --- BULK FILE EXCEL PARSER FUNCTION ---
def process_bulk_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        matched_col = None
        for col in df.columns:
            if "description" in str(col).lower() or "item" in str(col).lower() or "product" in str(col).lower():
                matched_col = col
                break
        if matched_col:
            imported_items = df[matched_col].dropna().astype(str).str.strip().unique()
            new_additions = [x for x in imported_items if x not in st.session_state.inventory_items and x.strip() != ""]
            if len(new_additions) > 0:
                st.session_state.inventory_items.extend(new_additions)
                st.success(f"🎉 Success! Imported {len(new_additions)} brand new variants!")
            else:
                st.info("Spreadsheet parsed successfully, but all components are already present.")
        else:
            st.error("❌ Format Error! Missing description column header.")
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Levels & Global Search", "📝 Record Paper Book Note", "⚙️ System Registries & Bulk Imports"])

# ==========================================
# TAB 1: STOCK LEVELS & SPECIFIC SITE DRILL-DOWN AUDITS
# ==========================================
with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.header("🔍 Global Equipment Locator")
        search_item = st.selectbox("Choose Equipment to Locate:", st.session_state.inventory_items, key="search_box")
        item_locations = []
        for loc in st.session_state.locations:
            bal = get_site_balance(loc, search_item)
            if bal > 0:
                item_locations.append({"Location / Site": loc, "Quantity On-Site": bal})
        if item_locations:
            st.dataframe(pd.DataFrame(item_locations), use_container_width=True, hide_index=True)
        else:
            st.info(f"No active allocations found.")
            
    with col_right:
        st.header("📊 Individual Site Inspection")
        selected_location = st.selectbox("Select Yard or Site to Inspect:", st.session_state.locations)
        balances = []
        for item in st.session_state.inventory_items:
            current_bal = get_site_balance(selected_location, item)
            balances.append({"Equipment Item": item, "Current Balance On-Site": current_bal})
        st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)
        
        # LOCALIZED SITE DRILL-DOWN REPORT ZONE
        st.markdown("---")
        st.markdown(f"##### 📜 History Log for Specific Gear at **{selected_location}**")
        audit_item = st.selectbox("Select an item above to see its localized movements:", st.session_state.inventory_items, key="local_audit_box")
        ledger_df = pd.DataFrame(st.session_state.transfer_ledger)
        if not ledger_df.empty:
            local_history = ledger_df[(ledger_df["Item"] == audit_item) & ((ledger_df["From"] == selected_location) | (ledger_df["To"] == selected_location))]
            if not local_history.empty:
                st.dataframe(local_history, use_container_width=True, hide_index=True)
            else:
                st.info(f"No recorded movements for '{audit_item}' on the '{selected_location}' logs yet.")

    st.markdown("---")
    st.header("📜 Global Paper Trail Dispute Resolver")
    if not ledger_df.empty:
        filtered_history = ledger_df[ledger_df["Item"] == search_item]
        if not filtered_history.empty:
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                sel_doc = st.selectbox("Filter by Doc Type:", ["Show All"] + list(filtered_history["Doc Type"].unique()))
            with f_col2:
                sel_ref = st.selectbox("Filter by Ref Number:", ["Show All"] + list(filtered_history["Ref Number"].unique()))
            with f_col3:
                sel_site = st.selectbox("Filter by Site:", ["Show All"] + st.session_state.locations)
            with f_col4:
                sel_manager = st.selectbox("Filter by Driver/Manager:", ["Show All"] + list(filtered_history["Driver/Manager"].unique()))
            if sel_doc != "Show All":
                filtered_history = filtered_history[filtered_history["Doc Type"] == sel_doc]
            if sel_ref != "Show All":
                filtered_history = filtered_history[filtered_history["Ref Number"] == sel_ref]
            if sel_site != "Show All":
                filtered_history = filtered_history[(filtered_history["From"] == sel_site) | (filtered_history["To"] == sel_site)]
            if sel_manager != "Show All":
                filtered_history = filtered_history[filtered_history["Driver/Manager"] == sel_manager]
            st.dataframe(filtered_history, use_container_width=True, hide_index=True)

# ==========================================
# TAB 2: RECORD NOTE (VISUAL CONFIRMATION MODE)
# ==========================================
with tab2:
    st.header("📝 New Logbook Entry")
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type = st.selectbox("Select Document Type:", ["HD (Hire Delivery)", "HR (Hire Return)", "TRF (Transfer Note)"])
    with col2:
        ref_number = st.text_input("Physical Note Reference Number:")
    with col3:
        driver_auth = st.text_input("Driver Name / Manager Initial:")
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        from_loc = st.selectbox("Source (From):", st.session_state.locations, key="src")
    with col5:
        to_loc = st.selectbox("Destination (To):", [l for l in st.session_state.locations if l != from_loc], key="dest")
    with col6:
        selected_item = st.selectbox("Select Material Type:", st.session_state.inventory_items)
    qty = st.number_input("Count of Units:", min_value=1, value=50, step=1)
    
    cleaned_ref = ref_number.strip().upper()
    existing_refs = list(st.session_state.transfer_ledger["Ref Number"].unique())
    
    is_duplicate = False
    if cleaned_ref in existing_refs:
        if cleaned_ref != "":
            is_duplicate = True
            
    available_stock = get_site_balance(from_loc, selected_item)
    has_deficit = False
    if "Yard" not in from_loc:
        if qty > available_stock:
            has_deficit = True

    is_authorized = True
    if is_duplicate:
        st.error(f"❌ Transaction Blocked! Note reference number '{cleaned_ref}' has ALREADY been used and allocated in the system ledger. Moenie n dom POES wees nie!!")
        is_authorized = False
        
    if has_deficit == True:
        if is_duplicate == False:
            st.warning(f"⚠️ Deficit Warning: '{from_loc}' only holds {available_stock} units. Bypass required.")
            override_pass = st.text_input("🔒 Senior Password Override:", type="password")
            if override_pass == OVERRIDE_PASSWORD:
                st.success("✅ Bypass authorized.")
                is_authorized = True
            else:
                if override_pass != "":
                    st.error("❌ Access denied.")
                is_authorized = False

    if st.button("Log Document Entry", type="primary"):
        if not ref_number.strip():
            st.error("Missing Reference Number!")
        elif is_authorized == False:
            st.error("Submission Denied!")
        else:
            time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            manager_initial = driver_auth.strip() if driver_auth.strip() else "System Auto"
            
            # Row Construction
            new_row_data = [[time_now, doc_type, cleaned_ref, from_loc, to_loc, selected_item, int(qty), manager_initial]]
