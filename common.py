import json
from pathlib import Path
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / 'dashboard_data'

BRAND = '#0064DC'
SURFACE = '#0E1117'
TEXT = '#FAFAFA'
MUTED = '#9AA0A6'
GRID = '#262A33'
# validated dark-mode categorical order (colorblind-safe for adjacent series)
PKG_COLORS = {'Weekly': '#3987e5', 'Monthly': '#d95926', 'Quarterly': '#199e70', 'Half Yearly': '#c98500'}
PKG_ORDER = ['Weekly', 'Monthly', 'Quarterly', 'Half Yearly']
MODE_COLORS = {'Auto': '#3987e5', 'Manual': '#d95926'}


def setup(title):
    st.set_page_config(page_title=f'{title} | Subscriber Retention Engine', page_icon='📈', layout='wide')
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown, .stMetric, button, input { font-family: 'Inter', sans-serif !important; }
    .block-container { padding-top: 2rem; max-width: 1300px; }
    div[data-testid="stMetric"] { background: #161A22; border: 1px solid #262A33; border-radius: 12px;
        padding: 14px 16px; border-top: 3px solid #0064DC; }
    div[data-testid="stMetricLabel"] p { color: #9AA0A6; font-size: 0.8rem; }
    .insight { background: #111827; border-left: 3px solid #0064DC; border-radius: 8px; padding: 12px 16px;
        margin: 4px 0 16px 0; color: #E5E7EB; font-size: 0.92rem; line-height: 1.5; }
    .insight b { color: #FFFFFF; }
    .caveat { color: #9AA0A6; font-size: 0.8rem; }
    </style>""", unsafe_allow_html=True)
    st.markdown(f"## {title}")


def insight(observation, so_what, action=None):
    html = f"<div class='insight'><b>What we see:</b> {observation}<br><b>So what:</b> {so_what}"
    if action:
        html += f"<br><b>Action:</b> {action}"
    st.markdown(html + "</div>", unsafe_allow_html=True)


def style(fig, height=360, legend=True):
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=TEXT, size=12), height=height,
        margin=dict(l=10, r=10, t=30, b=10), hoverlabel=dict(font_family='Inter'),
        legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='left', x=0, title=None, traceorder='normal') if legend else None,
        showlegend=legend, bargap=0.35)
    fig.update_xaxes(showgrid=False, linecolor=GRID, title=None)
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False, title=None, tickformat=',')
    return fig


@st.cache_data
def csv(name):
    return pd.read_csv(DATA / name)


@st.cache_data
def js(name):
    with open(DATA / name) as f:
        return json.load(f)


def chart_title(text, sub=None):
    st.markdown(f"<div style='font-weight:600;font-size:0.95rem;margin-top:8px'>{text}</div>"
                + (f"<div class='caveat'>{sub}</div>" if sub else ''), unsafe_allow_html=True)


def rs(x):
    if abs(x) >= 1e6:
        return f'Rs {x / 1e6:,.1f}M'
    if abs(x) >= 1e3:
        return f'Rs {x / 1e3:,.0f}K'
    return f'Rs {x:,.0f}'
