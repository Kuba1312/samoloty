# W tym miejscu importujemy biblioteki
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from math import radians, sin, cos, sqrt, atan2
import time
import datetime

# W tym miejscu podajemy współrzędne do miasta którego chcemy liczyć promień 
OLESNICA_LAT = 51.2136
OLESNICA_LON = 17.3836
PROMIEN_KM = 70

# W tym miejscu podajemy dane do wysyłania maila
SENDER_EMAIL = '11kubby11@gmail.com'
SENDER_PASSWORD = 'fbld ppsj icfu hmtg'
RECIPIENT_EMAIL = '11kubby11@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# W tym miejscu oblicza nam odległość z miejsca A do miejsca B 
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lat2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# W tym miejscu próbuje wyczytać nazwę/model samolotu jeżeli to tylko możliwe
def pobierz_model(icao24):
    url = f"https://opensky-network.org/api/metadata/aircraft/icao24/{icao24}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f" API zwróciło kod {response.status_code} — model niedostępny.")
            return "Brak danych"
        dane = response.json()
        return dane.get("aircraftType", "Nieznany")
    except Exception as e:
        print(f" Błąd pobierania modelu: {e}")
        return "Nieznany"

# W tym miejscu wysyła link do mapki gdzie znajduje się samolot 
def wyslij_mail(samolot):
    lat = samolot['latitude']
    lon = samolot['longitude']
    link_google_maps = f"https://www.google.com/maps?q={lat},{lon}"

    model_samolotu = pobierz_model(samolot['icao24'])

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"ALERT: Samolot w pobliżu Oleśnicy ({samolot['callsign']})"

    # W tym miejscu budujemy treść wiadomości
    body = f"""✈️ Wykryto nowy samolot w promieniu {PROMIEN_KM} km od Oleśnicy!

• Callsign: {samolot['callsign']}
• ICAO24: {samolot['icao24']}
• Typ/Model: {model_samolotu}
• Wysokość: {samolot.get('baro_altitude', 'brak')} m
• Prędkość: {samolot.get('velocity', 'brak')} m/s

Lokalizacja: {lat}, {lon}
Mapa: {link_google_maps}
"""

    # W tym miejscu zapisujemy wiadomość lokalnie do pliku
    try:
        with open("log_alerty.txt", "a", encoding="utf-8") as f:
            f.write(f"{body}\n{'-' * 50}\n")
        print(" Zapisano alert lokalnie do pliku.")
    except Exception as e:
        print(f" Błąd zapisu do pliku: {e}")

    # W tym miejscu próbujemy wysłać maila
    try:
        print(" Wysyłanie maila...")
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(" Mail z lokalizacją wysłany!")
    except Exception as e:
        print(" Mail się nie wysłał — zapisuję tylko lokalnie:", e)

# W tym miejscu znajduje się główna funkcja która ogólnie wyczytuje i znajduje samoloty które potem wyświetlają nam się w mailu 
widziane_samoloty = set()

def sprawdz_samoloty():
    url = "https://opensky-network.org/api/states/all?lamin=50.9&lamax=51.6&lomin=16.6&lomax=18.2"
    try:
        response = requests.get(url)
        if response.status_code == 200 and response.text.strip():
            try:
                data = response.json()
            except Exception as e:
                print(f" Błąd JSON: {e}")
                return
        else:
            print(f" API zwróciło kod {response.status_code} lub pustą odpowiedź.")
            return

        for s in data.get('states', []):
            icao24 = s[0]
            callsign = s[1]
            lon = s[5]
            lat = s[6]
            altitude = s[7]
            velocity = s[9]

            if lat is None or lon is None:
                print(f" Pominięto: brak lokalizacji dla samolotu {icao24}")
                continue

            dystans = haversine(OLESNICA_LAT, OLESNICA_LON, lat, lon)
            print(f" Samolot: {callsign or 'brak'} | {icao24} | dystans: {round(dystans, 2)} km")

            if dystans <= PROMIEN_KM and icao24 not in widziane_samoloty:
                widziane_samoloty.add(icao24)
                info = {
                    'callsign': callsign,
                    'icao24': icao24,
                    'latitude': lat,
                    'longitude': lon,
                    'baro_altitude': altitude,
                    'velocity': velocity
                }
                print(" Wykryto nowy samolot w promieniu — wysyłam alert!")
                wyslij_mail(info)
            else:
                print(" Samolot poza promieniem lub już widziany — pomijam.")

    except Exception as e:
        print(" Błąd danych:", e)

# W tym miejscu zastosowałem pętlę tak aby co 10 minut sprawdzało jaki samolot się porusza na obszarze 50km przy Oleśnicy (oczywiście jak wykrywa dany samolot to też mail przychodzi)
print("📡 Startuję! Sprawdzam samoloty co 10 minut...")

licznik = 1

while True:
    print(f"\n🌀 Krok {licznik} | {datetime.datetime.now().strftime('%H:%M:%S')} — sprawdzam niebo...")
    sprawdz_samoloty()
    licznik += 1
    time.sleep(600)
