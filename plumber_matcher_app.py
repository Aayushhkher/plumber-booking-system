import streamlit as st
import pandas as pd

# Load dataset
df = pd.read_csv('gujarat_plumbers_dataset.csv')

st.title('Gujarat Plumber Finder')

st.write('Enter your requirements to find the best available plumbers near you!')

# User inputs
location = st.selectbox('Select your district/location:', sorted(df['District'].unique()))
work_type = st.selectbox('Type of work needed:', sorted(df['Work_Specialization'].unique()))
time_slot = st.selectbox('Preferred time slot:', sorted(set(
    slot.strip() for slots in df['Free_Time_Slots'] for slot in str(slots).split(',')
)))
language = st.selectbox('Preferred language (optional):', ['Any'] + sorted(set(
    lang.strip() for langs in df['Languages_Spoken'] for lang in str(langs).split(',')
)))

if st.button('Find Plumbers'):
    # Filter by location
    filtered = df[df['District'] == location]
    # Filter by work type
    filtered = filtered[filtered['Work_Specialization'] == work_type]
    # Filter by time slot
    filtered = filtered[filtered['Free_Time_Slots'].str.contains(time_slot)]
    # Filter by language if not 'Any'
    if language != 'Any':
        filtered = filtered[filtered['Languages_Spoken'].str.contains(language)]
    # Sort by distance
    filtered = filtered.sort_values('Distance_from_Client_km')
    if not filtered.empty:
        st.success(f"Found {len(filtered)} plumber(s) matching your criteria:")
        st.dataframe(filtered[['Name', 'District', 'Work_Specialization', 'Free_Time_Slots', 'Languages_Spoken', 'Distance_from_Client_km']].reset_index(drop=True))
    else:
        st.warning('No plumbers found matching all your criteria. Try changing your filters!') 