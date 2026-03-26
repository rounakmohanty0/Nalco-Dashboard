# ============================================================
# NALCO NETWORK PERFORMANCE DASHBOARD
# Built with: Dash + Pandas + Plotly
# Data: DEVICE NAME MAPPING .xlsx (CLEANED_DATA sheet)
# ============================================================

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# STEP 1 — READ YOUR EXCEL FILE
# ============================================================

# Read the CLEANED_DATA sheet from your Excel file
df_raw = pd.read_excel(
    'data/DEVICE NAME MAPPING .xlsx',
    sheet_name='CLEANED_DATA',
    header=0
)

# The real column headers are in row 0 — fix that
df_raw.columns = df_raw.iloc[0]
df = df_raw.iloc[1:].reset_index(drop=True)

# Read the device name mapping sheet
dm = pd.read_excel(
    'data/DEVICE NAME MAPPING .xlsx',
    sheet_name='DEVICE_NAME_MAPPING'
)

# Convert number columns from text to actual numbers
num_cols = [
    'Availability_Percent', 'Max_Downtime_Min',
    'Total_Downtime_Min', 'LT _5_Count',
    'Min_5_30_Count', 'Min_30_60_count', 'GT_60_Count'
]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Apply clean device names from mapping sheet
name_map = dict(zip(dm['OLD_NAME'], dm['NEW_NAME']))
df['Clean_Name'] = df['Device_Name'].map(name_map).fillna(df['Device_Name'])

# Add severity column based on availability
def get_severity(avail):
    if avail < 50:   return 'CRITICAL'
    elif avail < 95: return 'HIGH'
    elif avail < 99: return 'MEDIUM'
    elif avail < 100:return 'LOW'
    else:            return 'OK'

df['Severity'] = df['Availability_Percent'].apply(get_severity)

# ============================================================
# STEP 2 — CALCULATE KPI NUMBERS
# ============================================================

total_devices    = len(df)
total_downtime   = int(df['Total_Downtime_Min'].sum())
avg_availability = round(df['Availability_Percent'].mean(), 2)
total_failures   = int(df['Total_Downtime_Min'].gt(0).sum())
critical_devices = int((df['Availability_Percent'] < 50).sum())

# ============================================================
# STEP 3 — PREPARE CHART DATA
# ============================================================

# Bar chart — top 15 devices by downtime
top15 = df[df['Total_Downtime_Min'] > 0].sort_values(
    'Total_Downtime_Min', ascending=False
).head(15)

# Pie chart — severity breakdown
severity_counts = df['Severity'].value_counts().reset_index()
severity_counts.columns = ['Severity', 'Count']

# Line chart — availability distribution (sorted)
avail_df = df.sort_values('Availability_Percent').reset_index(drop=True)
avail_df['Device_No'] = range(1, len(avail_df) + 1)

# Scatter chart — max downtime vs availability
scatter_df = df[df['Total_Downtime_Min'] > 0].copy()

# Downtime type breakdown
break_data = pd.DataFrame({
    'Break Type': ['< 5 min', '5–30 min', '30–60 min', '> 60 min'],
    'Count': [
        int(df['LT _5_Count'].sum()),
        int(df['Min_5_30_Count'].sum()),
        int(df['Min_30_60_count'].sum()),
        int(df['GT_60_Count'].sum())
    ]
})

# ============================================================
# STEP 4 — BUILD CHARTS
# ============================================================

# Color map for severity
sev_colors = {
    'CRITICAL': '#ef4444',
    'HIGH':     '#f97316',
    'MEDIUM':   '#eab308',
    'LOW':      '#3b82f6',
    'OK':       '#22c55e'
}

# Bar chart
fig_bar = px.bar(
    top15,
    x='Total_Downtime_Min',
    y='Clean_Name',
    orientation='h',
    color='Severity',
    color_discrete_map=sev_colors,
    title='Top 15 Devices by Total Downtime',
    labels={'Total_Downtime_Min': 'Total Downtime (minutes)', 'Clean_Name': 'Device'},
    template='plotly_dark'
)
fig_bar.update_layout(
    height=450,
    margin=dict(l=10, r=10, t=40, b=10),
    legend_title='Severity',
    yaxis={'categoryorder': 'total ascending'}
)

# Pie chart — severity distribution
fig_pie = px.pie(
    severity_counts,
    names='Severity',
    values='Count',
    color='Severity',
    color_discrete_map=sev_colors,
    title='Device Severity Distribution',
    template='plotly_dark',
    hole=0.4
)
fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))

# Line chart — availability across all devices
fig_line = px.line(
    avail_df,
    x='Device_No',
    y='Availability_Percent',
    title='Availability % Across All 100 Devices',
    labels={'Device_No': 'Device Number', 'Availability_Percent': 'Availability (%)'},
    template='plotly_dark',
    color_discrete_sequence=['#00d4aa']
)
fig_line.add_hline(y=99, line_dash='dash', line_color='#fbbf24',
                   annotation_text='99% threshold')
fig_line.add_hline(y=95, line_dash='dash', line_color='#f97316',
                   annotation_text='95% threshold')
fig_line.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))

# Scatter chart
fig_scatter = px.scatter(
    scatter_df,
    x='Max_Downtime_Min',
    y='Availability_Percent',
    color='Severity',
    color_discrete_map=sev_colors,
    hover_name='Clean_Name',
    title='Max Downtime vs Availability %',
    labels={
        'Max_Downtime_Min': 'Max Single Downtime (min)',
        'Availability_Percent': 'Availability (%)'
    },
    template='plotly_dark',
    size='Total_Downtime_Min',
    size_max=30
)
fig_scatter.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))

# Bar chart — break type counts
fig_breaks = px.bar(
    break_data,
    x='Break Type',
    y='Count',
    title='Downtime Break Duration Breakdown',
    color='Break Type',
    color_discrete_sequence=['#22c55e', '#eab308', '#f97316', '#ef4444'],
    template='plotly_dark'
)
fig_breaks.update_layout(
    height=320,
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False
)

# ============================================================
# STEP 5 — BUILD THE DASHBOARD LAYOUT
# ============================================================

# Simple login credentials — change these as you like
VALID_USERNAME = 'admin'
VALID_PASSWORD = 'nalco123'

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True
)
app.title = 'NALCO Network Dashboard'
server = app.server

# ── Colour helpers ──────────────────────────────────────────
CARD_STYLE = {
    'background': '#1e293b',
    'border': '1px solid #334155',
    'borderRadius': '12px',
    'padding': '20px',
    'marginBottom': '16px'
}

def kpi_card(title, value, color, icon):
    return dbc.Col(
        html.Div([
            html.Div(icon, style={'fontSize': '28px', 'marginBottom': '8px'}),
            html.Div(str(value), style={
                'fontSize': '32px', 'fontWeight': '800', 'color': color
            }),
            html.Div(title, style={
                'fontSize': '12px', 'color': '#94a3b8',
                'textTransform': 'uppercase', 'letterSpacing': '1px'
            })
        ], style={**CARD_STYLE, 'textAlign': 'center',
                  'borderTop': f'3px solid {color}'}),
        xs=12, sm=6, md=3
    )

# ── Login page ──────────────────────────────────────────────
login_layout = html.Div([
    html.Div([
        html.Div([
            html.P('NALCO // NETWATCH', style={
                'color': '#00d4aa', 'fontSize': '11px',
                'letterSpacing': '3px', 'marginBottom': '6px'
            }),
            html.H2('Network Monitor', style={'fontWeight': '700', 'marginBottom': '4px'}),
            html.P('Sign in to access the dashboard', style={
                'color': '#64748b', 'fontSize': '13px', 'marginBottom': '28px'
            }),
            dbc.Input(id='username', placeholder='Username',
                      type='text', className='mb-3',
                      style={'background': '#0f172a', 'border': '1px solid #334155',
                             'color': '#fff', 'borderRadius': '8px'}),
            dbc.Input(id='password', placeholder='Password',
                      type='password', className='mb-3',
                      style={'background': '#0f172a', 'border': '1px solid #334155',
                             'color': '#fff', 'borderRadius': '8px'}),
            dbc.Button('SIGN IN →', id='login-btn', color='success',
                       className='w-100 mb-3', style={'fontWeight': '700'}),
            html.Div(id='login-error', style={'color': '#ef4444', 'fontSize': '13px',
                                               'textAlign': 'center'}),
            html.P(['Demo: ', html.Span('admin / nalco123',
                    style={'color': '#00d4aa', 'fontFamily': 'monospace'})],
                   style={'textAlign': 'center', 'fontSize': '12px',
                          'color': '#64748b', 'marginTop': '12px'})
        ], style={
            'background': '#1e293b', 'border': '1px solid #334155',
            'borderRadius': '16px', 'padding': '44px 40px',
            'width': '380px', 'boxShadow': '0 0 40px rgba(0,212,170,0.08)'
        })
    ], style={
        'minHeight': '100vh', 'display': 'flex',
        'alignItems': 'center', 'justifyContent': 'center',
        'background': '#0f172a'
    })
])

# ── Dashboard page ──────────────────────────────────────────
dashboard_layout = html.Div([

    # Top bar
    dbc.Navbar([
        dbc.Container([
            html.Span('NALCO', style={
                'color': '#00d4aa', 'fontFamily': 'monospace',
                'fontSize': '13px', 'letterSpacing': '2px', 'marginRight': '14px'
            }),
            html.Span('Network Performance Dashboard — 30 Day Report',
                      style={'color': '#e2e8f0', 'fontSize': '15px', 'fontWeight': '500'}),
            dbc.NavbarToggler(id='navbar-toggler'),
            html.Div([
                html.Span('● LIVE', style={
                    'color': '#00d4aa', 'fontSize': '11px',
                    'fontFamily': 'monospace', 'marginRight': '20px'
                }),
                dbc.Button('LOGOUT', id='logout-btn', size='sm', outline=True,
                           color='danger', style={'fontFamily': 'monospace',
                                                   'fontSize': '11px'})
            ], style={'marginLeft': 'auto', 'display': 'flex', 'alignItems': 'center'})
        ], fluid=True, style={'display': 'flex', 'alignItems': 'center', 'width': '100%'})
    ], dark=True, style={'background': '#1e293b',
                          'borderBottom': '1px solid #334155'}),

    # Main content
    dbc.Container([

        # Department filter
        html.Div([
            html.Label('Filter by Severity:', style={
                'color': '#94a3b8', 'fontSize': '12px',
                'textTransform': 'uppercase', 'letterSpacing': '1px',
                'marginBottom': '6px'
            }),
            dcc.Dropdown(
                id='severity-filter',
                options=[{'label': s, 'value': s}
                         for s in ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'OK']],
                value='ALL',
                clearable=False,
                style={'background': '#1e293b', 'color': '#000',
                       'borderRadius': '8px', 'width': '220px'}
            )
        ], style={'margin': '20px 0 10px'}),

        # KPI Cards
        html.P('KEY PERFORMANCE INDICATORS', style={
            'color': '#475569', 'fontSize': '11px',
            'letterSpacing': '2px', 'marginBottom': '12px'
        }),
        dbc.Row([
            kpi_card('Total Devices',    total_devices,    '#3b82f6', '🖥️'),
            kpi_card('Total Downtime',   f'{total_downtime} min', '#ef4444', '⏱️'),
            kpi_card('Avg Availability', f'{avg_availability}%',  '#00d4aa', '📶'),
            kpi_card('Critical Devices', critical_devices, '#f97316', '⚠️'),
        ]),

        # Charts row 1
        html.P('DOWNTIME ANALYSIS', style={
            'color': '#475569', 'fontSize': '11px',
            'letterSpacing': '2px', 'margin': '8px 0 12px'
        }),
        dbc.Row([
            dbc.Col(html.Div(
                dcc.Graph(figure=fig_bar, config={'displayModeBar': False}),
                style=CARD_STYLE), md=8),
            dbc.Col(html.Div(
                dcc.Graph(figure=fig_pie, config={'displayModeBar': False}),
                style=CARD_STYLE), md=4),
        ]),

        # Charts row 2
        dbc.Row([
            dbc.Col(html.Div(
                dcc.Graph(figure=fig_line, config={'displayModeBar': False}),
                style=CARD_STYLE), md=8),
            dbc.Col(html.Div(
                dcc.Graph(figure=fig_breaks, config={'displayModeBar': False}),
                style=CARD_STYLE), md=4),
        ]),

        # Scatter chart
        dbc.Row([
            dbc.Col(html.Div(
                dcc.Graph(figure=fig_scatter, config={'displayModeBar': False}),
                style=CARD_STYLE), md=12),
        ]),

        # Device Table
        html.P('DEVICE DETAILS', style={
            'color': '#475569', 'fontSize': '11px',
            'letterSpacing': '2px', 'margin': '8px 0 12px'
        }),
        html.Div([
            dash_table.DataTable(
                id='device-table',
                columns=[
                    {'name': 'Device Name',      'id': 'Clean_Name'},
                    {'name': 'IP Address',        'id': 'Device_IP'},
                    {'name': 'Availability %',    'id': 'Availability_Percent'},
                    {'name': 'Max Downtime (min)','id': 'Max_Downtime_Min'},
                    {'name': 'Total Downtime',    'id': 'Total_Downtime_Min'},
                    {'name': 'Breaks > 60 min',  'id': 'GT_60_Count'},
                    {'name': 'Severity',          'id': 'Severity'},
                ],
                data=df[[
                    'Clean_Name', 'Device_IP', 'Availability_Percent',
                    'Max_Downtime_Min', 'Total_Downtime_Min',
                    'GT_60_Count', 'Severity'
                ]].to_dict('records'),
                sort_action='native',
                filter_action='native',
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': '#0f172a',
                    'color': '#94a3b8',
                    'fontWeight': '600',
                    'fontSize': '11px',
                    'textTransform': 'uppercase',
                    'letterSpacing': '1px',
                    'border': '1px solid #334155'
                },
                style_cell={
                    'backgroundColor': '#1e293b',
                    'color': '#e2e8f0',
                    'border': '1px solid #334155',
                    'fontSize': '13px',
                    'padding': '10px 14px',
                    'fontFamily': 'sans-serif'
                },
                style_data_conditional=[
                    {'if': {'filter_query': '{Severity} = "CRITICAL"',
                            'column_id': 'Severity'},
                     'color': '#ef4444', 'fontWeight': '700'},
                    {'if': {'filter_query': '{Severity} = "HIGH"',
                            'column_id': 'Severity'},
                     'color': '#f97316', 'fontWeight': '700'},
                    {'if': {'filter_query': '{Severity} = "MEDIUM"',
                            'column_id': 'Severity'},
                     'color': '#eab308', 'fontWeight': '700'},
                    {'if': {'filter_query': '{Severity} = "LOW"',
                            'column_id': 'Severity'},
                     'color': '#3b82f6', 'fontWeight': '700'},
                    {'if': {'filter_query': '{Severity} = "OK"',
                            'column_id': 'Severity'},
                     'color': '#22c55e', 'fontWeight': '700'},
                    {'if': {'row_index': 'odd'},
                     'backgroundColor': '#172033'},
                ]
            )
        ], style=CARD_STYLE),

        html.Div(style={'height': '40px'})

    ], fluid=True, style={'background': '#0f172a', 'minHeight': '100vh'})

], style={'background': '#0f172a', 'minHeight': '100vh'})

# ============================================================
# STEP 6 — APP LAYOUT WITH LOGIN ROUTING
# ============================================================

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='login-state', data=False),
    html.Div(id='page-content')
])

# ============================================================
# STEP 7 — CALLBACKS (the interactive parts)
# ============================================================

# Show login or dashboard based on login state
@app.callback(
    Output('page-content', 'children'),
    Input('login-state', 'data')
)
def display_page(logged_in):
    if logged_in:
        return dashboard_layout
    return login_layout

# Handle login button click
@app.callback(
    Output('login-state', 'data'),
    Output('login-error', 'children'),
    Input('login-btn', 'n_clicks'),
    Input('password', 'n_submit'),
    [dash.State('username', 'value'),
     dash.State('password', 'value'),
     dash.State('login-state', 'data')],
    prevent_initial_call=True
)
def handle_login(n_clicks, n_submit, username, password, current_state):
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        return True, ''
    return False, 'Invalid username or password. Try admin / nalco123'

# Handle logout
@app.callback(
    Output('login-state', 'data', allow_duplicate=True),
    Input('logout-btn', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    return False

# Filter table by severity
@app.callback(
    Output('device-table', 'data'),
    Input('severity-filter', 'value')
)
def filter_table(severity):
    if severity == 'ALL':
        filtered = df
    else:
        filtered = df[df['Severity'] == severity]
    return filtered[[
        'Clean_Name', 'Device_IP', 'Availability_Percent',
        'Max_Downtime_Min', 'Total_Downtime_Min',
        'GT_60_Count', 'Severity'
    ]].to_dict('records')

# ============================================================
# STEP 8 — RUN THE APP
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    