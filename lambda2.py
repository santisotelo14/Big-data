import json
import boto3
import logging
from bs4 import BeautifulSoup
from datetime import datetime

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    
    # Log del archivo recibido
    logger.info(f"Archivo recibido: {file_key}")
    
    # Validar que el archivo sea un HTML válido
    if not file_key.startswith("landing-casas/") or not file_key.endswith(".html"):
        logger.warning(f"Formato de key inválido: {file_key}")
        return {"statusCode": 400, "body": "Formato de archivo no válido"}
    
    # Descargar el archivo desde S3
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    html_content = response['Body'].read().decode('utf-8')
    
    # Procesar el HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraer información (esto debe ajustarse a la estructura del HTML)
    casas = []
    for casa in soup.find_all(class_='property-card'):
        barrio = casa.find(class_='barrio').text.strip() if casa.find(class_='barrio') else ""
        valor = casa.find(class_='precio').text.strip() if casa.find(class_='precio') else ""
        num_habitaciones = casa.find(class_='habitaciones').text.strip() if casa.find(class_='habitaciones') else ""
        num_banos = casa.find(class_='banos').text.strip() if casa.find(class_='banos') else ""
        mts2 = casa.find(class_='metros-cuadrados').text.strip() if casa.find(class_='metros-cuadrados') else ""
        
        casas.append([datetime.today().strftime('%Y-%m-%d'), barrio, valor, num_habitaciones, num_banos, mts2])
    
    # Guardar los datos en un archivo CSV en S3
    output_bucket = "casas-final-xxx"
    output_key = f"{datetime.today().strftime('%Y-%m-%d')}.csv"
    csv_content = "FechaDescarga,Barrio,Valor,NumHabitaciones,NumBanos,mts2\n"
    csv_content += "\n".join(",".join(row) for row in casas)
    
    s3.put_object(Bucket=output_bucket, Key=output_key, Body=csv_content.encode('utf-8'))
    
    logger.info(f"Archivo procesado y guardado en {output_bucket}/{output_key}")
    
    return {"statusCode": 200, "body": "Archivo procesado correctamente"}
