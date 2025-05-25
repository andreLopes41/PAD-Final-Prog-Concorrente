import websockets
import json
import asyncio
import time
import matplotlib.pyplot as plt
from datetime import datetime

async def executar_busca(termos, porta, max_tentativas=3):
    """
    Executa uma busca usando o websocket especificado
    """
    uri = f"ws://localhost:{porta}"
    tentativa = 0
    
    while tentativa < max_tentativas:
        try:
            async with websockets.connect(
                uri,
                ping_interval=None,
                ping_timeout=None,
                close_timeout=None,
                max_size=None
            ) as websocket:
                dados_busca = [{
                    'termos': ';'.join(termos),
                    'loja': 'steam'
                }]
                
                tempo_inicial = time.time()
                
                await websocket.send(json.dumps(dados_busca))
                
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        if data['tipo'] == 'busca_concluida':
                            tempo_total = time.time() - tempo_inicial
                            return tempo_total
                except websockets.exceptions.ConnectionClosedError:
                    print(f"Conexão fechada inesperadamente. Tentativa {tentativa + 1} de {max_tentativas}")
                    tentativa += 1
                    if tentativa < max_tentativas:
                        await asyncio.sleep(2)
                    continue
                
        except Exception as e:
            print(f"Erro ao conectar: {str(e)}. Tentativa {tentativa + 1} de {max_tentativas}")
            tentativa += 1
            if tentativa < max_tentativas:
                await asyncio.sleep(2)
            continue
    
    raise Exception(f"Falha após {max_tentativas} tentativas")

async def comparar_tempos(termos_teste):
    """
    Compara os tempos de execução entre os scrapers serial e concorrente
    """
    resultados = {
        'Serial': [],
        'Concorrente': []
    }
    
    for termos in termos_teste:
        print(f"\nTestando busca com termos: {', '.join(termos)}")
        
        try:
            print("Executando scraper serial...")
            tempo_serial = await executar_busca(termos, 8766)
            resultados['Serial'].append(tempo_serial)
            print(f"Tempo serial: {tempo_serial:.2f} segundos")
            
            await asyncio.sleep(5)
            
            print("Executando scraper concorrente...")
            tempo_concorrente = await executar_busca(termos, 8765)
            resultados['Concorrente'].append(tempo_concorrente)
            print(f"Tempo concorrente: {tempo_concorrente:.2f} segundos")
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Erro ao executar teste com {len(termos)} termos: {str(e)}")
            resultados['Serial'].append(0)
            resultados['Concorrente'].append(0)
    
    return resultados

def gerar_grafico(resultados, termos_teste):
    """
    Gera um gráfico comparando os tempos de execução
    """
    plt.figure(figsize=(12, 6))
    
    x = range(len(termos_teste))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], resultados['Serial'], width, label='Serial', color='#ff7f0e')
    plt.bar([i + width/2 for i in x], resultados['Concorrente'], width, label='Concorrente', color='#1f77b4')
    
    plt.xlabel('Conjunto de Termos')
    plt.ylabel('Tempo de Execução (segundos)')
    plt.title('Comparação de Tempo de Execução: Serial vs Concorrente')
    plt.legend()
    
    plt.xticks(x, [f"Teste {i+1}\n({len(termos)} termos)" for i, termos in enumerate(termos_teste)])
    
    for i in x:
        if resultados['Serial'][i] > 0: 
            plt.text(i - width/2, resultados['Serial'][i], f"{resultados['Serial'][i]:.1f}s", 
                    ha='center', va='bottom')
        if resultados['Concorrente'][i] > 0:
            plt.text(i + width/2, resultados['Concorrente'][i], f"{resultados['Concorrente'][i]:.1f}s", 
                    ha='center', va='bottom')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f'comparacao_tempos_{timestamp}.png')
    print(f"\nGráfico salvo como: comparacao_tempos_{timestamp}.png")

async def main():
    termos_teste = [
        ['minecraft'],  
        ['minecraft', 'among us'],  
        ['minecraft', 'among us', 'grand theft auto v'], 
        ['minecraft', 'among us', 'grand theft auto v', 'far cry 4'],  
        ['minecraft', 'among us', 'grand theft auto v', 'far cry 4', 'god of war']
    ]
    
    print("Iniciando comparação de tempos...")
    resultados = await comparar_tempos(termos_teste)
    
    print("\nGerando gráfico...")
    gerar_grafico(resultados, termos_teste)

if __name__ == "__main__":
    asyncio.run(main())