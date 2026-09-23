import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import (setup, insight, style, csv, chart_title,
                    PKG_ORDER, MODE_COLORS, BRAND)

setup('Who Subscribes')
st.caption("Where subscribers are, what they pay with, and which of "
           "those groups renew. Renewal = a new subscription within 7 "
           "days of expiry.")

seg = csv('segments.csv')
ret = csv('segment_retention.csv')

# ---------- filters ----------
f1, f2 = st.columns([3, 1])
pk = f1.multiselect('Package', PKG_ORDER, default=PKG_ORDER)
pm = f2.selectbox('Payment', ['All', 'Auto', 'Manual'])


def filt(df):
    df = df[df['package'].isin(pk)]
    if pm != 'All':
        df = df[df['payment_mode'] == pm]
    return df


seg, ret = filt(seg), filt(ret)


def rate(df, by):
    g = df.groupby(by)[['labelled', 'retained']].sum()
    g['rate'] = g['retained'] / g['labelled']
    return g.reset_index()


# ---------- KPIs ----------
known_city = seg[seg['city_grp'] != 'Other']
city_tot = known_city.groupby('city_grp')['subscriptions'].sum()
dev = seg.groupby('device')['subscriptions'].sum()
mode = seg.groupby('payment_mode')['subscriptions'].sum()
pay = rate(ret, 'Transaction_Type')
pay = pay[pay['labelled'] >= 300].sort_values('rate')
c = st.columns(4)
c[0].metric('Biggest city', city_tot.idxmax(),
            f"{city_tot.max() / seg['subscriptions'].sum():.0%} of "
            "subscriptions", delta_color='off', delta_arrow='off')
c[1].metric('Paid by auto-debit',
            f"{mode.get('Auto', 0) / mode.sum():.0%}")
ios, andr = dev.get('iOS', 0), dev.get('Android', 0)
c[2].metric('iOS share (known devices)', f"{ios / (ios + andr):.0%}")
c[3].metric('Best-renewing method', pay.iloc[-1]['Transaction_Type'],
            f"{pay.iloc[-1]['rate']:.0%} renew", delta_color='off',
            delta_arrow='off')

# ---------- city ----------
left, right = st.columns(2)
cities = (seg.groupby('city_grp')['subscriptions'].sum()
          .sort_values(ascending=False).index.tolist())
with left:
    chart_title('Subscriptions by city',
                '"Other" = all cities outside the top 6')
    cm = seg.groupby(['city_grp', 'payment_mode'])['subscriptions'].sum()
    cm = cm.reset_index()
    fig = go.Figure()
    for md in ['Auto', 'Manual']:
        d = cm[cm['payment_mode'] == md].set_index('city_grp')
        d = d.reindex(cities).fillna(0)
        fig.add_bar(
            y=cities, x=d['subscriptions'], name=md, orientation='h',
            marker=dict(color=MODE_COLORS[md], cornerradius=4,
                        line=dict(width=2, color='#0E1117')),
            hovertemplate='%{y} · ' + md + ': %{x:,}<extra></extra>')
    fig.update_layout(barmode='stack', yaxis=dict(autorange='reversed'))
    st.plotly_chart(style(fig, height=340), width='stretch')

with right:
    chart_title('Renewal rate by city, auto-debit payers only',
                'Auto only, so payment mix does not distort the comparison')
    ca = rate(ret[ret['payment_mode'] == 'Auto'], 'city_grp')
    ca = ca.set_index('city_grp').reindex(cities).reset_index()
    avg = ca['retained'].sum() / ca['labelled'].sum()
    fig = go.Figure()
    fig.add_bar(
        y=ca['city_grp'], x=ca['rate'], orientation='h',
        marker=dict(color=BRAND, cornerradius=4),
        text=ca['rate'].map('{:.0%}'.format), textposition='outside',
        customdata=ca['labelled'],
        hovertemplate='%{y}: %{x:.1%} renew<br>'
                      '%{customdata:,} subscriptions measured'
                      '<extra></extra>')
    fig.add_vline(x=avg, line=dict(color='#9AA0A6', width=1, dash='dot'),
                  annotation_text=f'avg {avg:.0%}',
                  annotation_position='bottom right',
                  annotation_font_color='#9AA0A6')
    fig.update_layout(yaxis=dict(autorange='reversed'))
    fig = style(fig, height=340, legend=False)
    fig.update_xaxes(tickformat='.0%', range=[0, 1], showgrid=True,
                     gridcolor='#262A33')
    st.plotly_chart(fig, width='stretch')

# ---------- payment method ----------
left, right = st.columns(2)
pv = seg.groupby(['Transaction_Type', 'payment_mode'])['subscriptions']
pv = pv.sum().reset_index().sort_values('subscriptions', ascending=False)
pv = pv[pv['subscriptions'] >= 100]
order = pv['Transaction_Type'].tolist()
with left:
    chart_title('Subscriptions by payment method')
    fig = go.Figure()
    for md in ['Auto', 'Manual']:
        d = pv[pv['payment_mode'] == md]
        fig.add_bar(
            y=d['Transaction_Type'], x=d['subscriptions'], name=md,
            orientation='h',
            marker=dict(color=MODE_COLORS[md], cornerradius=4),
            hovertemplate='%{y}: %{x:,} subscriptions<extra></extra>')
    fig.update_layout(yaxis=dict(categoryorder='array',
                                 categoryarray=order[::-1]))
    st.plotly_chart(style(fig, height=380), width='stretch')

with right:
    chart_title('Renewal rate by payment method',
                'Methods with 300+ measured subscriptions')
    pr = pay.copy()
    pr['mode'] = pr['Transaction_Type'].map(
        pv.drop_duplicates('Transaction_Type')
          .set_index('Transaction_Type')['payment_mode'])
    fig = go.Figure()
    for md in ['Auto', 'Manual']:
        d = pr[pr['mode'] == md]
        fig.add_bar(
            y=d['Transaction_Type'], x=d['rate'], name=md,
            orientation='h',
            marker=dict(color=MODE_COLORS[md], cornerradius=4),
            text=d['rate'].map('{:.0%}'.format), textposition='outside',
            hovertemplate='%{y}: %{x:.1%} renew<extra></extra>')
    fig.update_layout(yaxis=dict(categoryorder='array',
                                 categoryarray=pr['Transaction_Type']))
    fig = style(fig, height=380)
    fig.update_xaxes(tickformat='.0%', range=[0, 1], showgrid=True,
                     gridcolor='#262A33')
    st.plotly_chart(fig, width='stretch')

# ---------- device ----------
chart_title('Renewal rate by device and payment type')
dr = rate(ret, ['device', 'payment_mode'])
fig = go.Figure()
for md in ['Auto', 'Manual']:
    d = dr[dr['payment_mode'] == md]
    fig.add_bar(
        x=d['device'], y=d['rate'], name=md,
        marker=dict(color=MODE_COLORS[md], cornerradius=4),
        text=d['rate'].map('{:.0%}'.format), textposition='outside',
        hovertemplate='%{x} · ' + md + ': %{y:.1%} renew<extra></extra>')
fig.update_layout(barmode='group')
fig = style(fig, height=300)
fig.update_yaxes(tickformat='.0%', range=[0, 1])
st.plotly_chart(fig, width='stretch')

# ---------- insights ----------
allret = csv('segment_retention.csv')
a = rate(allret, 'Transaction_Type').set_index('Transaction_Type')['rate']
insight(
    f"How people pay decides renewal. Ufone renews {a['Ufone']:.0%}, "
    f"JazzCash Checkout {a['JazzCash Checkout']:.0%}, Easypaisa "
    f"{a['Easypaisa']:.0%}. Card renews {a['Credit/Debit Card']:.0%} and "
    f"Bill Payment {a['Bill Payment']:.0%}.",
    "Device barely matters once payment type is known: iOS and Android "
    "renew within a few points of each other. The lever is the payment "
    "rail, not the phone.",
    "At checkout, default users to a wallet or carrier auto-debit. "
    "Treat card and bill-payment users as one-time buyers unless they "
    "switch.")
big = ['Lahore', 'Karachi', 'Multan', 'Faisalabad', 'Rawalpindi',
       'Islamabad']
acr = rate(allret[allret['payment_mode'] == 'Auto'], 'city_grp')
acr = acr.set_index('city_grp').reindex(big)
ac = acr['rate'].sort_values()
low = ', '.join(f"{c} {v:.0%}" for c, v in ac.head(3).items())
high = ', '.join(f"{c} {v:.0%}" for c, v in ac.tail(2).items())
gap = (ac.max() - ac['Karachi']) * acr.loc['Karachi', 'labelled']
insight(
    f"Among auto payers, the weakest renewers are {low}. "
    f"The strongest are {high}.",
    "Karachi is the second-biggest market and sits in the weak group. "
    f"Matching the best city's rate would have kept about {gap:,.0f} "
    "more Karachi renewals over Jan to Aug.",
    "Check Karachi deal coverage and wallet-balance failures before "
    "spending more on Karachi acquisition.")
