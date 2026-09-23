import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import setup, insight, style, csv, js, rs, chart_title, PKG_COLORS, PKG_ORDER, BRAND

setup('Overview')
k = js('kpis.json')
st.caption(f"Paid subscriptions, Jan 1 to {pd.Timestamp(k['data_end']):%b %d, %Y}. Partner and B2B packages excluded. "
           "Revenue is estimated at list price (Rs.79 for PKR 79, Rs.400 for promo packages).")

m = csv('overview_monthly.csv')
months = sorted(m['month'].unique())

# ---------- filters (one row) ----------
f1, f2, f3 = st.columns([2, 2, 1])
rng = f1.select_slider('Months', options=months, value=(months[0], months[-1]),
                       format_func=lambda x: pd.Period(x).strftime('%b'))
pk = f2.multiselect('Package', PKG_ORDER, default=PKG_ORDER)
pm = f3.selectbox('Payment', ['All', 'Auto', 'Manual'])
f = m[(m['month'] >= rng[0]) & (m['month'] <= rng[1]) & m['package'].isin(pk)]
if pm != 'All':
    f = f[f['payment_mode'] == pm]

# ---------- KPIs ----------
c = st.columns(5)
c[0].metric('Paying subscribers (all time)', f"{k['subscribers']:,}")
c[1].metric('Active on ' + pd.Timestamp(k['data_end']).strftime('%b %d'), f"{k['active_now']:,}")
c[2].metric('Subscribed more than once', f"{k['recurring_share']:.0%}")
c[3].metric('Est. revenue (filtered)', rs(f['revenue'].sum()))
c[4].metric('Auto-pay renews in 7 days', f"{k['retained_7d_auto']:.0%}", f"manual: {k['retained_7d_manual']:.0%}",
            delta_color='off', delta_arrow='off')

# ---------- revenue by month ----------
left, right = st.columns([3, 2])
with left:
    rev = f.groupby(['month', 'package'])['revenue'].sum().reset_index()
    fig = go.Figure()
    for p in [x for x in PKG_ORDER if x in pk]:
        d = rev[rev['package'] == p]
        fig.add_bar(x=pd.PeriodIndex(d['month'], freq='M').strftime('%b'), y=d['revenue'], name=p,
                    marker=dict(color=PKG_COLORS[p], cornerradius=4, line=dict(width=2, color='#0E1117')),
                    hovertemplate='%{x} · ' + p + '<br>Rs %{y:,.0f}<extra></extra>')
    fig.update_layout(barmode='stack')
    chart_title('Estimated revenue by month')
    fig = style(fig)
    fig.update_yaxes(tickprefix='Rs ', tickformat='.2s')
    st.plotly_chart(fig, width='stretch')

with right:
    mix = f.groupby('package').agg(subscriptions=('subscriptions', 'sum'), revenue=('revenue', 'sum')).reindex(
        [p for p in PKG_ORDER if p in pk]).fillna(0)
    share = (mix / mix.sum()).reset_index()
    fig = go.Figure()
    fig.add_bar(y=share['package'], x=share['subscriptions'], name='Share of subscriptions', orientation='h',
                marker=dict(color='#5f6b7a', cornerradius=4), hovertemplate='%{y}: %{x:.0%} of subscriptions<extra></extra>')
    fig.add_bar(y=share['package'], x=share['revenue'], name='Share of revenue', orientation='h',
                marker=dict(color=BRAND, cornerradius=4), hovertemplate='%{y}: %{x:.0%} of revenue<extra></extra>')
    fig.update_layout(barmode='group', yaxis=dict(autorange='reversed'))
    chart_title('Package mix: volume vs money')
    fig = style(fig)
    fig.update_xaxes(tickformat='.0%', showgrid=True, gridcolor='#262A33')
    fig.update_yaxes(showgrid=False, tickformat=None)
    st.plotly_chart(fig, width='stretch')

# ---------- new vs returning ----------
nm = f.groupby('month').agg(subscriptions=('subscriptions', 'sum'), new=('new_users', 'sum')).reset_index()
nm['returning'] = nm['subscriptions'] - nm['new']
x = pd.PeriodIndex(nm['month'], freq='M').strftime('%b')
fig = go.Figure()
for col, name, color in [('returning', 'Returning subscribers', '#3987e5'), ('new', 'First-time subscribers', '#d95926')]:
    fig.add_scatter(x=x, y=nm[col], name=name, mode='lines+markers', line=dict(color=color, width=2),
                    marker=dict(size=8, line=dict(width=2, color='#0E1117')),
                    hovertemplate='%{x}: %{y:,} ' + name.lower() + '<extra></extra>')
fig.update_layout(hovermode='x unified')
chart_title('Subscriptions per month: first-time vs returning')
st.plotly_chart(style(fig, height=320), width='stretch')

# ---------- insights ----------
all_mix = m.groupby('package')[['subscriptions', 'revenue']].sum()
all_mix = all_mix / all_mix.sum()
aug = m[m['month'] == months[-1]]
jul = m[m['month'] == months[-2]]
insight(f"Weekly is {all_mix.loc['Weekly', 'subscriptions']:.0%} of all subscriptions and "
        f"{all_mix.loc['Weekly', 'revenue']:.0%} of revenue. Monthly brings "
        f"{all_mix.loc['Monthly', 'revenue']:.0%} of revenue from {all_mix.loc['Monthly', 'subscriptions']:.0%} of volume.",
        "Revenue depends on Weekly auto-debits repeating every 7 days. Most of those cycles go unused "
        "(see What Subscribers Do), so this base is exposed the day users notice the charge.",
        "Move engaged Weekly
