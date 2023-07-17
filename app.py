from dash import Dash, html, dcc, dash_table
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import requests
from datetime import datetime



def req_form(url):
    header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"  
    }

    r = requests.get(url, headers=header)

    #na tabela do site fundamentus o decimal é colocado como virgula
    df = pd.read_html(r.text,  decimal=',', thousands='.')[0] 
    return df

def limpeza(df):
    for coluna in ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'ROIC', 'ROE', 'Cresc. Rec.5a']:
        df[coluna] = df[coluna].str.replace('.', '')
        df[coluna] = df[coluna].str.replace(',', '.')
        df[coluna] = df[coluna].str.rstrip('%').astype('float') / 100
    return df

def filtros(df):
    df = df[df['Liq.2meses'] > 1000000]
    filtro = df['ROIC'] > 0.0
    df = df[filtro]
    filtro = df['Mrg. Líq.'] > 0.05
    df = df[filtro]
    filtro = df['P/L'] > 3.0
    df = df[filtro]
    filtro = df['ROE'] > 0.0
    df = df[filtro]
    filtro = df['EV/EBIT'] > 0.0
    df = df[filtro]
    return df

def criacaoRankings(df,num_acoes):
    ranking_a = pd.DataFrame()
    ranking_a['pos_EBIT'] = range(1,num_acoes)
    ranking_b = pd.DataFrame()
    ranking_b['pos_ROIC'] = range(1,num_acoes)

    #Este múltiplo compara o valor da empresa com o lucro antes de impostos e taxas (Ebit).
    #EV/EBIT maior que zero - > Só lucro operacional positivo

    ranking_a['Papel'] = df.sort_values(by=['EV/EBIT'])['Papel'][:(num_acoes-1)].values
    ranking_a['EV/EBIT %'] = df.sort_values(by=['EV/EBIT'], ascending=True)['EV/EBIT'][:(num_acoes-1)].values

    '''ROIC - Return on Invested Capital
    significa o RETORNO SOBRE CAPITAL INVESTIDO. Na prática, ele informa quanto de dinheiro uma empresa consegue 
    gerar em razão de todo o capital investido, incluindo os aportes por meio de dívidas.
    '''

    ranking_b['Papel'] = df.sort_values(by=['ROIC'], ascending=False)['Papel'][:(num_acoes-1)].values
    ranking_b['ROIC Value'] = df.sort_values(by=['ROIC'], ascending=False)['ROIC'][:(num_acoes-1)].values

    return ranking_a,ranking_b

#filtro de ações duplicadas
def retirar_duplicados(rank):
    Ticker = rank['Papel'].str.extract(r'([A-Z]{4})')
    rank["Ticker"] = Ticker
    rank.set_index("Ticker",inplace=True)
    rank = rank[~rank.index.duplicated(keep='first')]
    rank.reset_index(inplace=True)
    rank.index = rank.index + 1
    rank.drop('Ticker',axis=1,inplace=True)
    return rank
#filtro de ações financeiras
def retirar_financeiros(rank):
    financeiros = ['PSSA3', 'BBDC4','SANB11', 'BBAS4','BBSE4','ITSA4','ITUB3','ITUB3','WIZC3', 'ABCB3', 'ABCB4']
    for f in financeiros:
        rank = rank[rank.Papel != f]
    rank.reset_index(inplace=True)
    rank.index = rank.index + 1
    rank.drop('index',axis=1,inplace=True)
    return rank


def magicFormula(r_ebit,r_roic):
    ranking = pd.merge(r_ebit,r_roic)
    ranking['pts'] = ranking["pos_EBIT"] + ranking["pos_ROIC"]

    rank = ranking.sort_values('pts')
    rank = rank[["Papel","EV/EBIT %","ROIC Value","pts"]]
    rank = retirar_duplicados(rank)
    rank = retirar_financeiros(rank)

    return rank

url = 'http://www.fundamentus.com.br/resultado.php'

df = req_form(url)
df = limpeza(df)
df = filtros(df)

#RANKINGS
num_acoes = df.shape[0]
r_ebit,r_roic = criacaoRankings(df,num_acoes)



#POSIÇÕES DO MAGIC FORMULA
rank_magic_formula = magicFormula(r_ebit,r_roic)
print('NÃO É UMA RECOMENDAÇÃO DE COMPRA\n',rank_magic_formula.head(20))

top20 = rank_magic_formula[:20]

app = Dash(__name__)

app.layout = html.Div ([
    html.Label('NÃO É UMA RECOMENDAÇÃO DE COMPRA'),
    html.Label(' Data:{data}'.format(data = datetime.today().strftime('%d-%m-%Y'))),
    dash_table.DataTable(
        id = 'tabela',
        data = top20.to_dict('records'), 
        columns= [{"name": i, "id": i} for i in top20.columns],
    ),
])

app.run(debug=True)
# Salvar no CSV
'''
import csv
from datetime import datetime

data = datetime.today().strftime('%d-%m-%Y')
# abrindo o arquivo para escrita
rank.head(10).to_csv('EV-EBIT - ROIC Historico/magic_formula_{}.csv'.format(data))
'''