from flask import Flask, request, jsonify
from google.cloud import bigquery
import os
# Arquivo de credenciais do BigQuery, colocar o caminho com \\ do arquivo json de credencial.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\Wilson Roberto\\case-scrapy-0b2fb302ba37.json"

#API em Flask
app = Flask(__name__)
client = bigquery.Client(project='case-scrapy')  # Substitua pelo seu ID do projeto
dataset_id = 'bd_case'  # Substitua pelo seu ID do dataset
table_id = 'tb_case'     # Substitua pelo seu ID da tabela

#Home do app
@app.route('/')
def home():
    return "Use /search?keyword=seu_palavra-chave para buscar artigos."

#Define uma rota para a aplicação Flask. A rota /search responde a requisições do tipo GET
#Define a função search_articles, que é chamada quando alguém faz uma requisição para a rota /search.
#Adiciona a keyword digitada e busca no artigo
@app.route('/search', methods=['GET'])
def search_articles():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Keyword is required."}), 400
    
    #Query sql
    query = f"""
        SELECT id, titulo, autor, url, texto
        FROM `{client.project}.{dataset_id}.{table_id}`
        WHERE LOWER(texto) LIKE LOWER('%{keyword}%')
    """
    #Executa a query
    query_job = client.query(query)
    results = query_job.result()

    #Esse trecho cria uma lista de dicionários, onde cada dicionário representa um artigo encontrado, contendo as chaves id, titulo, autor, url e texto correspondentes a cada linha de resultado.
    articles = [{"id": row.id,
                "titulo": row.titulo, 
                "autor": row.autor, 
                "url": row.url, 
                "texto": row.texto
                }
                for row in results
    ]

    return jsonify(articles)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
