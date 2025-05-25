import asyncio
import websockets
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

PLATAFORMAS = {
    'steam': 'https://store.steampowered.com/search/?term='
}

def buscar_detalhes_jogo_steam(url):
    """
    Função que busca detalhes adicionais de um jogo na Steam
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data_element = soup.find('div', class_='date')
        data = data_element.text.strip() if data_element else "Data não disponível"
        
        publisher_element = soup.find('div', id='developers_list')
        publisher = publisher_element.text.strip() if publisher_element else "Distribuidora não disponível"
        
        return data, publisher
    except:
        return "Data não disponível", "Distribuidora não disponível"

def buscar_jogos_steam(termo):
    """
    Função que realiza o scraping na Steam
    """
    try:
        url = PLATAFORMAS['steam'] + quote(termo)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        jogos = []
        
        resultados = soup.find_all('a', class_='search_result_row')
        
        for item in resultados:
            try:
                nome = item.find('span', class_='title').text.strip()
                preco_element = item.find('div', class_='discount_final_price')
                preco = preco_element.text.strip() if preco_element else "Preço não disponível"
                
                img_element = item.find('img')
                imagem = img_element['src'] if img_element else ""
                
                data_lancamento, distribuidora = buscar_detalhes_jogo_steam(item['href'])
                
                jogos.append({
                    'nome': nome,
                    'plataforma': 'Steam',
                    'link': item['href'],
                    'imagem': imagem,
                    'lancamento': data_lancamento,
                    'distribuidora': distribuidora,
                    'preco': preco
                })
            except Exception as e:
                print(f"Erro ao processar jogo da Steam: {str(e)}")
                continue
                
        return jogos
    except Exception as e:
        print(f"Erro ao buscar na Steam: {str(e)}")
        return []

def buscar_jogos_plataforma(termo, plataforma):
    """
    Função que realiza o scraping em uma plataforma específica
    """
    try:
        if plataforma == 'steam':
            return buscar_jogos_steam(termo)
        else:
            print(f"Plataforma {plataforma} não suportada")
            return []
            
    except Exception as e:
        print(f"Erro ao buscar jogos na plataforma {plataforma}: {str(e)}")
        return []

async def websocket_handler(websocket, path):
    """
    Manipulador de conexões WebSocket
    """
    try:
        async for message in websocket:
            data = json.loads(message)
            
            todas_buscas = []
            for busca in data:
                termos = busca['termos'].split(';')
                plataforma = busca['loja']
                for termo in termos:
                    if termo.strip():
                        todas_buscas.append((termo.strip(), plataforma))
            
            total_termos = len(todas_buscas)
            termos_processados = 0
            
            # Processa cada busca sequencialmente
            for termo, plataforma in todas_buscas:
                try:
                    jogos = buscar_jogos_plataforma(termo, plataforma)
                    termos_processados += 1
                    
                    progresso_percentual = (termos_processados / total_termos) * 100
                    
                    resultado_parcial = {
                        'tipo': 'resultado_parcial',
                        'produtos': jogos,
                        'progresso': progresso_percentual
                    }
                    await websocket.send(json.dumps(resultado_parcial))
                    
                except Exception as e:
                    print(f"Erro ao processar resultado: {str(e)}")
                    termos_processados += 1
            
            await websocket.send(json.dumps({'tipo': 'busca_concluida'}))
            
    except websockets.exceptions.ConnectionClosed:
        print("Conexão fechada pelo cliente")
    except Exception as e:
        print(f"Erro no websocket_handler: {str(e)}")

async def main():
    """
    Função principal que inicia o servidor WebSocket
    """
    server = await websockets.serve(
        websocket_handler,
        "localhost",
        8766,
        ping_interval=None,
        ping_timeout=None,
        close_timeout=None
    )
    print("Servidor WebSocket Serial iniciado em ws://localhost:8766")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())