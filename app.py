# Subscriber Retention Engine: Golootlo
# One-file Streamlit dashboard. All summary data lives in one file,
# dashboard_data.xlsx, next to this file. Target Lists reads Supabase.
import io
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Subscriber Retention Engine',
                   page_icon='📈', layout='wide')

# =============================================================
# SETUP
# =============================================================
BASE = Path(__file__).parent
DATA = BASE / 'dashboard_data' if (BASE / 'dashboard_data').exists() \
    else BASE

BRAND = '#0064DC'
TEXT = '#FAFAFA'
MUTED = '#9AA0A6'
GRID = '#262A33'
BG = '#0E1117'
GREY = '#5f6b7a'
RED = '#d95926'
AMBER = '#c98500'
GREEN = '#199e70'
PKG_ORDER = ['Weekly', 'Monthly', 'Quarterly', 'Half Yearly']
PKG_COLORS = {'Weekly': '#3987e5', 'Monthly': '#d95926',
              'Quarterly': '#199e70', 'Half Yearly': '#c98500'}
MODE_COLORS = {'Auto': '#3987e5', 'Manual': '#d95926'}
PRICE = {'Weekly': 200, 'Monthly': 600, 'Quarterly': 1400,
         'Half Yearly': 2300}
PER_MONTH = {'Weekly': 4.33, 'Monthly': 1, 'Quarterly': 1 / 3,
             'Half Yearly': 1 / 6}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Unbounded:wght@700;800&family=JetBrains+Mono:wght@500;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stMetric, button, input {
  font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 1.5rem; max-width: 1300px; }
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
  display: none !important; visibility: hidden !important; }
header[data-testid="stHeader"] { background: transparent; }
div[data-testid="stMetric"] { background: #161A22;
  border: 1px solid #262A33; border-radius: 12px;
  padding: 14px 16px; border-top: 3px solid #0064DC; }
div[data-testid="stMetricLabel"] p { color: #9AA0A6;
  font-size: 0.8rem; }
.insight { background: #111827; border-left: 3px solid #0064DC;
  border-radius: 8px; padding: 12px 16px; margin: 4px 0 16px 0;
  color: #E5E7EB; font-size: 0.92rem; line-height: 1.5; }
.insight b { color: #FFFFFF; }
.caveat { color: #9AA0A6; font-size: 0.8rem; }
.card { background: #161A22; border: 1px solid #262A33;
  border-radius: 12px; padding: 16px 18px; height: 100%; }
.card h4 { margin: 0 0 4px 0; font-size: 0.95rem; color: #FAFAFA; }
.card .big { font-size: 1.9rem; font-weight: 700; color: #FAFAFA;
  line-height: 1.2; }
.card .sub { color: #9AA0A6; font-size: 0.85rem; line-height: 1.5; }
.bar { height: 10px; border-radius: 5px; background: #262A33;
  overflow: hidden; display: flex; margin: 10px 0 6px 0; }
.bar span { display: block; height: 100%; }
.reason { background: #161A22; border: 1px solid #262A33;
  border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
  display: flex; justify-content: space-between; gap: 12px;
  align-items: center; }
.reason .x { font-weight: 700; font-size: 1.05rem; white-space: nowrap; }
.pill { display: inline-block; padding: 2px 10px; border-radius: 99px;
  font-size: 0.75rem; font-weight: 600; }
button[data-baseweb="tab"] p { font-size: 0.95rem; font-weight: 600; }
.wi-title { font-family: 'Unbounded', 'Inter', sans-serif;
  font-weight: 700; font-size: 1.45rem; color: #F1F5F9; }
.wi-sub { color: #9FB3BF; font-size: 0.95rem; margin: 4px 0 12px 0;
  max-width: 560px; }
.wi-tag { display: inline-block; border: 1px solid #7a6420;
  color: #F6C343; border-radius: 99px; padding: 4px 14px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;
  letter-spacing: 0.08em; margin-bottom: 14px; }
.st-key-whatif { background: linear-gradient(160deg, #0d1c24 0%,
  #09131a 100%); border: 1px solid #1d3a44; border-radius: 22px;
  padding: 28px 30px 20px 30px; }
.st-key-whatif [data-testid="stWidgetLabel"] p { color: #B7C7D1;
  font-size: 0.95rem; }
.st-key-whatif [data-testid="stSliderThumbValue"] { color: #46E0C8;
  font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.st-key-whatif [role="radiogroup"] { gap: 8px; flex-wrap: wrap; }
.st-key-whatif button[data-variant="segmented_control"] {
  border-radius: 99px !important; border: 1px solid #25444f !important;
  background: #0f1d25 !important; padding: 8px 18px !important; }
.st-key-whatif button[data-variant="segmented_control"] p {
  color: #B7C7D1 !important; }
.st-key-whatif button[data-variant="segmented_control"][aria-checked="true"] {
  background: linear-gradient(135deg, #46E0C8, #0064DC) !important;
  border-color: transparent !important; }
.st-key-whatif button[data-variant="segmented_control"][aria-checked="true"] p {
  color: #06121a !important; font-weight: 600; }
.st-key-whatif [data-testid="stSlider"] div[style*="translate(-50%"] {
  background: #46E0C8 !important;
  box-shadow: 0 0 0 5px rgba(70,224,200,0.18); }
.wi-sentence { background: rgba(255,255,255,0.03);
  border: 1px solid #1d3a44; border-radius: 14px; padding: 14px 16px;
  color: #E6EEF2; line-height: 1.6; margin-top: 10px; }
.wi-gauge { position: relative; width: 250px; height: 250px;
  margin: 0 auto; }
.wi-center { position: absolute; inset: 0; display: flex;
  flex-direction: column; align-items: center; justify-content: center;
  text-align: center; }
.wi-big { font-family: 'Unbounded', 'Inter', sans-serif; font-weight: 800;
  font-size: 1.9rem; color: #F6C343; line-height: 1.1; }
.wi-lbl { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
  letter-spacing: 0.1em; color: #F6C343; margin-top: 6px; }
.wi-ring { color: #7fa3b3; font-size: 0.8rem; margin-top: 4px; }
.wi-bars { max-width: 360px; margin: 14px auto 0 auto; }
.wi-row { display: flex; justify-content: space-between;
  color: #B7C7D1; font-size: 0.85rem; margin-top: 8px; }
.wi-row b { color: #F1F5F9; }
.wi-track { height: 8px; background: #16252f; border-radius: 99px;
  overflow: hidden; margin-top: 4px; }
.wi-track div { height: 100%; border-radius: 99px; }
.wi-foot { color: #6f8a97; font-size: 0.78rem; margin-top: 16px; }
</style>""", unsafe_allow_html=True)


BOOK_FILE = BASE / 'dashboard_data.xlsx'


@st.cache_data
def book():
    # one sheet per table; returns None if the Excel file is not there
    if BOOK_FILE.exists():
        return pd.read_excel(BOOK_FILE, sheet_name=None)
    return None


def csv(name):
    b = book()
    stem = name.rsplit('.', 1)[0][:31]
    if b is not None and stem in b:
        return b[stem].copy()
    return pd.read_csv(DATA / name)


def js(name):
    b = book()
    stem = name.rsplit('.', 1)[0][:31]
    if b is not None and stem in b:
        return json.loads(b[stem]['json'].iloc[0])
    with open(DATA / name) as f:
        return json.load(f)


def rs(x):
    if abs(x) >= 1e6:
        return f'Rs {x / 1e6:,.1f}M'
    if abs(x) >= 1e3:
        return f'Rs {x / 1e3:,.0f}K'
    return f'Rs {x:,.0f}'


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def insight(observation, so_what, action=None):
    s = (f"<div class='insight'><b>What we see:</b> {observation}"
         f"<br><b>So what:</b> {so_what}")
    if action:
        s += f"<br><b>Action:</b> {action}"
    html(s + "</div>")


def chart_title(text, sub=None):
    s = (f"<div style='font-weight:600;font-size:0.95rem;"
         f"margin-top:8px'>{text}</div>")
    if sub:
        s += f"<div class='caveat'>{sub}</div>"
    html(s)


def style(fig, height=360, legend=True):
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', height=height,
        font=dict(family='Inter, sans-serif', color=TEXT, size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        hoverlabel=dict(font_family='Inter'), showlegend=legend,
        legend=dict(orientation='h', yanchor='bottom', y=1.0,
                    xanchor='left', x=0, title=None,
                    traceorder='normal'),
        bargap=0.35)
    fig.update_xaxes(showgrid=False, linecolor=GRID, title=None)
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False,
                     title=None, tickformat=',')
    return fig


def pct_axis(fig, axis='y'):
    if axis == 'y':
        fig.update_yaxes(tickformat='.0%', range=[0, 1.05])
    else:
        fig.update_xaxes(tickformat='.0%', range=[0, 1.05],
                         showgrid=True, gridcolor=GRID)
    return fig


def show(fig):
    st.plotly_chart(fig, width='stretch',
                    config={'displayModeBar': False})


def rate(df, by):
    g = df.groupby(by)[['labelled', 'retained']].sum()
    g['rate'] = g['retained'] / g['labelled']
    return g.reset_index()


def mode_bars(df, x, y, order, hover=''):
    fig = go.Figure()
    for md in ['Auto', 'Manual']:
        d = df[df['payment_mode'] == md].set_index(x).reindex(order)
        fig.add_bar(
            x=order, y=d[y], name=md,
            marker=dict(color=MODE_COLORS[md], cornerradius=4),
            text=d[y].map(lambda v: '' if pd.isna(v) else f'{v:.0%}'),
            textposition='outside',
            hovertemplate='%{x} · ' + md + ': %{y:.0%}' + hover
                          + '<extra></extra>')
    fig.update_layout(barmode='group')
    return fig


def payments(r, n):
    """Expected number of payments in n billing cycles when each cycle
    renews with probability r (the first payment counts)."""
    return sum(r ** k for k in range(int(n)))


CYCLES_3M = {'Weekly': 13, 'Monthly': 3, 'Quarterly': 1,
             'Half Yearly': 1}


def value_3m(pkg, r):
    return PRICE[pkg] * payments(r, CYCLES_3M[pkg])


# =============================================================
# HEADER
# =============================================================
k = js('kpis.json')
metrics = js('model_metrics.json')
END = pd.Timestamp(k['data_end'])
st.markdown('## Subscriber Retention Engine')
st.caption(f"Golootlo paid subscriptions, Jan 1 to {END:%b %d, %Y}. "
           "Partner and B2B packages excluded. Revenue is estimated at "
           "list price (Rs.79 for PKR 79, Rs.400 for promo packages). "
           "Renewal = a new subscription within 7 days of expiry.")

tabs = st.tabs(['Overview', 'Who Subscribes', 'What Subscribers Do',
                'Promotions', 'Renewal Risk', 'Revenue Simulator',
                'Target Lists'])

# =============================================================
# TAB 1: OVERVIEW
# =============================================================
with tabs[0]:
    m = csv('overview_monthly.csv')
    months = sorted(m['month'].unique())
    f1, f2, f3 = st.columns([2, 2, 1])
    rng = f1.select_slider(
        'Months', options=months, value=(months[0], months[-1]),
        format_func=lambda x: pd.Period(x).strftime('%b'), key='o_m')
    pk = f2.multiselect('Package', PKG_ORDER, default=PKG_ORDER,
                        key='o_p')
    pm = f3.selectbox('Payment', ['All', 'Auto', 'Manual'], key='o_pm')
    f = m[(m['month'] >= rng[0]) & (m['month'] <= rng[1])]
    f = f[f['package'].isin(pk)]
    if pm != 'All':
        f = f[f['payment_mode'] == pm]

    c = st.columns(5)
    c[0].metric('Paying subscribers', f"{k['subscribers']:,}")
    c[1].metric('Active on ' + END.strftime('%b %d'),
                f"{k['active_now']:,}")
    c[2].metric('Subscribed more than once',
                f"{k['recurring_share']:.0%}")
    c[3].metric('Est. revenue (filtered)', rs(f['revenue'].sum()))
    c[4].metric('Auto-pay renews', f"{k['retained_7d_auto']:.0%}",
                f"manual: {k['retained_7d_manual']:.0%}",
                delta_color='off', delta_arrow='off')

    left, right = st.columns([3, 2])
    with left:
        chart_title('Estimated revenue by month')
        rev = f.groupby(['month', 'package'])['revenue'].sum()
        rev = rev.reset_index()
        fig = go.Figure()
        for p in [x for x in PKG_ORDER if x in pk]:
            d = rev[rev['package'] == p]
            xm = pd.PeriodIndex(d['month'], freq='M').strftime('%b')
            fig.add_bar(
                x=xm, y=d['revenue'], name=p,
                marker=dict(color=PKG_COLORS[p], cornerradius=4,
                            line=dict(width=2, color=BG)),
                hovertemplate='%{x} · ' + p
                              + '<br>Rs %{y:,.0f}<extra></extra>')
        fig.update_layout(barmode='stack')
        fig = style(fig)
        fig.update_yaxes(tickprefix='Rs ', tickformat='.2s')
        show(fig)
    with right:
        chart_title('Package mix: volume vs money')
        mix = f.groupby('package').agg(
            subscriptions=('subscriptions', 'sum'),
            revenue=('revenue', 'sum'))
        mix = mix.reindex([p for p in PKG_ORDER if p in pk]).fillna(0)
        share = (mix / mix.sum()).reset_index()
        fig = go.Figure()
        fig.add_bar(
            y=share['package'], x=share['subscriptions'],
            name='Share of subscriptions', orientation='h',
            marker=dict(color=GREY, cornerradius=4),
            hovertemplate='%{y}: %{x:.0%} of subscriptions'
                          '<extra></extra>')
        fig.add_bar(
            y=share['package'], x=share['revenue'],
            name='Share of revenue', orientation='h',
            marker=dict(color=BRAND, cornerradius=4),
            hovertemplate='%{y}: %{x:.0%} of revenue<extra></extra>')
        fig.update_layout(barmode='group',
                          yaxis=dict(autorange='reversed'))
        fig = style(fig)
        fig.update_xaxes(tickformat='.0%', showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False, tickformat=None)
        show(fig)

    chart_title('Subscriptions per month: first-time vs returning')
    nm = f.groupby('month').agg(
        subscriptions=('subscriptions', 'sum'),
        new=('new_users', 'sum')).reset_index()
    nm['returning'] = nm['subscriptions'] - nm['new']
    x = pd.PeriodIndex(nm['month'], freq='M').strftime('%b')
    fig = go.Figure()
    for col, name, color in [
            ('returning', 'Returning subscribers', '#3987e5'),
            ('new', 'First-time subscribers', RED)]:
        fig.add_scatter(
            x=x, y=nm[col], name=name, mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=8, line=dict(width=2, color=BG)),
            hovertemplate='%{x}: %{y:,} ' + name.lower()
                          + '<extra></extra>')
    fig.update_layout(hovermode='x unified')
    show(style(fig, height=320))

    tot = m.groupby('package')[['subscriptions', 'revenue']].sum()
    tot = tot / tot.sum()
    cv = js('cohort_value.json')
    insight(
        f"Weekly is {tot.loc['Weekly', 'subscriptions']:.0%} of all "
        f"subscriptions and {tot.loc['Weekly', 'revenue']:.0%} of "
        "revenue. While a user stays, Weekly earns more per month "
        "(Rs 866 vs Rs 600 on Monthly).",
        "But Weekly users leave faster. Among auto users who started "
        f"in Jan to Mar, {cv['Weekly']['alive90']:.0%} of Weekly users "
        f"were still subscribed after 90 days vs "
        f"{cv['Monthly']['alive90']:.0%} on Monthly. Over 5 months a "
        f"Monthly auto user brought Rs {cv['Monthly']['rev150']:,.0f} "
        f"vs Rs {cv['Weekly']['rev150']:,.0f} for Weekly.",
        "Keep Weekly auto users where they are. Target Weekly MANUAL "
        "payers, who barely renew, with a Monthly auto-pay offer.")
    last, prev = months[-1], months[-2]
    a_, p_ = m[m['month'] == last], m[m['month'] == prev]
    insight(
        f"{pd.Period(last).strftime('%B')} subscriptions jumped to "
        f"{a_['subscriptions'].sum():,} from "
        f"{p_['subscriptions'].sum():,} in "
        f"{pd.Period(prev).strftime('%B')}, but revenue moved only "
        f"{rs(a_['revenue'].sum())} vs {rs(p_['revenue'].sum())}.",
        "PKR 79 bought volume, not revenue. Its real value shows only "
        "when those users hit the Rs.600 renewal in September.")

# =============================================================
# TAB 2: WHO SUBSCRIBES
# =============================================================
with tabs[1]:
    seg0, ret0 = csv('segments.csv'), csv('segment_retention.csv')
    city_order = (seg0[seg0['city15'] != 'Other']
                  .groupby('city15')['subscriptions'].sum()
                  .sort_values(ascending=False).index.tolist())
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    pk = f1.multiselect('Package', PKG_ORDER, default=PKG_ORDER,
                        key='w_p')
    pm = f2.selectbox('Payment', ['All', 'Auto', 'Manual'], key='w_pm')
    city = f3.selectbox('City', ['All'] + city_order + ['Other'],
                        key='w_c')
    dev = f4.selectbox('Device', ['All', 'Android', 'iOS', 'Unknown'],
                       key='w_d')

    def filt(df, use_city=True, use_dev=True):
        df = df[df['package'].isin(pk)]
        if pm != 'All':
            df = df[df['payment_mode'] == pm]
        if use_city and city != 'All':
            df = df[df['city15'] == city]
        if use_dev and dev != 'All':
            df = df[df['device'] == dev]
        return df

    seg, ret = filt(seg0), filt(ret0)
    sel = ' · '.join(x for x in [city if city != 'All' else '',
                                 dev if dev != 'All' else ''] if x)
    if sel:
        st.caption(f'Showing: {sel}')

    mode = seg.groupby('payment_mode')['subscriptions'].sum()
    rr = ret['retained'].sum() / max(ret['labelled'].sum(), 1)
    rr_all = ret0['retained'].sum() / ret0['labelled'].sum()
    pay = rate(ret, 'Transaction_Type')
    pay = pay[pay['labelled'] >= 100].sort_values('rate')
    c = st.columns(4)
    c[0].metric('Subscriptions', f"{seg['subscriptions'].sum():,}")
    c[1].metric('Paid by auto-debit',
                f"{mode.get('Auto', 0) / max(mode.sum(), 1):.0%}")
    c[2].metric('Renewal rate', f"{rr:.0%}", f"all users: {rr_all:.0%}",
                delta_color='off', delta_arrow='off')
    if len(pay):
        c[3].metric('Best-renewing method',
                    pay.iloc[-1]['Transaction_Type'],
                    f"{pay.iloc[-1]['rate']:.0%} renew",
                    delta_color='off', delta_arrow='off')

    left, right = st.columns(2)
    cs = filt(seg0, use_city=False)
    cr = filt(ret0, use_city=False)
    cities = city_order + ['Other']
    hl = [BRAND if (city in ('All', c_)) else GREY for c_ in cities]
    with left:
        chart_title('Subscriptions by city',
                    'Top 15 cities. Your selected city is highlighted.')
        tot_c = cs.groupby('city15')['subscriptions'].sum()
        tot_c = tot_c.reindex(cities).fillna(0)
        fig = go.Figure()
        fig.add_bar(
            y=cities, x=tot_c.values, orientation='h',
            marker=dict(color=hl, cornerradius=4),
            hovertemplate='%{y}: %{x:,} subscriptions<extra></extra>')
        fig.update_layout(yaxis=dict(autorange='reversed'))
        show(style(fig, height=480, legend=False))
    with right:
        chart_title('Renewal rate by city',
                    'Auto-pay users only, so payment mix does not '
                    'distort the comparison')
        ca = rate(cr[cr['payment_mode'] == 'Auto'], 'city15')
        ca = ca.set_index('city15').reindex(cities).reset_index()
        fig = go.Figure()
        fig.add_bar(
            y=ca['city15'], x=ca['rate'], orientation='h',
            marker=dict(color=hl, cornerradius=4),
            text=ca['rate'].map(
                lambda v: '' if pd.isna(v) else f'{v:.0%}'),
            textposition='outside', customdata=ca['labelled'],
            hovertemplate='%{y}: %{x:.1%} renew<br>%{customdata:,} '
                          'subscriptions measured<extra></extra>')
        fig.update_layout(yaxis=dict(autorange='reversed'))
        show(pct_axis(style(fig, height=480, legend=False), 'x'))

    pv = seg.groupby(['Transaction_Type', 'payment_mode'])[
        'subscriptions'].sum().reset_index()
    pv = pv[pv['subscriptions'] >= 30].sort_values('subscriptions')
    left, right = st.columns(2)
    with left:
        chart_title('Subscriptions by payment method')
        fig = go.Figure()
        for md in ['Auto', 'Manual']:
            d = pv[pv['payment_mode'] == md]
            fig.add_bar(
                y=d['Transaction_Type'], x=d['subscriptions'], name=md,
                orientation='h',
                marker=dict(color=MODE_COLORS[md], cornerradius=4),
                hovertemplate='%{y}: %{x:,} subscriptions'
                              '<extra></extra>')
        fig.update_layout(yaxis=dict(
            categoryorder='array',
            categoryarray=pv['Transaction_Type'].tolist()))
        show(style(fig, height=380))
    with right:
        chart_title('Renewal rate by payment method',
                    'Methods with 100+ measured subscriptions')
        modes = pv.drop_duplicates('Transaction_Type').set_index(
            'Transaction_Type')['payment_mode']
        pay['mode'] = pay['Transaction_Type'].map(modes)
        fig = go.Figure()
        for md in ['Auto', 'Manual']:
            d = pay[pay['mode'] == md]
            fig.add_bar(
                y=d['Transaction_Type'], x=d['rate'], name=md,
                orientation='h',
                marker=dict(color=MODE_COLORS[md], cornerradius=4),
                text=d['rate'].map('{:.0%}'.format),
                textposition='outside',
                hovertemplate='%{y}: %{x:.1%} renew<extra></extra>')
        fig.update_layout(yaxis=dict(
            categoryorder='array',
            categoryarray=pay['Transaction_Type'].tolist()))
        show(pct_axis(style(fig, height=380), 'x'))

    left, right = st.columns(2)
    ds = filt(seg0, use_dev=False)
    dr_ = filt(ret0, use_dev=False)
    devs = ['Android', 'iOS', 'Unknown']
    with left:
        chart_title('Subscriptions by device')
        dv = ds.groupby('device')['subscriptions'].sum().reindex(devs)
        fig = go.Figure()
        fig.add_bar(
            x=devs, y=dv.values,
            marker=dict(color=[BRAND if dev in ('All', d_) else GREY
                               for d_ in devs], cornerradius=4),
            text=[f'{v / dv.sum():.0%}' for v in dv.values],
            textposition='outside',
            hovertemplate='%{x}: %{y:,} subscriptions<extra></extra>')
        show(style(fig, height=300, legend=False))
    with right:
        chart_title('Renewal rate by device and payment type')
        drr = rate(dr_, ['device', 'payment_mode'])
        show(pct_axis(style(mode_bars(drr, 'device', 'rate', devs,
                                      hover=' renew'), height=300)))

    a = rate(ret0, 'Transaction_Type').set_index('Transaction_Type')
    a = a['rate']
    insight(
        f"How people pay decides renewal. Ufone renews {a['Ufone']:.0%}, "
        f"JazzCash Checkout {a['JazzCash Checkout']:.0%}, Easypaisa "
        f"{a['Easypaisa']:.0%}. Card renews "
        f"{a['Credit/Debit Card']:.0%} and Bill Payment "
        f"{a['Bill Payment']:.0%}.",
        "Device barely matters once payment type is known. The lever is "
        "the payment rail, not the phone.",
        "Default checkout to a wallet or carrier auto-debit.")
    big = city_order[:6]
    acr = rate(ret0[ret0['payment_mode'] == 'Auto'], 'city15')
    acr = acr.set_index('city15').reindex(big)
    ac = acr['rate'].sort_values()
    low = ', '.join(f"{c_} {v:.0%}" for c_, v in ac.head(3).items())
    high = ', '.join(f"{c_} {v:.0%}" for c_, v in ac.tail(2).items())
    insight(
        f"Among auto payers in the six biggest cities, the weakest "
        f"renewers are {low}. The strongest are {high}.",
        "A few points of renewal in a big city is thousands of "
        "subscriptions a year.",
        "Check deal coverage and wallet-balance failures in the weak "
        "cities before spending more on acquisition there.")

# =============================================================
# TAB 3: WHAT SUBSCRIBERS DO
# =============================================================
with tabs[2]:
    use0, fb0 = csv('usage_by_package.csv'), csv('first_brands.csv')
    tb0, loy0 = csv('top_brands.csv'), csv('brand_loyalty.csv')
    pk = st.multiselect('Package', PKG_ORDER, default=PKG_ORDER,
                        key='d_p')
    order = [p for p in PKG_ORDER if p in pk]
    use = use0[use0['package'].isin(pk)]
    fb, tb = fb0[fb0['package'].isin(pk)], tb0[tb0['package'].isin(pk)]
    loy = loy0[loy0['package'].isin(pk)]

    subs = use['subscriptions'].sum()
    used = (use['used_any'] * use['subscriptions']).sum()
    uses = (use['avg_uses'] * use['subscriptions']).sum()
    total_uses = use['instore_uses'].sum() + use['ecom_uses'].sum()
    kfc = tb.loc[tb['top_brand'] == 'KFC', 'uses'].sum()
    same = ((loy['same_top_brand'] * loy['renewals_compared']).sum()
            / loy['renewals_compared'].sum())
    c = st.columns(4)
    c[0].metric('Used at least once', f"{used / subs:.0%}")
    c[1].metric('Uses per subscription', f"{uses / subs:.1f}")
    c[2].metric('KFC share of uses', f"{kfc / total_uses:.0%}")
    c[3].metric('Same top brand on renewal', f"{same:.0%}")

    left, right = st.columns(2)
    with left:
        chart_title('Share of subscriptions actually used',
                    'At least one scan or redemption during the '
                    'subscription')
        show(pct_axis(style(mode_bars(use, 'package', 'used_any', order,
                                      hover=' used'), height=340)))
    with right:
        chart_title('Where they use it', 'Share of uses by vertical')
        v = use.groupby('package')[['instore_uses', 'ecom_uses',
                                    'delivery_orders']].sum()
        v = v.reindex(order)
        v = v.div(v.sum(axis=1), axis=0)
        fig = go.Figure()
        for col, name, color in [('instore_uses', 'Instore', '#3987e5'),
                                 ('ecom_uses', 'Ecom', RED),
                                 ('delivery_orders', 'Delivery', GREEN)]:
            fig.add_bar(
                y=order, x=v[col], name=name, orientation='h',
                marker=dict(color=color, line=dict(width=2, color=BG)),
                hovertemplate='%{y} · ' + name + ': %{x:.0%}'
                              '<extra></extra>')
        fig.update_layout(barmode='stack',
                          yaxis=dict(autorange='reversed'))
        show(pct_axis(style(fig, height=340), 'x'))

    left, right = st.columns(2)
    with left:
        chart_title('First brand used after subscribing',
                    'Top 10, number of subscriptions')
        f10 = (fb.groupby('first_brand')['subscriptions'].sum()
               .sort_values(ascending=False).head(10).reset_index())
        fig = go.Figure()
        fig.add_bar(
            y=f10['first_brand'], x=f10['subscriptions'],
            orientation='h', marker=dict(color=BRAND, cornerradius=4),
            hovertemplate='%{y}: first brand for %{x:,} '
                          'subscriptions<extra></extra>')
        fig.update_layout(yaxis=dict(autorange='reversed'))
        show(style(fig, height=380, legend=False))
    with right:
        chart_title('Most-used brands',
                    'Top 10, total uses by subscribers')
        t10 = (tb.groupby('top_brand')['uses'].sum()
               .sort_values(ascending=False).head(10).reset_index())
        fig = go.Figure()
        fig.add_bar(
            y=t10['top_brand'], x=t10['uses'], orientation='h',
            marker=dict(color=BRAND, cornerradius=4),
            hovertemplate='%{y}: %{x:,} uses<extra></extra>')
        fig.update_layout(yaxis=dict(autorange='reversed'))
        show(style(fig, height=380, legend=False))

    chart_title('Do renewers go back to the same brand?',
                'Share of renewals where the most-used brand matched '
                'the previous subscription')
    show(pct_axis(style(mode_bars(loy, 'package', 'same_top_brand',
                                  order, hover=' same brand'),
                        height=300)))

    u = use0.set_index(['package', 'payment_mode'])
    wa, wm = u.loc[('Weekly', 'Auto')], u.loc[('Weekly', 'Manual')]
    insight(
        f"Only {wa['used_any']:.0%} of Weekly auto-pay subscriptions "
        f"are used at all. Weekly manual payers use "
        f"{wm['used_any']:.0%} of theirs, usually within minutes of "
        "paying.",
        "Manual payers subscribe at the counter to unlock a deal. Auto "
        "payers keep paying whether or not they use it. That is "
        "inertia, and it turns into cancellations once users notice "
        "the charge.",
        "Send every new auto subscriber a 'your first deal nearby' push "
        "within 48 hours, and flag 3 unused weeks in a row for a "
        "re-engagement offer.")
    insight(
        f"KFC alone accounts for {kfc / total_uses:.0%} of subscriber "
        "uses and is the most common first brand by far.",
        "For many users the subscription is a KFC pass. KFC deal terms "
        "are a single point of failure for retention.",
        "Protect the KFC deal, and push a second brand in the first "
        "week so users build more than one habit.")

# =============================================================
# TAB 4: PROMOTIONS
# =============================================================
with tabs[3]:
    camp = csv('campaigns.csv').set_index('campaign')
    r100 = csv('campaign_return_100.csv').set_index('campaign')
    promos = ['New Year', 'Ramadan', 'Eid', 'PKR 79']
    done = ['New Year', 'Ramadan', 'Eid']
    pr, reg = camp.loc[promos], camp.loc['Regular']
    new_share = ((pr['new_to_subscription'] * pr['subscriptions']).sum()
                 / pr['subscriptions'].sum())
    dn = camp.loc[done]
    back30 = ((dn['returned_30d'] * dn['labelled_30d']).sum()
              / dn['labelled_30d'].sum())
    c = st.columns(4)
    c[0].metric('Promo subscriptions',
                f"{pr['subscriptions'].sum():,.0f}")
    c[1].metric('New to Golootlo subscriptions', f"{new_share:.0%}")
    c[2].metric('Discount given', rs(pr['discount_given'].sum()))
    c[3].metric('Came back within 30 days', f"{back30:.0%}",
                f"regular subscribers: {reg['returned_30d']:.0%}",
                delta_color='off', delta_arrow='off')

    st.markdown('#### Out of every 100 promo buyers…')
    st.caption('Did they buy another subscription within 30 days of '
               'the promo ending, and which one?')
    cols = st.columns(5)
    for col, name in zip(cols, done + ['Regular', 'PKR 79']):
        with col:
            if name == 'PKR 79':
                html("<div class='card'><h4>PKR 79</h4>"
                     "<div class='big'>Sept</div><div class='sub'>"
                     "Their first renewal is due in September. Measured "
                     "once September data is added.</div></div>")
                continue
            row = r100.loc[name]
            back = 100 - row['Did not return']
            mo, wk = row.get('Monthly', 0), row.get('Weekly', 0)
            oth = back - mo - wk
            label = 'Regular (benchmark)' if name == 'Regular' else name
            html(f"<div class='card'><h4>{label}</h4>"
                 f"<div class='big'>{back:.0f}"
                 f"<span style='font-size:1rem;color:{MUTED}'>"
                 f" / 100 came back</span></div>"
                 f"<div class='bar'>"
                 f"<span style='width:{mo}%;background:{RED}'></span>"
                 f"<span style='width:{wk}%;background:#3987e5'></span>"
                 f"<span style='width:{oth}%;background:{GREEN}'></span>"
                 f"</div><div class='sub'>"
                 f"<span style='color:{RED}'>■</span> {mo:.0f} on Monthly"
                 f"<br><span style='color:#3987e5'>■</span> {wk:.0f} on "
                 f"Weekly<br><span style='color:{GREEN}'>■</span> "
                 f"{oth:.0f} other<br>⬜ {100 - back:.0f} did not return"
                 "</div></div>")

    left, right = st.columns(2)
    with left:
        chart_title('Transactions per subscriber',
                    'Instore scans + ecom redemptions + delivery orders '
                    'during the subscription. PKR 79 is only part-way '
                    'through its month (data ends Aug 31).')
        names = promos + ['Regular']
        d = camp.loc[names]
        fig = go.Figure()
        for col, name, color in [('instore', 'Instore', '#3987e5'),
                                 ('ecom', 'Ecom', RED),
                                 ('delivery', 'Delivery', GREEN)]:
            fig.add_bar(
                x=names, y=d[col] / d['subscriptions'], name=name,
                marker=dict(color=color, line=dict(width=2, color=BG)),
                hovertemplate='%{x} · ' + name + ': %{y:.2f} per '
                              'subscriber<extra></extra>')
        per = (d['transactions'] + d['delivery']) / d['subscriptions']
        fig.add_scatter(x=names, y=per, mode='text',
                        text=[f'{v:.1f}' for v in per],
                        textposition='top center', showlegend=False,
                        hoverinfo='skip')
        fig.update_layout(barmode='stack')
        show(style(fig, height=340))
    with right:
        chart_title('Share of subscribers who used it at least once')
        fig = go.Figure()
        fig.add_bar(
            x=names, y=d['used_any'],
            marker=dict(color=[BRAND] * 4 + [GREY], cornerradius=4),
            text=d['used_any'].map('{:.0%}'.format),
            textposition='outside',
            hovertemplate='%{x}: %{y:.0%} used it<extra></extra>')
        show(pct_axis(style(fig, height=340, legend=False)))

    chart_title('Campaign economics')
    t = camp.loc[promos].reset_index()
    t['Ran'] = (pd.to_datetime(t['first_start']).dt.strftime('%b %d')
                + ' to '
                + pd.to_datetime(t['last_start']).dt.strftime('%b %d'))
    t['Discount per subscription'] = t['original_price'] - t['promo_price']
    t['Transactions'] = t['transactions'] + t['delivery']
    t['Per subscriber'] = t['Transactions'] / t['subscriptions']
    money = st.column_config.NumberColumn(format='Rs %,.0f')
    pct = st.column_config.NumberColumn(format='percent')
    num = st.column_config.NumberColumn(format='%,d')
    st.dataframe(
        t[['campaign', 'Ran', 'subscriptions', 'original_price',
           'promo_price', 'Discount per subscription', 'discount_given',
           'new_to_subscription', 'Transactions', 'Per subscriber',
           'returned_30d']].rename(columns={
               'campaign': 'Campaign', 'subscriptions': 'Subscriptions',
               'original_price': 'Original price',
               'promo_price': 'Promo price',
               'discount_given': 'Total discount',
               'new_to_subscription': 'New subscribers',
               'returned_30d': 'Back in 30 days'}),
        hide_index=True, width='stretch',
        column_config={
            'Original price': money, 'Promo price': money,
            'Discount per subscription': money, 'Total discount': money,
            'New subscribers': pct, 'Back in 30 days': pct,
            'Subscriptions': num, 'Transactions': num,
            'Per subscriber': st.column_config.NumberColumn(
                format='%.1f')})
    st.markdown("<span class='caveat'>Original price = Monthly list "
                "price (Rs 600). PKR 79 return rate appears once "
                "September data is added.</span>",
                unsafe_allow_html=True)

    insight(
        f"Promo buyers are mostly new: {new_share:.0%} had never "
        "subscribed before. They also use it heavily, about "
        f"{camp.loc['New Year', 'transactions_per_sub']:.1f} "
        "transactions each vs "
        f"{reg['transactions_per_sub']:.1f} for a regular "
        "subscription. But only "
        f"{100 - r100.loc[done, 'Did not return'].max():.0f} to "
        f"{100 - r100.loc[done, 'Did not return'].min():.0f} out of 100 "
        "come back within 30 days.",
        "Promos work as acquisition and engagement, not retention. The "
        "few who come back mostly choose Monthly.",
        "Judge promos on returning subscribers, not sign-ups. Build a "
        "day-25 push into every promo offering Monthly auto-pay.")
    insight(
        f"PKR 79 gave "
        f"Rs {camp.loc['PKR 79', 'original_price'] - 79:,.0f} off "
        f"each of {camp.loc['PKR 79', 'subscriptions']:,.0f} "
        f"subscriptions: {rs(camp.loc['PKR 79', 'discount_given'])} in "
        "total.",
        "If PKR 79 buyers return like earlier promos (17 to 26 in 100), "
        "each returning subscriber will have cost roughly Rs 2,000 to "
        "Rs 3,000 in discount.",
        "Use September data to confirm the return rate before repeating "
        "a price this low.")

# =============================================================
# TAB 5: RENEWAL RISK
# =============================================================
with tabs[4]:
    drv = csv('renewal_drivers.csv')
    par = csv('usage_paradox.csv')
    rsk = csv('risk_summary.csv')

    st.markdown('#### 1. Can we predict who will leave?')
    top20 = metrics['lapse_in_top20_model']
    base_ = metrics['test_lapse_rate']
    left, right = st.columns([2, 3])
    with left:
        html(f"<div class='card'><div class='big'>"
             f"{top20 * 100:.0f} out of 100</div><div class='sub'>"
             "people the model flags as most at risk actually left "
             f"(tested on June to August).<br><br>Picking people at "
             f"random catches only <b>{base_ * 100:.0f} out of 100</b>. "
             "So the model finds leavers about "
             f"<b>{top20 / base_:.1f}x</b> better than guessing. "
             "Useful, not perfect.</div></div>")
    with right:
        fig = go.Figure()
        lbl = ['Random pick', 'Simple rule<br>(payment + package)',
               'Our model<br>(top 20% risk)']
        vals = [base_, metrics['lapse_in_top20_baseline'], top20]
        fig.add_bar(
            x=lbl, y=vals, marker=dict(color=[GREY, GREY, BRAND],
                                       cornerradius=4),
            text=[f'{v * 100:.0f} in 100' for v in vals],
            textposition='outside',
            hovertemplate='%{x}: %{y:.0%} actually left<extra></extra>')
        fig = style(fig, height=260, legend=False)
        fig.update_yaxes(tickformat='.0%', range=[0, 0.7])
        show(fig)

    st.markdown('#### 2. What makes people leave or stay')
    st.caption('Auto-pay subscribers. "3x" means three times as likely, '
               'compared with a typical first-time Easypaisa Weekly '
               'subscriber.')
    names = {
        'Bought a promo package (New Year/Eid/Ramadan)':
            'Bought a promo package',
        'History: Lapsed before': 'Stopped once before',
        'Used an Ecom deal in first 5 days':
            'First used an online (ecom) deal',
        'Pays via Zong': 'Pays with Zong',
        'Number of past cycles (log)':
            'Has renewed many times before',
        'Pays via Ufone': 'Pays with Ufone',
        'Pays via JazzCash Checkout': 'Pays with JazzCash Checkout',
        'Package: Long term': 'On a Quarterly or Half Yearly package',
        'Package: Monthly': 'On a Monthly package',
        'Used the subscription in first 5 days':
            'Used it in the first 5 days',
    }
    d = drv[drv['driver'].isin(names) & (drv['p_value'] < 0.05)].copy()
    d['label'] = d['driver'].map(names)
    leave = d[d['odds_ratio'] < 1].sort_values('odds_ratio').head(5)
    stay = d[d['odds_ratio'] > 1].sort_values(
        'odds_ratio', ascending=False).head(5)
    left, right = st.columns(2)
    with left:
        html(f"<div style='color:{RED};font-weight:600;margin-bottom:8px'>"
             "⬇ More likely to LEAVE</div>")
        for _, r in leave.iterrows():
            html(f"<div class='reason'><span>{r['label']}</span>"
                 f"<span class='x' style='color:{RED}'>"
                 f"{1 / r['odds_ratio']:.1f}x</span></div>")
    with right:
        html(f"<div style='color:{GREEN};font-weight:600;"
             "margin-bottom:8px'>⬆ More likely to STAY</div>")
        for _, r in stay.iterrows():
            html(f"<div class='reason'><span>{r['label']}</span>"
                 f"<span class='x' style='color:{GREEN}'>"
                 f"{r['odds_ratio']:.1f}x</span></div>")

    p = par.set_index(['history', 'used_early'])['retained']
    insight(
        "Auto payers who renewed last time and did NOT use the app "
        f"renewed {p[('Renewed last time', 0)]:.0%} of the time. Those "
        f"who used it renewed {p[('Renewed last time', 1)]:.0%}.",
        "Some of the most 'loyal' auto payers are simply not paying "
        "attention. Their renewals are inertia, which is fragile.",
        "Treat passive auto payers as a hidden risk, not a win.")

    st.markdown(f'#### 3. Who is at risk right now ({END:%b %d})')
    band = rsk.groupby('risk_band').agg(
        subscribers=('subscribers', 'sum'),
        value=('revenue_at_stake', 'sum'),
        risk=('avg_lapse_risk', 'mean'))
    wavg = rsk.assign(w=rsk['avg_lapse_risk'] * rsk['subscribers'])
    wavg = wavg.groupby('risk_band')['w'].sum() / band['subscribers']
    info = {'High': (RED, 'Most will leave', 'Act now'),
            'Medium': (AMBER, 'Could go either way', 'Nudge'),
            'Low': (GREEN, 'Likely to stay', 'Leave alone')}
    cols = st.columns(3)
    for col, b in zip(cols, ['High', 'Medium', 'Low']):
        color, meaning, todo = info[b]
        with col:
            html(f"<div class='card' style='border-top:3px solid "
                 f"{color}'><span class='pill' style='background:{color}'>"
                 f"{b} risk</span><div class='big' style='margin-top:8px'>"
                 f"{band.loc[b, 'subscribers']:,.0f}</div>"
                 f"<div class='sub'>subscribers · "
                 f"{rs(band.loc[b, 'value'])} current value<br>"
                 f"About {wavg[b] * 10:.0f} in 10 expected to leave. "
                 f"<b>{meaning}.</b> {todo}.</div></div>")


# =============================================================
# TAB 6: REVENUE SIMULATOR
# =============================================================
with tabs[5]:
    sim = csv('simulator_inputs.csv').set_index('package').reindex(
        PKG_ORDER)
    pas = csv('passive_auto_payers.csv')
    p79 = js('pkr79.json')
    ra, rm = sim['retention_Auto'], sim['retention_Manual']
    new_man = sim['new_per_month_Manual']
    reg_p = pas[pas['campaign'] == 'Regular'].set_index(
        'package').reindex(PKG_ORDER).fillna(0)
    passive_month = sum(reg_p.loc[p, 'passive_payers'] * PRICE[p]
                        * PER_MONTH[p] for p in PKG_ORDER)

    def lever_a(conv, real):
        """Weekly manual payers moved to Monthly auto-pay."""
        n = new_man['Weekly'] * 3 * conv
        r_new = rm['Monthly'] + (ra['Monthly'] - rm['Monthly']) * real
        gain = value_3m('Monthly', r_new) - value_3m('Weekly',
                                                     rm['Weekly'])
        return n, n * gain / 2

    def lever_b(conv, real, pkgs=PKG_ORDER):
        """Manual payers moved to auto-pay on the same package."""
        tot_n, tot_v = 0, 0
        for p in pkgs:
            n = new_man[p] * 3 * conv
            r_new = rm[p] + (ra[p] - rm[p]) * real
            gain = value_3m(p, r_new) - value_3m(p, rm[p])
            tot_n += n
            tot_v += n * gain / 2
        return tot_n, tot_v

    def lever_c(cancel, save):
        at_risk = passive_month * 3 * cancel
        return at_risk, at_risk * save

    def lever_d(renew):
        n = (p79['auto'] + p79['manual']) * renew
        return n, n * value_3m('Monthly', ra['Monthly'])

    with st.container(key='whatif'):
        html("<div class='wi-title'>Revenue what-if calculator</div>"
             "<div class='wi-sub'>Pick a move, drag the sliders and watch "
             "the 3-month revenue change.</div>"
             "<span class='wi-tag'>3-MONTH ESTIMATE</span>")
        MOVES = {'Weekly manual → Monthly auto': 'a',
                 'Manual → auto (same package)': 'b',
                 'Wake up passive auto payers': 'c',
                 'PKR 79 renewals at Rs 600': 'd'}
        lever = st.segmented_control(
            'Pick a move', list(MOVES), default=list(MOVES)[0],
            key='s_lever', label_visibility='collapsed') or list(MOVES)[0]
        mv = MOVES[lever]
        left, right = st.columns([1.15, 1], gap='large')
        with left:
            if mv == 'a':
                ring = st.slider('Weekly manual payers who accept (%)',
                                 0, 100, 20, 5, key='s_a') / 100
                real = st.slider(
                    'Share of the auto-pay renewal boost they get (%)',
                    0, 100, 50, 10, key='s_ar',
                    help='Auto-pay users are partly more committed to '
                         'begin with, so a switched user may not renew '
                         'as often. 50% is a cautious middle.') / 100
                n, v = lever_a(ring, real)
                before = new_man['Weekly'] * 3 * ring * value_3m(
                    'Weekly', rm['Weekly']) / 2
                sentence = (f"Moving <b>{ring:.0%}</b> of Weekly manual "
                            f"payers (about <b>{n:,.0f}</b> people over 3 "
                            f"months) to Monthly auto-pay adds about "
                            f"<b>{rs(v)}</b>.")
                bars = [('Their revenue today', before, GREY),
                        ('After the switch', before + v, BRAND)]
                big_lbl, ring_lbl = 'EXTRA IN 3 MONTHS', 'switched'
            elif mv == 'b':
                ring = st.slider('Manual payers who switch to auto-pay (%)',
                                 0, 100, 20, 5, key='s_b') / 100
                real = st.slider(
                    'Share of the auto-pay renewal boost they get (%)',
                    0, 100, 50, 10, key='s_br') / 100
                n, v = lever_b(ring, real)
                before = sum(new_man[p] * 3 * ring * value_3m(p, rm[p])
                             for p in PKG_ORDER) / 2
                sentence = (f"Switching <b>{ring:.0%}</b> of manual payers "
                            f"(about <b>{n:,.0f}</b> people over 3 months) "
                            f"to auto-pay adds about <b>{rs(v)}</b>.")
                bars = [('Their revenue today', before, GREY),
                        ('After the switch', before + v, BRAND)]
                big_lbl, ring_lbl = 'EXTRA IN 3 MONTHS', 'switched'
            elif mv == 'c':
                cancel = st.slider('Passive payers who would cancel once '
                                   'they notice (%)', 0, 100, 25, 5,
                                   key='s_c') / 100
                ring = st.slider('Of those, kept by an activation push (%)',
                                 0, 100, 35, 5, key='s_cs') / 100
                at_risk, v = lever_c(cancel, ring)
                n = reg_p['passive_payers'].sum()
                sentence = (f"<b>{n:,.0f}</b> auto payers haven't used "
                            f"their current subscription. If "
                            f"<b>{cancel:.0%}</b> cancel, <b>{rs(at_risk)}"
                            f"</b> is lost over 3 months. An activation "
                            f"push keeping <b>{ring:.0%}</b> of them "
                            f"protects <b>{rs(v)}</b>.")
                bars = [('Lost if nothing is done', at_risk, RED),
                        ('Protected by the push', v, GREEN)]
                big_lbl, ring_lbl = 'PROTECTED IN 3 MONTHS', 'kept'
            else:
                ring = st.slider('PKR 79 buyers who renew at Rs 600 (%)',
                                 0, 100, 25, 5, key='s_d') / 100
                n, v = lever_d(ring)
                sentence = (f"If <b>{ring:.0%}</b> of the "
                            f"{p79['auto'] + p79['manual']:,} PKR 79 "
                            f"buyers renew at Rs 600, that is <b>{n:,.0f}"
                            f"</b> subscribers worth about <b>{rs(v)}</b> "
                            f"over 3 months. {p79['used_any']:.0%} of them "
                            "have used the subscription so far.")
                bars = [('Revenue from renewals', v, BRAND)]
                big_lbl, ring_lbl = 'FROM RENEWALS', 'renew'
            html(f"<div class='wi-sentence'>{sentence}</div>")

        with right:
            circ = 2 * 3.14159 * 92
            arc = max(ring, 0.001) * circ
            top = max(b_[1] for b_ in bars) or 1
            rows = ''.join(
                f"<div class='wi-row'><span>{lb}</span><b>{rs(val)}</b>"
                f"</div><div class='wi-track'><div style='width:"
                f"{val / top * 100:.1f}%;background:{col}'></div></div>"
                for lb, val, col in bars)
            html(f"""
<div class='wi-gauge'>
 <svg viewBox='0 0 220 220' width='250' height='250'>
  <defs><linearGradient id='wig' x1='0' y1='0' x2='1' y2='1'>
   <stop offset='0' stop-color='#0064DC'/>
   <stop offset='1' stop-color='#46E0C8'/></linearGradient></defs>
  <circle cx='110' cy='110' r='92' fill='none' stroke='#16252f'
   stroke-width='16'/>
  <circle cx='110' cy='110' r='92' fill='none' stroke='url(#wig)'
   stroke-width='16' stroke-linecap='round'
   stroke-dasharray='{arc:.1f} {circ:.1f}'
   transform='rotate(-90 110 110)'/>
 </svg>
 <div class='wi-center'>
  <div class='wi-big'>{rs(v).replace('Rs ', 'Rs&nbsp;')}</div>
  <div class='wi-lbl'>{big_lbl}</div>
  <div class='wi-ring'>{ring:.0%} {ring_lbl}</div>
 </div>
</div>
<div class='wi-bars'>{rows}</div>""")
        html("<div class='wi-foot'>3-month value = expected payments over "
             "the next 3 months, using each package's renewal rate. People "
             "switched part-way through the period are counted for half "
             "the time on average.</div>")

# =============================================================
# TAB 7: TARGET LISTS (password protected, reads Supabase)
# =============================================================
with tabs[6]:
    st.markdown('#### Target lists and customer search')
    st.caption('Active subscribers with name, phone and lapse risk. '
               'Password protected.')

    if 'APP_PASSWORD' not in st.secrets or 'DB_URL' not in st.secrets:
        st.warning('This tab needs two secrets. In Streamlit Cloud: '
                   'your app → ⋮ → Settings → Secrets, then paste:')
        st.code('DB_URL = "postgresql+psycopg2://postgres.PROJECT:'
                'PASSWORD@HOST:6543/postgres"\n'
                'APP_PASSWORD = "your-dashboard-password"', 'toml')
        st.stop()

    pw = st.text_input('Password', type='password', key='t_pw')
    if pw != st.secrets['APP_PASSWORD']:
        if pw:
            st.error('Wrong password.')
        st.stop()

    @st.cache_data(ttl=3600, show_spinner='Loading list...')
    def load_list():
        from sqlalchemy import create_engine
        eng = create_engine(st.secrets['DB_URL'])
        return pd.read_sql('select * from retention_risk_list', eng)

    try:
        rl = load_list()
    except Exception as e:
        st.error('Could not reach Supabase. If the project is paused, '
                 'open it in Supabase and click Restore. '
                 f'({str(e)[:150]})')
        st.stop()

    ph = rl['phone'].astype(str).str.replace(r'\.0$', '', regex=True)
    rl['phone'] = '0' + ph.str.replace(r'\D', '', regex=True).str.lstrip(
        '0')
    COLS = {'User_ID': 'User ID', 'User_Name': 'Name', 'phone': 'Phone',
            'Subscription_Package': 'Package', 'campaign': 'Campaign',
            'payment_mode': 'Payment', 'Transaction_Type': 'Method',
            'city': 'City', 'end': 'Expires', 'days_to_expiry':
            'Days to expiry', 'lapse_risk': 'Lapse risk',
            'risk_band': 'Risk', 'reasons': 'Why',
            'recommended_action': 'Action'}
    view = rl[list(COLS)].rename(columns=COLS)
    view['Expires'] = pd.to_datetime(view['Expires']).dt.strftime(
        '%b %d, %Y')
    risk_col = st.column_config.ProgressColumn(
        'Lapse risk', format='percent', min_value=0, max_value=1)

    def downloads(df, name):
        c1, c2, _ = st.columns([1, 1, 3])
        c1.download_button(
            '⬇ Download CSV', df.to_csv(index=False).encode('utf-8'),
            file_name=f'{name}.csv', mime='text/csv', type='primary',
            key=f'csv_{name}')
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as xw:
            df.to_excel(xw, index=False, sheet_name='Target list')
        c2.download_button(
            '⬇ Download Excel', buf.getvalue(),
            file_name=f'{name}.xlsx', key=f'xlsx_{name}',
            mime='application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.sheet')

    part = st.radio('What do you want to do?', horizontal=True,
                    key='t_part',
                    options=['🔍 Search a customer', '📋 Build a list'])

    if part == '🔍 Search a customer':
        q = st.text_input('Type a name, phone number or user ID',
                          key='t_q', placeholder='e.g. 03001234567')
        if q:
            ql = q.strip().lower()
            qd = ql.lstrip('0').replace('-', '').replace(' ', '')
            hit = (view['Name'].astype(str).str.lower().str.contains(
                       ql, regex=False)
                   | view['Phone'].str.contains(qd, regex=False)
                   | view['User ID'].astype(str).str.contains(
                       qd, regex=False))
            res = view[hit]
            st.caption(f'{len(res):,} match(es)')
            if len(res) == 1:
                r = res.iloc[0]
                color = {'High': RED, 'Medium': AMBER,
                         'Low': GREEN}.get(r['Risk'], GREY)
                html(f"<div class='card' style='border-top:3px solid "
                     f"{color}'><h4>{r['Name']} · {r['Phone']}</h4>"
                     f"<span class='pill' style='background:{color}'>"
                     f"{r['Risk']} risk · {r['Lapse risk']:.0%}</span>"
                     f"<div class='sub' style='margin-top:10px'>"
                     f"{r['Package']} ({r['Campaign']}) · {r['Payment']} "
                     f"via {r['Method']} · {r['City']}<br>Expires "
                     f"{r['Expires']} ({r['Days to expiry']:.0f} days)"
                     f"<br><b>Why:</b> {r['Why']}<br><b>Do this:</b> "
                     f"{r['Action']}</div></div>")
            st.dataframe(res, hide_index=True, width='stretch',
                         column_config={'Lapse risk': risk_col})
            if len(res):
                downloads(res, 'customer_search')
        else:
            st.caption('Only active subscribers (live subscription on '
                       f'{END:%b %d}) are searchable.')
    else:
        f1, f2, f3, f4 = st.columns(4)
        bands = f1.multiselect('Risk', ['High', 'Medium', 'Low'],
                               default=['High'], key='t_b')
        modes = f2.multiselect('Payment', ['Auto', 'Manual'],
                               default=['Auto', 'Manual'], key='t_m')
        camps = f3.multiselect(
            'Campaign', sorted(view['Campaign'].unique()),
            default=sorted(view['Campaign'].unique()), key='t_c')
        maxd = int(view['Days to expiry'].max())
        days = f4.slider('Expires within (days)', 0, maxd, 7, key='t_d')
        f5, f6, f7 = st.columns([2, 1, 1])
        acts = f5.multiselect(
            'Action', sorted(view['Action'].unique()),
            default=sorted(view['Action'].unique()), key='t_a')
        pkgs = f6.multiselect(
            'Package', sorted(view['Package'].unique()),
            default=sorted(view['Package'].unique()), key='t_p')
        top_c = view['City'].value_counts().head(15).index.tolist()
        cty = f7.selectbox('City', ['All'] + top_c, key='t_city')

        out = view[view['Risk'].isin(bands)
                   & view['Payment'].isin(modes)
                   & view['Campaign'].isin(camps)
                   & (view['Days to expiry'] <= days)
                   & view['Action'].isin(acts)
                   & view['Package'].isin(pkgs)]
        if cty != 'All':
            out = out[out['City'] == cty]
        out = out.sort_values(['Days to expiry', 'Lapse risk'],
                              ascending=[True, False])
        c = st.columns(3)
        c[0].metric('People in this list', f"{len(out):,}")
        c[1].metric('Average lapse risk',
                    f"{out['Lapse risk'].mean():.0%}" if len(out)
                    else '-')
        c[2].metric('Expiring in the next 3 days',
                    f"{(out['Days to expiry'] <= 3).sum():,}")
        st.dataframe(out, hide_index=True, width='stretch', height=420,
                     column_config={'Lapse risk': risk_col})
        downloads(out, f'target_list_{END:%Y%m%d}')
