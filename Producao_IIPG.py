import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
import os

# URL do arquivo XLSX no GitHub
url = 'https://github.com/JacoLucas/ProducaoIIPG/raw/main/Produção IIPG.xlsx'

# Lê os dados da planilha Excel a partir do GitHub
response = requests.get(url)
if response.status_code == 200:
    df = pd.read_excel(BytesIO(response.content), sheet_name='Para Código', engine='openpyxl')
else:
    raise Exception("Falha ao baixar o arquivo do GitHub. Verifique a URL e tente novamente.")

# Verifique os nomes das colunas
print(df.columns)

# Remova espaços em branco dos nomes das colunas
df.columns = df.columns.str.strip()

# Converte a coluna 'Dias' para o formato de data
df['Dias'] = pd.to_datetime(df['Dias'], format='%d/%m/%Y')  # Ajuste o formato de data conforme necessário

# Extrai ano e mês dos dados
df['Ano_Mes'] = df['Dias'].dt.to_period('M')

# Renomeia as colunas para remover a palavra 'Produção'
df.rename(columns={
    'Produção CBUQ': 'CBUQ',
    'Produção Binder': 'Binder',
    'Produção BGS': 'BGS',
    'Produção BGTC': 'BGTC'
}, inplace=True)

# Inicializa o aplicativo Dash
app = dash.Dash(__name__)
app.title = 'Produção IIPG'

app.layout = html.Div([
    html.H1('Produção IIPG'),
    html.Div([
        html.Label('Selecione o Período:'),
        dcc.Dropdown(
            id='month-dropdown',
            options=[{'label': str(month), 'value': str(month)} for month in df['Ano_Mes'].unique()],
            value=str(df['Ano_Mes'].unique()[0])
        )
    ], style={'width': '33%', 'display': 'inline-block', 'margin-bottom': '20px'}),
    html.Div([
        dcc.Graph(id='line-chart', style={'width': '100%', 'display': 'inline-block'})
    ]),
    html.Div([
        dcc.Graph(id='bar-chart', style={'width': '60%', 'display': 'inline-block'}),
        dcc.Graph(id='pie-chart', style={'width': '40%', 'display': 'inline-block'})
    ]),
    html.Div([
        html.H2('Produção USA e USS'),
        html.Div([
            html.Label('Selecione a Usina:'),
            dcc.Dropdown(
                id='unit-dropdown',
                options=[
                    {'label': 'USA', 'value': 'USA'},
                    {'label': 'USS', 'value': 'USS'}
                ],
                value='USA',
                clearable=False
            )
        ], style={'width': '33%', 'margin-bottom': '20px'}),
        dcc.Graph(id='usa-uss-chart', style={'width': '100%', 'display': 'inline-block'})
    ], style={'margin-top': '20px'})
])

@app.callback(
    [Output('line-chart', 'figure'),
     Output('bar-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('usa-uss-chart', 'figure')],
    [Input('month-dropdown', 'value'),
     Input('unit-dropdown', 'value')]
)
def update_charts(selected_month, selected_unit):
    filtered_df = df[df['Ano_Mes'] == selected_month]
    
    # Mapa de cores
    color_map = {
        'Pó de Pedra': '#006699',
        'Pedrisco': '#660099',
        'Brita 1': '#990033',
        'Brita 2': '#FFCC00'
    }
    
    # Gráfico de linha
    fig_line = px.line(filtered_df, x='Dias', y='Produção Primário', title='Sistema Primário', line_shape='linear')
    fig_line.update_traces(line=dict(color='#006699'))
    fig_line.update_layout(
        xaxis_title='Período',
        yaxis_title='Produção (ton.)'
    )
    
    # Gráfico de barras horizontais
    data = {
        'Material': ['Pó de Pedra', 'Pedrisco', 'Brita 1', 'Brita 2'],
        'Produção (ton.)': filtered_df[['Pó de Pedra', 'Pedrisco', 'Brita 1', 'Brita 2']].sum().values
    }
    bar_df = pd.DataFrame(data)
    fig_bar = px.bar(
        bar_df,
        x='Produção (ton.)',
        y='Material',
        orientation='h',
        title='Sistema Secundário',
        color='Material',
        color_discrete_map=color_map
    )
    fig_bar.update_layout(
        xaxis_title='Produção (ton.)',
        yaxis_title='Material',
        showlegend=False
    )
    
    # Gráfico de pizza
    fig_pie = px.pie(
        bar_df,
        values='Produção (ton.)',
        names='Material',
        title='Distribuição de Materiais',
        color='Material',
        color_discrete_map=color_map
    )
    fig_pie.update_traces(
        showlegend=False,
        hoverinfo='label+percent+value'
    )
    
    # Gráfico de linha para USA e USS
    if selected_unit == 'USA':
        usa_uss_data = filtered_df.melt(id_vars=['Dias'], value_vars=['CBUQ', 'Binder'], var_name='Material', value_name='Produção (ton.)')
        fig_usa_uss = px.line(
            usa_uss_data,
            x='Dias',
            y='Produção (ton.)',
            color='Material',
            title='Produção USA e USS',
            labels={'value': 'Produção (ton.)', 'variable': 'Material'}
        )
        fig_usa_uss.update_traces(line=dict(color='#006699'), selector=dict(name='CBUQ'))
        fig_usa_uss.update_traces(line=dict(color='#FFCC00'), selector=dict(name='Binder'))
    else:
        usa_uss_data = filtered_df.melt(id_vars=['Dias'], value_vars=['BGS', 'BGTC'], var_name='Material', value_name='Produção (ton.)')
        fig_usa_uss = px.line(
            usa_uss_data,
            x='Dias',
            y='Produção (ton.)',
            color='Material',
            title='Produção USA e USS',
            labels={'value': 'Produção (ton.)', 'variable': 'Material'}
        )
        fig_usa_uss.update_traces(line=dict(color='#006699'), selector=dict(name='BGS'))
        fig_usa_uss.update_traces(line=dict(color='#FFCC00'), selector=dict(name='BGTC'))
    fig_usa_uss.update_layout(
        xaxis_title='Período',
        yaxis_title='Produção (ton.)'
    )
    
    return fig_line, fig_bar, fig_pie, fig_usa_uss

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
