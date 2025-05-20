# NOTE: DEV App configuration & constants

import plotly.express as px

# General

DEV = False

# Data

CQ_DATA_DIR_PATH_DEV = './Web/data/'
CQ_DATA_DIR_PATH = './Data/PROD/'
CQ_DATA_FILE_PATH = 'CQ_DATA_PROD_2_ENHANCED.csv'

# Mappings

PERIOD_BACKEND_MAPPING = {
    'Ukraine War 2022' : 'UA',
    'COVID-19 Pandemic' : 'COVID',
    'European Sovereign Debt Crisis (ESDC)' : 'ESDC',
    'Great Financial Crisis 2008 (GFC)' : 'GFC'
}

PHASE_BACKEND_MAPPING = {
    'Full period' : "full_period",
    'Phase I' : 'phase_I',
    'Phase II' : 'phase_II',
    'Phase III' : 'phase_III'
}

CMAP_BACKEND_MAPPING = {
    'Coolwarm' : 'RdBu'
}


CMAPS = px.colors.named_colorscales()

