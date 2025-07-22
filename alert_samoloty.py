# 📦 Import bibliotek
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from math import radians, sin, cos, sqrt, atan2
import matplotlib.pyplot as plt
import time

# 📍 Pozycja Oleśnicy
OLESNICA_LAT = 51.2136
OLESNICA_LON = 17.3836
PROMIEN_KM = 50

# ✉️ Dane do wysyłki maila
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = '11kubby11@gmail.com'        
SENDER_PASSWORD = 'fbld ppsj icfu hmtg'               
RECIPIENT_EMAIL = '11kubby11@gmail.com'  

# 🔢 Obliczanie dystansu pomiędzy dwoma punktami
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# 🗺️ Tworzenie mapy z samolotem i Oleśnicą
def generuj_mape(lat, lon, callsign):
    plt.figure(figsize=(6, 6))
    plt.plot(OLESNICA_LON, OLESNICA_LAT, 'bo', label='Oleśnica')
    plt.plot(lon, lat, 'ro', label=f'Samolot: {callsign}')
    plt.legend()
    plt.title('Samolot w pobliżu Oleśnicy')
    plt.xlabel('Długość geograficzna')
    plt.ylabel('Szerokość geograficzna')
    plt.grid(True)
    plt.savefig('mapa_samolotu.png')
    plt.close()

# ✉️ Wysyłanie maila z załącznikiem (mapą)
def wyslij_mail_z_mapa(samolot):
    generuj_mape(samolot['latitude'], samolot['longitude'], samolot['callsign'])

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"ALERT: Samolot w pobliżu Oleśnicy ({samolot['callsign']})"

    body = f"""Samolot {samolot['callsign']} ({samolot['icao24']}) znajduje się w promieniu 50 km od Oleśnicy.
Pozycja: {samolot['latitude']} / {samolot['longitude']}
Wysokość: {samolot.get('baro_altitude', 'brak')} m
Prędkość: {samolot.get('velocity', 'brak')} m/s"""

    msg.attach(MIMEText(body, 'plain'))

    filename = 'mapa_samolotu.png'
    with open(filename, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print("✅ Mail z mapą wysłany!")
    except Exception as e:
        print("❌ Błąd maila:", e)

# 🛰️ Sprawdzanie samolotów — tylko nowe w promieniu
widziane_samoloty = set()  # zapamiętane ICAO24

def sprawdz_samoloty():
    url = "https://opensky-network.org/api/states/all?lamin=50.9&lamax=51.6&lomin=16.6&lomax=18.2"
    try:
        response = requests.get(url)
        data = response.json()

        for samolot in data.get('states', []):
            icao24 = samolot[0]
            callsign = samolot[1]
            lon = samolot[5]
            lat = samolot[6]
            baro_altitude = samolot[7]
            velocity = samolot[9]

            if lat is not None and lon is not None:
                dystans = haversine(OLESNICA_LAT, OLESNICA_LON, lat, lon)
                if dystans <= PROMIEN_KM and icao24 not in widziane_samoloty:
                    widziane_samoloty.add(icao24)
                    info = {
                        'callsign': callsign,
                        'icao24': icao24,
                        'latitude': lat,
                        'longitude': lon,
                        'baro_altitude': baro_altitude,
                        'velocity': velocity
                    }
                    wyslij_mail_z_mapa(info)
    except Exception as e:
        print("❌ Błąd danych:", e)

# 🔁 Uruchamiaj cyklicznie co 10 minut
while True:
    sprawdz_samoloty()
    time.sleep(600)
