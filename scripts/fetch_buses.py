#!/usr/bin/env python3
"""
Fetcher genérico para a Atividade 2 — posições de ônibus.

Uso básico:
  python scripts\fetch_buses.py --url "https://api.exemplo/veiculos" --line 10 --out data/bus_positions.json

Se a API requer token, passe `--token TOKEN` (será enviado como header Authorization: Bearer TOKEN).

O script tenta extrair lat/lon de campos comuns nas respostas JSON ("lat","lon","latitude","longitude","y","x").
Ele grava um array JSON com objetos: {"id":..., "line":..., "lat":..., "lon":...}

Adapte os parâmetros ou a função `extract_vehicles` se sua API usar formato diferente.
"""
import argparse
import requests
import json
import sys
import os
from typing import List, Dict, Any


def load_dotenv(path: str = '.env') -> None:
    """Carrega variáveis de um arquivo .env simples para os.environ.
    Formato: KEY=VALUE, linhas começando com # são comentários.
    Não depende de python-dotenv para manter a solução leve.
    """
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith('#'):
                    continue
                if '=' not in ln:
                    continue
                k, v = ln.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        # não falhar se houver problema lendo o arquivo
        return


def extract_vehicles(j: Any, line_param: str = None) -> List[Dict[str, Any]]:
    """Tenta normalizar uma resposta JSON em uma lista de veículos com lat/lon.
    Procura por objetos com campos comuns e retorna lista com keys: id, line, lat, lon
    """
    candidates = []

    # navega para a lista caso a resposta seja do tipo { 'vehicles': [...] }
    if isinstance(j, dict):
        # Heurística: prefer keys que contenham 'vehicle' ou 'veiculo' ou 'data'
        for k in ('vehicles','veiculos','data','result','items'):
            if k in j and isinstance(j[k], list):
                j = j[k]
                break

    if not isinstance(j, list):
        return []

    for item in j:
        if not isinstance(item, dict):
            continue
        lat = None
        lon = None
        # check common names
        for lk in ('lat','latitude','y'):
            if lk in item and item[lk] not in (None, ''):
                lat = float(item[lk])
                break
        for lk in ('lon','lng','longitude','x'):
            if lk in item and item[lk] not in (None, ''):
                lon = float(item[lk])
                break

        # fallback: sometimes coordinates are nested
        if (lat is None or lon is None) and 'location' in item and isinstance(item['location'], dict):
            loc = item['location']
            if 'lat' in loc and 'lon' in loc:
                lat = float(loc['lat']); lon = float(loc['lon'])

        if lat is None or lon is None:
            # try to find numeric values in the dict values (last resort)
            nums = [v for v in item.values() if isinstance(v, (int,float))]
            if len(nums) >= 2:
                lat, lon = float(nums[0]), float(nums[1])

        if lat is None or lon is None:
            continue

        vid = item.get('id') or item.get('vehicleId') or item.get('veiculoId') or item.get('placa') or ''
        vline = item.get('line') or item.get('linha') or line_param or ''
        candidates.append({'id': str(vid), 'line': str(vline), 'lat': lat, 'lon': lon})

    return candidates


def main():
    # carrega .env (se existir) para BUS_API_URL, BUS_API_TOKEN
    load_dotenv('.env')

    p = argparse.ArgumentParser()
    p.add_argument('--url', required=False, help='Endpoint da API que retorna posições (JSON). Opcional se BUS_API_URL estiver em .env')
    p.add_argument('--line', required=False, help='Linha de ônibus (opcional)')
    p.add_argument('--token', required=False, help='Token (Bearer) se necessário')
    p.add_argument('--out', default='data/bus_positions.json', help='Arquivo de saída JSON')
    p.add_argument('--params', nargs='*', help='Parâmetros extras para querystring key=value')
    args = p.parse_args()

    # Prioridade: argumento CLI > variáveis de ambiente
    url = args.url or os.environ.get('BUS_API_URL')
    token = args.token or os.environ.get('BUS_API_TOKEN')

    if not url:
        print('URL da API não fornecida. Passe --url ou defina BUS_API_URL no .env', file=sys.stderr)
        sys.exit(2)

    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    params = {}
    if args.params:
        for kv in args.params:
            if '=' in kv:
                k, v = kv.split('=', 1)
                params[k] = v

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        j = resp.json()
    except Exception as e:
        print('Erro ao acessar API:', e, file=sys.stderr)
        sys.exit(2)

    vehicles = extract_vehicles(j, line_param=args.line)
    if not vehicles:
        print('Nenhum veículo extraído automaticamente. Verifique o formato da resposta ou adapte extract_vehicles().', file=sys.stderr)

    # salva apenas os campos desejados
    out = [{'id': v['id'], 'line': v['line'], 'lat': v['lat'], 'lon': v['lon']} for v in vehicles]
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('Posições salvas em', args.out)


if __name__ == '__main__':
    main()
