import boto3
import csv
import os
from bs4 import BeautifulSoup
from datetime import datetime

def process_mitula_html(event, context):
    s3 = boto3.client("s3")
    source_bucket = "mitula10"
    destination_bucket = "infocasas"
    
    # Obtener el archivo del evento de S3
    for record in event['Records']:
        key = record['s3']['object']['key']
        response = s3.get_object(Bucket=source_bucket, Key=key)
        html_content = response['Body'].read().decode('utf-8')
        
        # Extraer información con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        houses = []
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        for listing in soup.find_all("div", class_="listing-info"):  # Ajustar selector según estructura real
            barrio = listing.find("span", class_="location").text if listing.find("span", class_="location") else ""
            valor = listing.find("span", class_="price").text if listing.find("span", class_="price") else ""
            habitaciones = listing.find("span", class_="bedrooms").text if listing.find("span", class_="bedrooms") else ""
            banos = listing.find("span", class_="bathrooms").text if listing.find("span", class_="bathrooms") else ""
            mts2 = listing.find("span", class_="size").text if listing.find("span", class_="size") else ""
            
            houses.append([today, barrio, valor, habitaciones, banos, mts2])
        
        # Guardar en CSV en S3
        csv_key = f"{today}.csv"
        local_csv = f"/tmp/{csv_key}"
        
        with open(local_csv, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["FechaDescarga", "Barrio", "Valor", "NumHabitaciones", "NumBanos", "mts2"])
            writer.writerows(houses)
        
        s3.upload_file(local_csv, destination_bucket, csv_key)
        print(f"Archivo guardado en s3://{destination_bucket}/{csv_key}")
    
    return {"status": "success"}
