import os
import boto3
import csv
import json
from bs4 import BeautifulSoup
from datetime import datetime

S3_BUCKET_INPUT = os.getenv("S3_BUCKET_INPUT", "mitula10")
S3_BUCKET_OUTPUT = os.getenv("S3_BUCKET_OUTPUT", "casascsv")
s3_client = boto3.client("s3")

def extract_data_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    listings = []

    # Intentar encontrar listados con la estructura de producción
    elements = soup.find_all("div", class_="listing-card__properties")

    # Si no encuentra, intentar con la estructura de prueba
    if not elements:
        elements = soup.find_all("div", class_="listing-item")

    print(f"Listados encontrados: {len(elements)}")  # Log de depuración

    if not elements:
        print("No se encontraron listados en el HTML.")

    for listing in elements:
        # Intentar extraer con la estructura de producción
        barrio_tag = listing.find_previous("div", class_="listing-card__location__geo")
        barrio = barrio_tag.text.strip() if barrio_tag else None

        valor_tag = listing.find_previous("a", attrs={"data-price": True})
        valor = valor_tag["data-price"] if valor_tag else None

        habitaciones_tag = listing.find("p", {"data-test": "bedrooms"})
        habitaciones = habitaciones_tag.text.strip().split(" ")[0] if habitaciones_tag else None

        banos_tag = listing.find("p", {"data-test": "bathrooms"})
        banos = banos_tag.text.strip().split(" ")[0] if banos_tag else None

        metros_tag = listing.find("p", {"data-test": "floor-area"})
        metros = metros_tag.text.strip().replace(" m²", "") if metros_tag else None

        # Si los datos no fueron extraídos con la estructura de producción, intentar con la de prueba
        if not barrio:
            barrio_tag = listing.find("div", class_="neighborhood")
            barrio = barrio_tag.text.strip() if barrio_tag else "N/A"

        if not valor:
            valor_tag = listing.find("div", class_="price")
            valor = valor_tag.text.strip() if valor_tag else "N/A"

        if not habitaciones:
            habitaciones_tag = listing.find("div", class_="rooms")
            habitaciones = habitaciones_tag.text.strip() if habitaciones_tag else "N/A"

        if not banos:
            banos_tag = listing.find("div", class_="bathrooms")
            banos = banos_tag.text.strip() if banos_tag else "N/A"

        if not metros:
            metros_tag = listing.find("div", class_="size")
            metros = metros_tag.text.strip() if metros_tag else "N/A"

        print(f"Extraído: {barrio}, {valor}, {habitaciones}, {banos}, {metros}")  # Log de depuración

        listings.append([
            datetime.today().strftime('%Y-%m-%d'),
            barrio, valor, habitaciones, banos, metros
        ])

    return listings


def process_html_file(key):
    response = s3_client.get_object(Bucket=S3_BUCKET_INPUT, Key=key)
    html_content = response["Body"].read().decode("utf-8")
    extracted_data = extract_data_from_html(html_content)
    
    if not extracted_data:
        print("No se extrajo ningún dato válido.")
    
    output_key = key.replace("mitula10", "casascsv").replace(".html", ".csv")
    save_to_csv(extracted_data, output_key)

def save_to_csv(data, key):
    csv_buffer = "FechaDescarga,Barrio,Valor,NumHabitaciones,NumBanos,mts2\n"
    for row in data:
        csv_buffer += ",".join(row) + "\n"
    
    s3_client.put_object(Bucket=S3_BUCKET_OUTPUT, Key=key, Body=csv_buffer)
    print(f"CSV guardado en: {key}")

def lambda_handler(event, context):
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        process_html_file(key)
    return {"statusCode": 200, "body": "Procesamiento completado"}