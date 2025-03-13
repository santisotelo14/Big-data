import json
import boto3
import logging
from bs4 import BeautifulSoup
from datetime import datetime

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_s3_object(bucket_name, file_key):
    """Descarga el contenido de un archivo desde S3."""
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    return response["Body"].read().decode("utf-8")

def extract_property_data(html_content):
    """Extrae información de propiedades desde HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    def extract_text(casa, class_name):
        elemento = casa.find(class_=class_name)
        return elemento.text.strip() if elemento else ""
    
    return [
        [
            datetime.today().strftime("%Y-%m-%d"),
            extract_text(casa, "barrio"),
            extract_text(casa, "precio"),
            extract_text(casa, "habitaciones"),
            extract_text(casa, "banos"),
            extract_text(casa, "metros-cuadrados"),
        ]
        for casa in soup.find_all(class_="property-card")
    ]

def save_to_s3(bucket_name, file_key, data):
    """Guarda datos en formato CSV en un bucket S3."""
    csv_content = "FechaDescarga,Barrio,Valor,NumHabitaciones,NumBanos,mts2\n"
    csv_content += "\n".join(",".join(row) for row in data)
    s3.put_object(Bucket=bucket_name, Key=file_key, Body=csv_content.encode("utf-8"))

def process_html(bucket_name, file_key):
    """Proceso completo de extracción y almacenamiento de datos desde un archivo HTML en S3."""
    if not file_key.startswith("landing-casas/") or not file_key.endswith(".html"):
        logger.warning(f"Formato de key inválido: {file_key}")
        return {"statusCode": 400, "body": "Formato de archivo no válido"}
    
    html_content = get_s3_object(bucket_name, file_key)
    data = extract_property_data(html_content)
    
    output_bucket = "casas-final"
    output_key = f"{datetime.today().strftime('%Y-%m-%d')}.csv"
    save_to_s3(output_bucket, output_key, data)
    
    logger.info(f"Archivo procesado y guardado en {output_bucket}/{output_key}")
    return {"statusCode": 200, "body": "Archivo procesado correctamente"}

def lambda_handler(event, context):
    """Manejador de eventos Lambda."""
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    file_key = event["Records"][0]["s3"]["object"]["key"]
    logger.info(f"Archivo recibido: {file_key}")
    return process_html(bucket_name, file_key)
