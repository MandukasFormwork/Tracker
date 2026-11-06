import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Mandukas Stock Loop Tracker", page_icon="🏗️", layout="wide")
st.title("🏗️ Mandukas Stock Loop Tracker")
st.markdown("### Physical Logbook Matching & Site Allocation System")

# --- INITIALIZE DATABASE ---
if "locations" not in st.session_state:
    st.session_state.locations = ["Durban Yard", "Joburg Yard", "Umhlanga Ridge Project", "Ballito Junction Site", "Sandton Mall Job"]

if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = ["Kwikstage Standards 3.0m", "Kwikstage Ledgers 2.5m", "Steel Props Size 2", "H20 Timber Beams", "Formwork Plywood Boards"]

if "transfer_ledger" not in st.session_state:
    # Seed historic entries mapping directly to physical paper sequences
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
    # Base reserve assumptions for main yards
    initial_stock = 10000 if "Yard" in location else 0
    return (initial_stock + total_in) - total_out

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Levels & Global Search", "📝 Record Paper Book Note", "⚙️ System Registries (Add Sites & Items)"])

# ==========================================
# TAB 1: LIVE SITE BALANCES & GLOBAL SEARCH
# ==========================================
with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.header("🔍 Global Equipment Locator")
        st.markdown("*Select any item below to see exactly which yards and project sites it is currently sitting at:*")
        search_item = st.selectbox("Choose Equipment to Locate:", st.session_state.inventory_items, key="search_box")
        
        # Calculate location breakdown for selected item
        item_locations = []
        for loc in st.session_state.locations:
            bal = get_site_balance(loc, search_item)
            if bal > 0:
                item_locations.append({"Location / Site": loc, "Quantity On-Site": bal})
        
        if item_locations:
            st.dataframe(pd.DataFrame(item_locations), use_container_width=True, hide_index=True)
        else:
            st.info(f"No active allocations found for {search_item} across any sites.")

    with col_right:
        st.header("📊 Individual Site Inspection")
        st.markdown("*Select a specific yard or construction job to view its full component manifest:*")
        selected_location = st.selectbox("Select Yard or Construction Site to Inspect:", st.session_state.locations)
        
        balances = []
        for item in st.session_state.inventory_items:
            current_bal = get_site_balance(selected_location, item)
            balances.append({"Equipment Item": item, "Current Balance On-Site": current_bal})
        
        st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)

    # --- ADVANCED AUDIT LOG SECTION ---
    st.markdown("---")
    st.header("📜 Paper Trail Dispute Resolver")
    st.markdown(f"Refine and audit the historical chain-of-custody log for: **{search_item}**")
    
    ledger_df = pd.DataFrame(st.session_state.transfer_ledger)
    if not ledger_df.empty:
        filtered_history = ledger_df[ledger_df["Item"] == search_item]
        
        if not filtered_history.empty:
            st.markdown("#### 🛠️ Deep-Dive Column Dropdown Filters:")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            
            with f_col1:
                unique_docs = ["Show All"] + list(filtered_history["Doc Type"].unique())
                sel_doc = st.selectbox("Filter by Doc Type:", unique_docs)
                
            with f_col2:
                unique_refs = ["Show All"] + list(filtered_history["Ref Number"].unique())
                sel_ref = st.selectbox("Filter by Ref Number:", unique_refs)
                
            with f_col3:
                unique_sites = ["Show All"] + st.session_state.locations
                sel_site = st.selectbox("Filter by Site Involved:", unique_sites)
                
            with f_col4:
                unique_managers = ["Show All"] + list(filtered_history["Driver/Manager"].unique())
                sel_manager = st.selectbox("Filter by Driver/Manager:", unique_managers)
            
            if sel_doc != "Show All":
                filtered_history = filtered_history[filtered_history["Doc Type"] == sel_doc]
                
            if sel_ref != "Show All":
                filtered_history = filtered_history[filtered_history["Ref Number"] == sel_ref]
                
            if sel_site != "Show All":
                filtered_history = filtered_history[(filtered_history["From"] == sel_site) | (filtered_history["To"] == sel_site)]
                
            if sel_manager != "Show All":
                filtered_history = filtered_history[filtered_history["Driver/Manager"] == sel_manager]
            
            st.markdown("##### Filtered Book Records Ledger Result:")
            if not filtered_history.empty:
                st.dataframe(filtered_history, use_container_width=True, hide_index=True)
            else:
                st.warning("No records match that specific combination of dropdown parameters.")
        else:
            st.info(f"No physical delivery or return notes have been recorded for '{search_item}' yet.")
    else:
        st.info("The transaction ledger is currently empty.")

# ==========================================
# TAB 2: LOGBOOK ROUTING ENGINE
# ==========================================
with tab2:
    st.header("📝 New Logbook Entry")
    st.markdown("Capture raw dispatch, return, or site-to-site movement records directly from physical tracking books.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type = st.selectbox("Select Logbook Document Type:", ["HD (Hire Delivery)", "HR (Hire Return)", "TRF (Transfer Note)"])
    with col2:
        ref_number = st.text_input("Physical Note Reference Number:", placeholder="e.g., HD-9942, HR-1105")
    with col3:
        driver_auth = st.text_input("Driver Name / Yard Manager Initial:")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        from_loc = st.selectbox("Source (From):", st.session_state.locations, key="src")
    with col5:
        dest_options = [loc for loc in st.session_state.locations if loc != from_loc]
        to_loc = st.selectbox("Destination (To):", dest_options, key="dest")
    with col6:
        selected_item = st.selectbox("Select Material Type:", st.session_state.inventory_items)

    qty = st.number_input("Count of Physical Units:", min_value=1, value=50, step=1)
    
    if st.button("Log Document Entry", type="primary"):
        if not ref_number.strip():
            st.error("Transaction rejected! You must supply a valid Reference Number from the physical logbook.")
        else:
            available_stock = get_site_balance(from_loc, selected_item)
            if "Yard" not in from_loc and qty > available_stock:
                st.error(f"Deficit Blocked! '{from_loc}' only holds {available_stock} units of {selected_item}. You cannot move {qty}.")
            else:
                new_entry = {
                    "Date & Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Doc Type": doc_type,
                    "Ref Number": ref_number.strip().upper(),
                    "From": from_loc,
                    "To": to_loc,
                    "Item": selected_item,
                    "Qty": int(qty),
                    "Driver/Manager": driver_auth.strip() if driver_auth.strip() else "System Auto"
                }
                
                st.session_state.transfer_ledger = pd.concat([
                    pd.DataFrame([new_entry]), 
                    st.session_state.transfer_ledger
                ], ignore_index=True)
                
                st.success(f"Logged Successfully: {qty} units of {selected_item} recorded via reference {ref_number.upper()}.")

    st.markdown("---")
    st.subheader("📋 Central Movement Ledger Log")
    st.dataframe(st.session_state.transfer_ledger, use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: SYSTEM REGISTRIES (LOCATIONS & STOCK ITEMS)
# ==========================================
with tab3:
    st.header("⚙️ Core Database Control Panel")
    st.markdown("Scale up your yards, project locations, and physical fleet variants instantly without entering code lines.")
    
    reg_col1, reg_col2 = st.columns(2)
    
    # Left Box: Location Controls
    with reg_col1:
        st.subheader("➕ Expand Tracking Network (Sites/Yards)")
        new_site = st.text_input("Create New Site / Yard Name:", placeholder="e.g., Umhlanga Phase 2 Job")
        if st.button("Add Location to Registry"):
