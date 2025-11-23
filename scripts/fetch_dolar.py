#!/usr/bin/env python3
"""
Script de suporte para Atividade 1.
Uso: python scripts/fetch_dolar.py MMYYYY

O script:
- Constrói data inicial e final para o mês recebido.
- Consulta a API PTAX (BCB) para o período.
- Converte resposta para série diária e preenche dias sem cotação usando o último dia útil disponível.
- Salva JSON em data/dolar_MMYYYY.json com formato: [{"date": "YYYY-MM-DD", "value": 5.1234}, ...]

Obs: Requer as bibliotecas: requests, pandas
Instale com: pip install requests pandas
"""
import sys
import calendar
from datetime import datetime, timedelta
import os
import requests
import pandas as pd

def month_dates(mmYYYY: str):
    first = datetime.strptime(mmYYYY, "%m%Y")
    last_day = calendar.monthrange(first.year, first.month)[1]
    first_date = first.replace(day=1)
    last_date = first.replace(day=last_day)
    return first_date, last_date

def fetch_bcb(first_date: datetime, last_date: datetime):
    # A API OData do BCB (PTAX) aceita datas no formato dd-MM-YYYY
    di = first_date.strftime('%d-%m-%Y')
    df = last_date.strftime('%d-%m-%Y')
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarPeriodo(dataInicial='{di}',dataFinal='{df}')?$top=10000&$format=json"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    # Estrutura: j['value'] é lista de objetos com 'cotacaoCompra','cotacaoVenda','dataHora'...
    return j.get('value', [])

def to_daily_series(values, first_date, last_date):
    # Construir DataFrame com data e valor médio (ou cotacaoVenda)
    rows = []
    for item in values:
        # A API retorna campo 'dataHora' como "2021-08-02 00:00:00"
        dh = item.get('dataHora') or item.get('dataHoraCotacao') or item.get('timestamp')
        if not dh:
            continue
        date = pd.to_datetime(dh).date()
        # usar 'cotacaoVenda' se disponível, senão 'cotacaoCompra'
        val = item.get('cotacaoVenda') if item.get('cotacaoVenda') is not None else item.get('cotacaoCompra')
        if val is None:
            continue
        rows.append({'date': pd.to_datetime(date), 'value': float(val)})

    if not rows:
        return pd.DataFrame(columns=['date','value'])

    df = pd.DataFrame(rows).drop_duplicates(subset='date').set_index('date').sort_index()

    # construir índice diário completo e preencher usando método ffill (último dia útil)
    full_idx = pd.date_range(first_date.date(), last_date.date(), freq='D')
    df = df.reindex(full_idx)
    df['value'] = df['value'].ffill()
    df.index.name = 'date'
    return df.reset_index()

def save_json(df, mmYYYY):
    os.makedirs('data', exist_ok=True)
    out = f'data/dolar_{mmYYYY}.json'
    payload = [{'date': row['date'].strftime('%Y-%m-%d'), 'value': round(float(row['value']), 6)} for _, row in df.iterrows()]
    import json
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print('Arquivo gerado:', out)

def main():
    if len(sys.argv) < 2:
        print('Uso: python scripts/fetch_dolar.py MMYYYY')
        sys.exit(1)
    mmYYYY = sys.argv[1]
    first_date, last_date = month_dates(mmYYYY)
    print('Buscando dados de', first_date.date(), 'até', last_date.date())
    values = fetch_bcb(first_date, last_date)
    df = to_daily_series(values, first_date, last_date)
    if df.empty:
        print('Nenhum dado retornado da API para o período.')
        sys.exit(2)
    save_json(df, mmYYYY)

if __name__ == '__main__':
    main()
