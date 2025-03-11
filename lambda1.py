import boto3
import requests
from datetime import datetime
from urllib.parse import urlencode

def download_mitula_pages(event, context):
    bucket_name = "mitula10"
    base_url = "https://casas.mitula.com.co/find"
    s3 = boto3.client("s3")
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    
    for page in range(1, 11):  # Descargar las primeras 10 páginas
        params = {
            "operationType": "sell",
            "propertyType": "mitula_studio_apartment",
            "geoId": "mitula-CO-poblacion-0000014156",
            "text": "Bogotá,  (Cundinamarca)",
            "page": page
        }
        url = f"{base_url}?{urlencode(params)}"
        
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code == 200:
            file_key = f"landing-casas/{today}/page_{page}.html"
            s3.put_object(Bucket=bucket_name, Key=file_key, Body=response.text, ContentType="text/html")
            print(f"Guardado: s3://{bucket_name}/{file_key}")
        else:
            print(f"Error al descargar {url}: {response.status_code}")
    
    return {"status": "success"}
