# Subscriber Retention Engine: Golootlo
# One-file Streamlit dashboard. Data files sit next to this file
# (or in a dashboard_data folder). The target list reads from Supabase.
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Subscriber Retention Engine',
                   page_icon='📈', layout='wide')

# =============================================================
# SETUP: paths, colours, helpers
# =============================================================
BASE = Path(__file__).parent
DATA = BASE / 'dashboard_data' if (BASE / 'dashboard_data').exists() \
    else BASE

BRAND = '#0064DC'
TEXT = '#FAFAFA'
GRID = '#262A33'
BG = '#0E1117'
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stMetric, button, input {
  font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 2rem; max-width: 1300px; }
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
button[data-baseweb="tab"] p { font-size: 0.95rem; font-weight: 600; }
</style>""", unsafe_allow_html=True)


@st.cache_data
def csv(name):
    return pd.read_csv(DATA / name)


@st.cache_data
def js(name):
    with open(DATA / name) as f:
        return json.load(f)


def rs(x):
    if abs(x) >= 1e6:
        return f'Rs {x / 1e6:,.1f}M'
    if abs(x) >= 1e3:
        return f'Rs {x / 1e3:,.0f}K'
    return f'Rs {x:,.0f}'


def insight(observation, so_what, action=None):
    html = (f"<div class='insight'><b>What we see:</b> {observation}"
            f"<br><b>So what:</b> {so_what}")
    if action:
        html += f"<br><b>Action:</b> {action}"
    st.markdown(html + "</div>", unsafe_allow_html=True)


def chart_title(text, sub=None):
    html = (f"<div style='font-weight:600;font-size:0.95rem;"
            f"margin-top:8px'>{text}</div>")
    if sub:
        html += f"<div class='caveat'>{sub}</div>"
    st.markdown(html, unsafe_allow_html=True)


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
        fig.update_yaxes(tickformat='.0%', range=[0, 1])
    else:
        fig.update_xaxes(tickformat='.0%', range=[0, 1], showgrid=True,
                         gridcolor=GRID)
    return fig


def show(fig):
    st.plotly_chart(fig, width='stretch')


def rate(df, by):
    g = df.groupby(by)[['labelled', 'retained']].sum()
    g['rate'] = g['retained'] / g['labelled']
    return g.reset_index()


def mode_bars(df, x, y, order, pct=True, text=True, hover=''):
    """Grouped Auto vs Manual bars."""
    fig = go.Figure()
    for md in ['Auto', 'Manual']:
        d = df[df['payment_mode'] == md].set_index(x).reindex(order)
        fig.add_bar(
            x=order, y=d[y], name=md,
            marker=dict(color=MODE_COLORS[md], cornerradius=4),
            text=d[y].map('{:.0%}'.format) if text else None,
            textposition='outside',
            hovertemplate='%{x} · ' + md + ': %{y:.0%}' + hover
                          + '<extra></extra>')
    fig.update_layout(barmode='group')
    return fig


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
                'Promotions', 'Renewal Risk', 'Auto-Pay Simulator',
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
            marker=dict(color='#5f6b7a', cornerradius=4),
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
            ('new', 'First-time subscribers', '#d95926')]:
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
    insight(
        f"Weekly is {tot.loc['Weekly', 'subscriptions']:.0%} of all "
        f"subscriptions and {tot.loc['Weekly', 'revenue']:.0%} of "
        f"revenue. Monthly brings {tot.loc['Monthly', 'revenue']:.0%} "
        f"of revenue from {tot.loc['Monthly', 'subscriptions']:.0%} "
        "of volume.",
        "Revenue depends on Weekly auto-debits repeating every 7 days. "
        "Most of those cycles go unused (see What Subscribers Do), so "
        "this base is exposed the day users notice the charge.",
        "Move engaged Weekly users to Monthly or Quarterly, and "
        "activate the passive ones.")
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
    f1, f2 = st.columns([3, 1])
    pk = f1.multiselect('Package', PKG_ORDER, default=PKG_ORDER,
                        key='w_p')
    pm = f2.selectbox('Payment', ['All', 'Auto', 'Manual'], key='w_pm')
    seg = seg0[seg0['package'].isin(pk)]
    ret = ret0[ret0['package'].isin(pk)]
    if pm != 'All':
        seg = seg[seg['payment_mode'] == pm]
        ret = ret[ret['payment_mode'] == pm]

    city_tot = seg[seg['city_grp'] != 'Other'].groupby(
        'city_grp')['subscriptions'].sum()
    dev = seg.groupby('device')['subscriptions'].sum()
    mode = seg.groupby('payment_mode')['subscriptions'].sum()
    pay = rate(ret, 'Transaction_Type')
    pay = pay[pay['labelled'] >= 300].sort_values('rate')
    ios, andr = dev.get('iOS', 0), dev.get('Android', 0)
    c = st.columns(4)
    c[0].metric('Biggest city', city_tot.idxmax(),
                f"{city_tot.max() / seg['subscriptions'].sum():.0%} of "
                "subscriptions", delta_color='off', delta_arrow='off')
    c[1].metric('Paid by auto-debit',
                f"{mode.get('Auto', 0) / mode.sum():.0%}")
    c[2].metric('iOS share (known devices)',
                f"{ios / max(ios + andr, 1):.0%}")
    c[3].metric('Best-renewing method',
                pay.iloc[-1]['Transaction_Type'],
                f"{pay.iloc[-1]['rate']:.0%} renew",
                delta_color='off', delta_arrow='off')

    cities = (seg.groupby('city_grp')['subscriptions'].sum()
              .sort_values(ascending=False).index.tolist())
    left, right = st.columns(2)
    with left:
        chart_title('Subscriptions by city',
                    '"Other" = all cities outside the top 6')
        cm = seg.groupby(['city_grp', 'payment_mode'])[
            'subscriptions'].sum().reset_index()
        fig = go.Figure()
        for md in ['Auto', 'Manual']:
            d = cm[cm['payment_mode'] == md].set_index('city_grp')
            d = d.reindex(cities).fillna(0)
            fig.add_bar(
                y=cities, x=d['subscriptions'], name=md,
                orientation='h',
                marker=dict(color=MODE_COLORS[md], cornerradius=4,
                            line=dict(width=2, color=BG)),
                hovertemplate='%{y} · ' + md + ': %{x:,}<extra></extra>')
        fig.update_layout(barmode='stack',
                          yaxis=dict(autorange='reversed'))
        show(style(fig, height=340))
    with right:
        chart_title('Renewal rate by city, auto-debit payers only',
                    'Auto only, so payment mix does not distort it')
        ca = rate(ret[ret['payment_mode'] == 'Auto'], 'city_grp')
        ca = ca.set_index('city_grp').reindex(cities).reset_index()
        fig = go.Figure()
        fig.add_bar(
            y=ca['city_grp'], x=ca['rate'], orientation='h',
            marker=dict(color=BRAND, cornerradius=4),
            text=ca['rate'].map('{:.0%}'.format), textposition='outside',
            customdata=ca['labelled'],
            hovertemplate='%{y}: %{x:.1%} renew<br>%{customdata:,} '
                          'subscriptions measured<extra></extra>')
        fig.update_layout(yaxis=dict(autorange='reversed'))
        show(pct_axis(style(fig, height=340, legend=False), 'x'))

    pv = seg.groupby(['Transaction_Type', 'payment_mode'])[
        'subscriptions'].sum().reset_index()
    pv = pv[pv['subscriptions'] >= 100].sort_values('subscriptions')
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
                    'Methods with 300+ measured subscriptions')
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

    chart_title('Renewal rate by device and payment type')
    dr = rate(ret, ['device', 'payment_mode'])
    show(pct_axis(style(mode_bars(dr, 'device', 'rate',
                                  ['Android', 'iOS', 'Unknown'],
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
        "Default checkout to a wallet or carrier auto-debit. Treat card "
        "and bill-payment users as one-time buyers unless they switch.")
    big = ['Lahore', 'Karachi', 'Multan', 'Faisalabad', 'Rawalpindi',
           'Islamabad']
    acr = rate(ret0[ret0['payment_mode'] == 'Auto'], 'city_grp')
    acr = acr.set_index('city_grp').reindex(big)
    ac = acr['rate'].sort_values()
    low = ', '.join(f"{c_} {v:.0%}" for c_, v in ac.head(3).items())
    high = ', '.join(f"{c_} {v:.0%}" for c_, v in ac.tail(2).items())
    gap = (ac.max() - ac['Karachi']) * acr.loc['Karachi', 'labelled']
    insight(
        f"Among auto payers, the weakest renewers are {low}. "
        f"The strongest are {high}.",
        "Karachi is the second-biggest market and sits in the weak "
        f"group. Matching the best city's rate would have kept about "
        f"{gap:,.0f} more Karachi renewals over Jan to Aug.",
        "Check Karachi deal coverage and wallet-balance failures before "
        "spending more on Karachi acquisition.")

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
        parts = [('instore_uses', 'Instore', '#3987e5'),
                 ('ecom_uses', 'Ecom', '#d95926'),
                 ('delivery_orders', 'Delivery', '#199e70')]
        fig = go.Figure()
        for col, name, color in parts:
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
        "Manual payers subscribe at the counter to unlock one deal. "
        "Auto payers keep paying whether or not they use it. That is "
        "inertia, and it turns into cancellations and complaints once "
        "users notice the charge.",
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
    insight(
        f"{same:.0%} of renewers keep the same favourite brand from one "
        "subscription to the next.",
        "With 30,000+ brands available, this is preference, not lack "
        "of choice.",
        "Personalise renewal reminders with the user's own top brand.")

# =============================================================
# TAB 4: PROMOTIONS
# =============================================================
with tabs[3]:
    camp = csv('campaigns.csv')
    nxt = csv('campaign_next_package.csv').set_index('campaign')
    promos = ['New Year', 'Ramadan', 'Eid', 'PKR 79']
    cp = camp.set_index('campaign').reindex(promos + ['Regular'])
    done = cp.loc[['New Year', 'Ramadan', 'Eid']]
    reg = cp.loc['Regular']

    pr = cp.loc[promos]
    new_share = ((pr['new_to_subscription'] * pr['subscriptions']).sum()
                 / pr['subscriptions'].sum())
    back30 = ((done['returned_30d'] * done['labelled_30d']).sum()
              / done['labelled_30d'].sum())
    c = st.columns(4)
    c[0].metric('Promo subscriptions', f"{pr['subscriptions'].sum():,.0f}")
    c[1].metric('First-time subscribers in promos', f"{new_share:.0%}")
    c[2].metric('Discount given', rs(pr['discount_given'].sum()))
    c[3].metric('Back within 30 days (past promos)', f"{back30:.0%}",
                f"regular: {reg['returned_30d']:.0%}",
                delta_color='off', delta_arrow='off')

    left, right = st.columns(2)
    with left:
        chart_title('Did promo subscribers come back?',
                    'Share who subscribed again. PKR 79 renewals start '
                    'in September, so they are not measured yet.')
        names = ['New Year', 'Ramadan', 'Eid', 'Regular']
        d = cp.loc[names]
        fig = go.Figure()
        for col, name, color in [
                ('retained_7d', 'Within 7 days', '#3987e5'),
                ('returned_30d', 'Within 30 days', '#d95926')]:
            fig.add_bar(
                x=names, y=d[col], name=name,
                marker=dict(color=color, cornerradius=4),
                text=d[col].map('{:.0%}'.format), textposition='outside',
                hovertemplate='%{x}: %{y:.0%} ' + name.lower()
                              + '<extra></extra>')
        fig.update_layout(barmode='group')
        show(pct_axis(style(fig, height=360)))
    with right:
        chart_title('What they bought next',
                    'Next subscription after the promo package')
        cols = ['Weekly', 'Monthly', 'Quarterly', 'Half Yearly', 'None']
        colors = {**PKG_COLORS, 'None': '#5f6b7a'}
        d = nxt.reindex(names)[cols]
        fig = go.Figure()
        for col in cols:
            label = 'Did not return' if col == 'None' else col
            fig.add_bar(
                y=names, x=d[col], name=label, orientation='h',
                marker=dict(color=colors[col],
                            line=dict(width=2, color=BG)),
                hovertemplate='%{y} → ' + label + ': %{x:.0%}'
                              '<extra></extra>')
        fig.update_layout(barmode='stack',
                          yaxis=dict(autorange='reversed'))
        show(pct_axis(style(fig, height=360), 'x'))

    chart_title('Campaign economics')
    t = cp.loc[promos].reset_index()
    t['Ran'] = (pd.to_datetime(t['first_start']).dt.strftime('%b %d')
                + ' to '
                + pd.to_datetime(t['last_start']).dt.strftime('%b %d'))
    t['Back in 30 days'] = t['returned_30d']
    t['Discount per returning user'] = t['discount_given'] / (
        t['subscriptions'] * t['returned_30d'])
    money = st.column_config.NumberColumn(format='Rs %,.0f')
    pct = st.column_config.NumberColumn(format='percent')
    st.dataframe(
        t[['campaign', 'Ran', 'subscriptions', 'new_to_subscription',
           'revenue', 'discount_given', 'Back in 30 days',
           'Discount per returning user']].rename(columns={
               'campaign': 'Campaign', 'subscriptions': 'Subscriptions',
               'new_to_subscription': 'First-time subscribers',
               'revenue': 'Revenue', 'discount_given': 'Discount given'}),
        hide_index=True, width='stretch',
        column_config={'Revenue': money, 'Discount given': money,
                       'Discount per returning user': money,
                       'First-time subscribers': pct,
                       'Back in 30 days': pct,
                       'Subscriptions': st.column_config.NumberColumn(
                           format='%,d')})
    st.markdown("<span class='caveat'>PKR 79 return rates appear once "
                "September data is added.</span>",
                unsafe_allow_html=True)

    insight(
        f"Promo packages pull in new people: "
        f"{cp.loc['New Year', 'new_to_subscription']:.0%} of New Year "
        f"buyers and {cp.loc['PKR 79', 'new_to_subscription']:.0%} of "
        "PKR 79 buyers had never subscribed before. But only "
        f"{done['returned_30d'].min():.0%} to "
        f"{done['returned_30d'].max():.0%} came back within 30 days, "
        f"vs {reg['returned_30d']:.0%} for regular subscribers.",
        "Promos work as acquisition, not retention. Most promo buyers "
        "treat them as a one-off deal. The ones who return mostly move "
        "to Monthly, not Weekly.",
        "Judge promos on cost per returning subscriber, not sign-ups. "
        "Build a day-25 conversion push into every promo that offers "
        "Monthly auto-pay.")
    insight(
        f"PKR 79 gave away {rs(cp.loc['PKR 79', 'discount_given'])} in "
        f"discount for {cp.loc['PKR 79', 'subscriptions']:,.0f} "
        "subscriptions.",
        "If PKR 79 buyers return like earlier promos (17 to 26%), each "
        "returning subscriber will have cost roughly Rs 2,000 to Rs "
        "3,000 in discount.",
        "Use September data to confirm the PKR 79 return rate before "
        "repeating a price this low.")

# =============================================================
# TAB 5: RENEWAL RISK
# =============================================================
with tabs[4]:
    drv = csv('renewal_drivers.csv')
    par = csv('usage_paradox.csv')
    rsk = csv('risk_summary.csv')

    c = st.columns(4)
    c[0].metric('Model accuracy (AUC)', f"{metrics['auc_model']:.2f}",
                f"simple rule: {metrics['auc_baseline']:.2f}",
                delta_color='off', delta_arrow='off')
    c[1].metric('Lapse rate in top 20% flagged',
                f"{metrics['lapse_in_top20_model']:.0%}",
                f"average: {metrics['test_lapse_rate']:.0%}",
                delta_color='off', delta_arrow='off')
    c[2].metric('Active subscribers scored',
                f"{rsk['subscribers'].sum():,}")
    hi = rsk[rsk['risk_band'] == 'High']
    c[3].metric('High risk', f"{hi['subscribers'].sum():,}",
                f"{rs(hi['revenue_at_stake'].sum())} at stake",
                delta_color='off', delta_arrow='off')
    st.markdown(
        "<span class='caveat'>Logistic regression on auto-pay "
        "subscribers, trained on Jan to May and tested on Jun to Aug. "
        "Manual payers are scored from their historical renewal rate. "
        "AUC: 0.5 = coin flip, 1.0 = perfect.</span>",
        unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        chart_title('What drives renewal (auto-pay subscribers)',
                    'Odds ratio vs baseline: Easypaisa, Weekly, first '
                    'subscription, Android, Lahore. Right = renews more.')
        d = drv[(drv['p_value'] < 0.05)
                & ~drv['driver'].str.contains('Renewed last time')].copy()
        d['driver'] = d['driver'].str.replace(
            'Number of past cycles (log)',
            'More past renewals (per doubling)', regex=False)
        d = d.sort_values('odds_ratio')
        colors = [BRAND if r >= 1 else '#d95926' for r in d['odds_ratio']]
        fig = go.Figure()
        fig.add_bar(
            y=d['driver'], x=d['odds_ratio'] - 1, base=1,
            orientation='h', marker=dict(color=colors, cornerradius=4),
            customdata=d['in_plain_english'],
            hovertemplate='%{y}<br>%{customdata}<extra></extra>')
        fig.add_vline(x=1, line=dict(color='#9AA0A6', width=1))
        fig = style(fig, height=460, legend=False)
        fig.update_xaxes(type='log', showgrid=True, gridcolor=GRID,
                         tickvals=[0.1, 0.25, 0.5, 1, 2, 3],
                         ticktext=['0.1x', '0.25x', '0.5x', '1x', '2x',
                                   '3x'])
        show(fig)
    with right:
        chart_title('The usage paradox',
                    'Renewal rate by history and early usage')
        par['label'] = par['history'].replace({
            'First sub': 'First subscription',
            'Renewed last time': 'Renewed last time',
            'Lapsed before': 'Lapsed before'})
        fig = go.Figure()
        for flag, name, color in [(0, 'No use in first 5 days',
                                   '#5f6b7a'),
                                  (1, 'Used in first 5 days', BRAND)]:
            dd = par[par['used_early'] == flag]
            fig.add_bar(
                x=dd['label'], y=dd['retained'], name=name,
                marker=dict(color=color, cornerradius=4),
                text=dd['retained'].map('{:.0%}'.format),
                textposition='outside',
                hovertemplate='%{x}: %{y:.0%} renew<extra></extra>')
        fig.update_layout(barmode='group')
        show(pct_axis(style(fig, height=460)))

    chart_title('Active subscribers by risk level',
                f"Everyone with a live subscription on {END:%b %d}")
    band = rsk.groupby(['campaign', 'risk_band'])['subscribers'].sum()
    band = band.unstack().reindex(columns=['High', 'Medium', 'Low'])
    band = band.fillna(0)
    bcol = {'High': '#d95926', 'Medium': '#c98500', 'Low': '#199e70'}
    fig = go.Figure()
    for b in ['High', 'Medium', 'Low']:
        fig.add_bar(
            y=band.index, x=band[b], name=f'{b} risk', orientation='h',
            marker=dict(color=bcol[b], line=dict(width=2, color=BG)),
            hovertemplate='%{y} · ' + b + ' risk: %{x:,}<extra></extra>')
    fig.update_layout(barmode='stack')
    show(style(fig, height=240))

    act = rsk.groupby('recommended_action').agg(
        subscribers=('subscribers', 'sum'),
        revenue=('revenue_at_stake', 'sum')).sort_values(
        'subscribers', ascending=False).reset_index()
    st.dataframe(
        act.rename(columns={'recommended_action': 'Recommended action',
                            'subscribers': 'Subscribers',
                            'revenue': 'Current subscription value'}),
        hide_index=True, width='stretch',
        column_config={
            'Current subscription value': st.column_config.NumberColumn(
                format='Rs %,.0f'),
            'Subscribers': st.column_config.NumberColumn(format='%,d')})

    p = par.set_index(['history', 'used_early'])['retained']
    insight(
        "Auto payers who renewed last time and did NOT use the app "
        f"renew {p[('Renewed last time', 0)]:.0%} of the time. Those who "
        f"did use it renew {p[('Renewed last time', 1)]:.0%}.",
        "The most 'loyal' auto payers are often the least engaged. "
        "Their renewals are inertia, which is fragile.",
        "Treat passive auto payers as a hidden risk segment, not a win "
        "(see the Auto-Pay Simulator).")
    insight(
        "Past behaviour predicts renewal best: each doubling of past "
        "renewals makes renewal 2.5x more likely, and someone who lapsed "
        "once is 3.8x more likely to lapse again. Promo packages are "
        "13.5x more likely to lapse.",
        f"The model flags lapses {metrics['lapse_in_top20_model']:.0%} "
        "of the time in its top 20%, vs "
        f"{metrics['lapse_in_top20_baseline']:.0%} for a simple "
        "payment-and-package rule. Useful, not perfect.",
        "Work the High-risk list first, starting with those closest to "
        "expiry (Target Lists tab).")

# =============================================================
# TAB 6: AUTO-PAY SIMULATOR
# =============================================================
with tabs[5]:
    sim = csv('simulator_inputs.csv').set_index('package').reindex(
        PKG_ORDER)
    pas = csv('passive_auto_payers.csv')
    om = csv('overview_monthly.csv')
    man = om[(om['payment_mode'] == 'Manual')
             & (om['campaign'] == 'Regular')
             & (om['month'] < '2026-08')]
    n_months = man['month'].nunique()
    man_pm = man.groupby('package')['subscriptions'].sum() / n_months
    man_pm = man_pm.reindex(PKG_ORDER).fillna(0)

    st.markdown('#### Lever 1: Move manual payers to auto-pay')
    s1, s2 = st.columns(2)
    conv = s1.slider('% of new manual payers switched to auto-pay',
                     0, 100, 20, 5, key='s_conv') / 100
    real = s2.slider('How much of the auto-pay advantage they really '
                     'get', 0, 100, 50, 10, key='s_real',
                     help='Auto-pay users are partly more committed to '
                          'begin with. 50% is a conservative '
                          'assumption: a switched user gets half the '
                          'renewal boost.') / 100

    ra = sim['retention_Auto']
    rm = sim['retention_Manual']
    # expected number of future renewals = r / (1 - r)
    future_auto = ra / (1 - ra)
    future_man = rm / (1 - rm)
    price = pd.Series(PRICE).reindex(PKG_ORDER)
    switched = man_pm * conv
    extra_per_user = (future_auto - future_man) * real * price
    value = switched * extra_per_user

    c = st.columns(3)
    c[0].metric('Manual payers switched per month',
                f"{switched.sum():,.0f}")
    c[1].metric('Extra revenue per month of switching',
                rs(value.sum()))
    c[2].metric('Per year', rs(value.sum() * 12))

    chart_title('Extra revenue from one month of switching, by package',
                'Future renewals they make that manual payers would not')
    fig = go.Figure()
    fig.add_bar(
        x=PKG_ORDER, y=value.values,
        marker=dict(color=[PKG_COLORS[p] for p in PKG_ORDER],
                    cornerradius=4),
        text=[rs(v) for v in value.values], textposition='outside',
        customdata=list(zip(switched.round(0), extra_per_user.round(0))),
        hovertemplate='%{x}: %{customdata[0]:,.0f} switched × '
                      'Rs %{customdata[1]:,.0f} each<extra></extra>')
    fig = style(fig, height=300, legend=False)
    fig.update_yaxes(tickprefix='Rs ', tickformat='.2s')
    show(fig)
    with st.expander('How this is calculated'):
        tbl = pd.DataFrame({
            'New manual payers / month': man_pm.round(0),
            'Auto renewal rate': ra, 'Manual renewal rate': rm,
            'Price': price,
            'Extra value per switched user': extra_per_user.round(0)})
        st.dataframe(tbl, width='stretch', column_config={
            'Auto renewal rate': st.column_config.NumberColumn(
                format='percent'),
            'Manual renewal rate': st.column_config.NumberColumn(
                format='percent'),
            'Price': st.column_config.NumberColumn(format='Rs %,.0f'),
            'Extra value per switched user':
                st.column_config.NumberColumn(format='Rs %,.0f')})
        st.markdown(
            "Expected future renewals = r ÷ (1 − r), where r is the "
            "renewal rate. Extra value = (auto future renewals − manual "
            "future renewals) × realisation % × price. Based on regular "
            "packages, Jan to Jul.")

    st.markdown('#### Lever 2: The passive auto-pay risk')
    reg_p = pas[pas['campaign'] == 'Regular'].set_index('package')
    reg_p = reg_p.reindex(PKG_ORDER).fillna(0)
    monthly_rev = reg_p['passive_payers'] * pd.Series(
        {p: PRICE[p] * PER_MONTH[p] for p in PKG_ORDER})
    cancel = st.slider('% of passive payers who cancel once they notice '
                       'the charge', 0, 100, 25, 5, key='s_cancel') / 100
    save = st.slider('% of those you win back with an activation '
                     'campaign', 0, 100, 30, 5, key='s_save') / 100
    at_risk = monthly_rev.sum() * cancel
    c = st.columns(3)
    c[0].metric('Passive auto payers (regular packages)',
                f"{reg_p['passive_payers'].sum():,.0f}")
    c[1].metric('Monthly revenue at risk', rs(at_risk))
    c[2].metric('Protected by activation', rs(at_risk * save))
    st.markdown(
        f"<span class='caveat'>Passive = auto-pay subscription active on "
        f"{END:%b %d} with no use so far in its current cycle. PKR 79 "
        "users are excluded because their subscriptions just started."
        "</span>", unsafe_allow_html=True)

    insight(
        "Manual payers barely renew, so every switch to auto-pay adds "
        "future renewals. At the default settings (20% switched, half "
        f"the boost) that is about {rs(value.sum())} a month.",
        "This is a steady compounding gain, not a one-off spike. The "
        "Weekly package drives most of it because it renews most often.",
        "Offer a small first-week bonus for choosing wallet or carrier "
        "auto-pay at checkout.")
    insight(
        f"{reg_p['passive_payers'].sum():,.0f} regular auto payers "
        f"worth about {rs(monthly_rev.sum())} a month have not used "
        "their current subscription.",
        "This revenue exists because people haven't noticed, not "
        "because they value it. It is the most fragile revenue on the "
        "books.",
        "Activate them before they notice: a personalised first-deal "
        "push beats a cancellation and a complaint.")

# =============================================================
# TAB 7: TARGET LISTS (password protected, reads Supabase)
# =============================================================
with tabs[6]:
    st.markdown('#### Target lists and customer lookup')
    st.caption('Names and phone numbers of active subscribers, ranked by '
               'lapse risk. Password protected.')

    if 'APP_PASSWORD' not in st.secrets or 'DB_URL' not in st.secrets:
        st.info('Add DB_URL and APP_PASSWORD in the app Secrets to '
                'enable this tab.')
    else:
        pw = st.text_input('Password', type='password', key='t_pw')
        if pw != st.secrets['APP_PASSWORD']:
            if pw:
                st.error('Wrong password.')
        else:
            @st.cache_data(ttl=3600, show_spinner='Loading list...')
            def load_list():
                from sqlalchemy import create_engine
                eng = create_engine(st.secrets['DB_URL'])
                return pd.read_sql('select * from retention_risk_list',
                                   eng)

            try:
                rl = load_list()
            except Exception as e:
                st.error('Could not reach Supabase. If the project is '
                         'paused, open it in Supabase and click Restore. '
                         f'({str(e)[:150]})')
                st.stop()

            ph = rl['phone'].astype(str).str.replace(r'\.0$', '',
                                                     regex=True)
            rl['phone'] = '0' + ph.str.replace(r'\D', '',
                                               regex=True).str.lstrip('0')
            f1, f2, f3, f4 = st.columns(4)
            bands = f1.multiselect('Risk', ['High', 'Medium', 'Low'],
                                   default=['High'], key='t_b')
            modes = f2.multiselect('Payment', ['Auto', 'Manual'],
                                   default=['Auto', 'Manual'], key='t_m')
            camps = f3.multiselect(
                'Campaign', sorted(rl['campaign'].unique()),
                default=sorted(rl['campaign'].unique()), key='t_c')
            maxd = int(rl['days_to_expiry'].max())
            days = f4.slider('Expires within (days)', 0, maxd, 7,
                             key='t_d')
            f5, f6 = st.columns(2)
            acts = f5.multiselect(
                'Action', sorted(rl['recommended_action'].unique()),
                default=sorted(rl['recommended_action'].unique()),
                key='t_a')
            q = f6.text_input('Search name, phone or user ID', key='t_q')

            out = rl[rl['risk_band'].isin(bands)
                     & rl['payment_mode'].isin(modes)
                     & rl['campaign'].isin(camps)
                     & (rl['days_to_expiry'] <= days)
                     & rl['recommended_action'].isin(acts)]
            if q:
                ql = q.strip().lower().lstrip('0')
                hit = (rl['User_Name'].astype(str).str.lower()
                       .str.contains(ql, regex=False)
                       | rl['phone'].str.contains(ql, regex=False)
                       | rl['User_ID'].astype(str).str.contains(
                           ql, regex=False))
                out = rl[hit]
                st.caption('Search ignores the filters above.')

            out = out.sort_values(['days_to_expiry', 'lapse_risk'],
                                  ascending=[True, False])
            c = st.columns(3)
            c[0].metric('People in this list', f"{len(out):,}")
            c[1].metric('Current subscription value',
                        rs(out['price'].sum()))
            c[2].metric('Average lapse risk',
                        f"{out['lapse_risk'].mean():.0%}"
                        if len(out) else '-')
            cols = ['User_ID', 'User_Name', 'phone',
                    'Subscription_Package', 'campaign', 'payment_mode',
                    'Transaction_Type', 'city', 'days_to_expiry',
                    'lapse_risk', 'risk_band', 'reasons',
                    'recommended_action']
            nice = {'User_ID': 'User ID', 'User_Name': 'Name',
                    'phone': 'Phone', 'Subscription_Package': 'Package',
                    'campaign': 'Campaign', 'payment_mode': 'Payment',
                    'Transaction_Type': 'Method', 'city': 'City',
                    'days_to_expiry': 'Days to expiry',
                    'risk_band': 'Risk', 'reasons': 'Why',
                    'recommended_action': 'Action'}
            st.dataframe(
                out[cols].rename(columns=nice), hide_index=True,
                width='stretch', height=420,
                column_config={
                    'lapse_risk': st.column_config.ProgressColumn(
                        'Lapse risk', format='percent',
                        min_value=0, max_value=1)})
            st.download_button(
                'Download this list (CSV)',
                out[cols].rename(columns=nice).to_csv(
                    index=False).encode('utf-8'),
                file_name=f'target_list_{END:%Y%m%d}.csv',
                mime='text/csv', type='primary')
