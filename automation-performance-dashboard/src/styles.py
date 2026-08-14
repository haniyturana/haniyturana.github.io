def get_app_css() -> str:
    return """
    <style>
        .stApp {
            background: #f6f8fb;
            color: #0f172a;
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"] {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #102A43 !important;
        }
        section[data-testid="stSidebar"] {
            border-right: 1px solid #dbe4ee !important;
        }
        [data-testid="stSidebar"] * { color: #243B53 !important; }
        [data-testid="stSidebar"] label { color: #52667a !important; font-weight: 600; }
        [data-testid="stSidebarNav"] a { border-radius: 8px; margin-bottom: 3px; background: transparent !important; }
        [data-testid="stSidebarNav"] a[aria-current="page"] { background: #e7f3f1 !important; }
        [data-testid="stSidebarNav"] li:first-child a > * { display: none !important; }
        [data-testid="stSidebarNav"] li:first-child a { font-size: 0 !important; }
        [data-testid="stSidebarNav"] li:first-child a::after {
            content: "Executive Summary";
            font-size: 0.875rem;
            color: #243B53;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background-color: #f8fafc !important;
            border-color: #cbd5e1 !important;
            color: #102A43 !important;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        h1 {
            font-size: 2.25rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em;
            margin-bottom: 1rem !important;
        }
        h2, h3 { color: #102A43; letter-spacing: -0.02em; }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe4ee;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            min-height: 118px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMetricLabel"] { color: #52667a; font-weight: 650; }
        [data-testid="stMetricValue"] { color: #102A43; font-size: 1.65rem; }
        [data-testid="stPlotlyChart"] {
            background: white;
            border: 1px solid #dbe4ee;
            border-radius: 12px;
            padding: 0.35rem;
        }
        .kpi-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #dfe7f1;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 3px 8px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
            min-height: 140px;
        }
        .metric-label {
            font-size: 0.76rem;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        .metric-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0f172a;
            margin-top: 0.5rem;
            line-height: 1.15;
        }
        .positive {
            color: #0f766e;
        }
        .warning {
            color: #b45309;
        }
        .critical {
            color: #b91c1c;
        }
        .concept-banner {
            background: #e8f7f5;
            border-left: 5px solid #0f766e;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 1rem;
            color: #0f172a;
            font-weight: 600;
        }
        .stTabs [role="tablist"] {
            gap: 0.5rem;
        }
        .stTabs [role="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 0.5rem 1rem;
        }
    </style>
    """
