import scrapy
import os
from google.cloud import bigquery
import uuid

# Arquivo de credenciais do BigQuery, colocar o caminho com \\ do arquivo json de credencial.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\Wilson Roberto\\case-scrapy-0b2fb302ba37.json"

# Classe do BigQueryClient para fazer a conexao com BigQuery com a funcao de inserir os registros na tabela
class BigQueryClient:
    def __init__(self, project_id):
        self.client = bigquery.Client(project=project_id)

    def insert_row(self, dataset_id, table_id, row):
        table_ref = f"{self.client.project}.{dataset_id}.{table_id}"  
        errors = self.client.insert_rows_json(table_ref, [row])
        if errors:
            print("Ocorreram erros ao inserir as linhas:", errors)



# Classe onde todo o processo de webscrapping é realizado
class GuardianArticleSpider(scrapy.Spider):
# São os links das materias que foram inseridas na tabela. Rodar um link por vez, em matérias do the guardian.     
    name = 'guardian_article'
    start_urls = ['https://www.theguardian.com/world/2024/oct/07/israeli-troop-reinforcements-cast-doubt-over-limited-lebanon-invasion']
    #start_urls = ['https://www.theguardian.com/us-news/2024/oct/06/harris-media-whirlwind-trump-battleground-states'] 
    #start_urls = ['https://www.theguardian.com/world/2024/oct/08/zelenskyy-victory-plan-summit-in-doubt-after-joe-biden-pulls-out'] 
    #start_urls = ['https://www.theguardian.com/world/2024/oct/08/mexico-murder-beheading-city-mayor-alejandro-arcos-catalan-chilpancingo']
    #start_urls = ['https://www.theguardian.com/world/2024/oct/08/son-of-god-pastor-apollo-quiboloy-registers-jail-philippines-state-election']



# Adicao do User agent é usada para definir o identificador do navegador que seu crawler se apresenta ao acessar sites. 
# AUTOTHROTTLE_ENABLED ajusta automaticamente a velocidade das requisições para evitar sobrecarregar o servidor que você está acessando e para minimizar a possibilidade de ser bloqueado.
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'AUTOTHROTTLE_ENABLED': True
    }

    def __init__(self, *args, **kwargs):
        super(GuardianArticleSpider, self).__init__(*args, **kwargs)
        # Inicialize o cliente do BigQuery
        self.bq_client = BigQueryClient('case-scrapy')  # Substitua pelo seu ID do projeto
        self.dataset_id = 'bd_case'  # Substitua pelo seu ID do dataset
        self.table_id = 'tb_case'       # Substitua pelo seu ID da tabela

    def parse(self, response):
        # Extraindo o titulo do artigo na classe h1 e pega o texto contido e tirando espaços
        title = response.css('h1::text').get(default='Título não encontrado').strip()
        # O autor do artigo está na classe .dcr-1cfpnlw pegando o texto ou o texto do span e tirando espaços
        author = response.css('.dcr-1cfpnlw a::text, .dcr-1cfpnlw span::text').get(default='Autor não encontrado').strip()
        # A url do artigo sendo acessada
        article_url = response.url
        
        # O texto do artigo está dentro do article e extraiu o texto dos <p> paragrafo e <a> descricao dos links
        paragraphs = response.css('article p::text, article a::text').getall()
        
        #Sao as partes da pagina do artigo que devem ser ignoradas para que a extracao seja bem sucedida
        ignored_content = response.css(
             '.dcr-16lnb0w p::text, .dcr-16lnb0w a::text,'
             'figure *::text, '
             'figure[data-spacefinder-role="inline"] *::text, '
             'figure[data-spacefinder-role="richLink"] *::text,'
             '.dcr-1cfpnlw a::text,'
             '.dcr-zhx6xs a::text'
        ).getall()

        #Mais uns termos a serem ignorados
        specific_ignored_texts = ['Sign up to']
        ignored_content.extend(specific_ignored_texts)

        # A primeira linha filtra os paragrafos, removendo aqueles que estao na lista de conteudos indesejados.
        # A segunda linha junta os paragrafos restantes em uma unica string, representando o texto do artigo, com espacos apropriados entre as partes.
        paragraphs = [text for text in paragraphs if text.strip() not in ignored_content]
        article_text = ' '.join(paragraphs).strip()

        # Retirar excesso de espacos que aparecem
        article_text = article_text.replace("  ", " ")
        article_text = article_text.replace(" . " , ". ")


        # Removendo mais alguns termos que aparecem no fim da pagina e nao sao necessarios
        links_texts = response.css('.dcr-1jl528t a::text').getall()
        joined_links = ' '.join(links_texts)
        article_text = article_text.replace(joined_links, '').strip()

        # Essa linha de codigo esta criando um dicionario que contem as informacoes relevantes de um artigo (com um ID unico), e usando yield para retornar esse dicionario.
        # Permite extrair o arquivo JSON com os dados
        # str(uuid.uuid4()) - gera uma chave primaria aleatoria para os artigos
        yield {
            'id': str(uuid.uuid4()),
            'titulo': title,
            'autor': author,
            'url': article_url,
            'texto': article_text,
        }

        # Criar o dicionario de dados a serem inseridos no BigQuery
        row = {
            'id': str(uuid.uuid4()),
            'titulo': title,
            'autor': author,
            'url': article_url,
            'texto': article_text,
        }

        # Insere os dados no BigQuery
        self.bq_client.insert_row(self.dataset_id, self.table_id, row)



