"""GitHub Actions için Telegram hatırlatıcı. Her çalışmada bir kez bakar ve vakti gelen mesajları yollar."""
import os, json, urllib.request, urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ---- BURAYI DÜZENLE (token ve chat ID buraya YAZILMAZ, GitHub Secrets'ta durur) ----
UYANMA = "08:00"
ANTRENMAN = "18:00"
KALORI, PROTEIN = 2750, 104
# 0=Pazartesi ... 6=Pazar. Antrenman olmayan günler dinlenme sayılır.
PROGRAM = {
    0: ("Üst Vücut A", ["Bench Press 4x8", "Oturarak Kürek 3x10", "Omuz Press 3x10", "Dumbbell Curl 3x10", "Triceps Pushdown 3x12"]),
    1: ("Alt Vücut A", ["Squat 4x8", "Romanian Deadlift 3x10", "Baldır Press 4x15", "Plank 3x45sn"]),
    3: ("Üst Vücut B", ["Eğimli Dumbbell Press 3x10", "Lat Pulldown 4x10", "Lateral Raise 3x15", "Face Pull 3x15", "Hammer Curl 2x12"]),
    4: ("Alt Vücut B", ["Leg Press 3x12", "Hip Thrust 3x10", "Leg Curl 3x12", "Baldır Press 4x15", "Crunch 3x15"]),
}
# ------------------------------------------------------------------------------------

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo("Europe/Istanbul")
GECIKME_DK = 90  # Gecikmeli çalışsa bile vakti en fazla 90 dk geçmiş mesajı yollar

def gonder(metin):
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": metin}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data)
    urllib.request.urlopen(req, timeout=20).read()
    print("gönderildi:", metin.split("\n")[0])

def saat(s, dk=0):
    h, m = map(int, s.split(":"))
    t = (h * 60 + m + dk) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"

def gunluk_plan(gun):
    p = PROGRAM.get(gun)
    ozet = f"Hedef: {KALORI} kcal, {PROTEIN} g protein, 2,5 L su."
    if p:
        sabah = f"Günaydın! Bugün: {p[0]}\n" + "\n".join("- " + e for e in p[1]) + f"\n{ozet}"
    else:
        sabah = f"Günaydın! Bugün dinlenme günü. Kaslar dinlenirken büyür.\n{ozet}\n5 g kreatini kahvaltıyla al."
    liste = [(saat(UYANMA, 30), sabah)]
    if p:
        liste += [
            (saat(ANTRENMAN, -150), "Antrenman öncesi ana öğün zamanı: karbonhidrat + protein, yağı az tut."),
            (saat(ANTRENMAN, -45), "Hafif atıştırma: muz veya yulaf, biraz su."),
            (ANTRENMAN, f"Antrenman vakti: {p[0]}. Son setlerde zorlanacağın ağırlığı seç."),
            (saat(ANTRENMAN, 75), "Gainer + 5 g kreatin zamanı. Yarım ölçekle başla, sonra artır."),
            (saat(ANTRENMAN, 210), "Akşam yemeği: protein + karbonhidrat + sebze."),
        ]
    else:
        liste += [("20:00", "Akşam yemeği zamanı: protein + karbonhidrat + sebze.")]
    liste += [("12:00", "Su hatırlatması: bir bardak iç."), ("16:00", "Su hatırlatması: bir bardak iç."),
              ("22:30", "Yatmadan önce lor veya yoğurt + ceviz. Sonra uyku, 7-8 saat.")]
    return liste

simdi = datetime.now(TZ)
bugun = simdi.strftime("%Y-%m-%d")

try:
    with open("state.json") as f:
        durum = json.load(f)
except Exception:
    durum = {}
if durum.get("date") != bugun:
    durum = {"date": bugun, "sent": []}

if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
    gonder("Test mesajı: bot GitHub'dan çalışıyor.")

for t, msg in gunluk_plan(simdi.weekday()):
    h, m = map(int, t.split(":"))
    vakit = simdi.replace(hour=h, minute=m, second=0, microsecond=0)
    if t not in durum["sent"] and timedelta(0) <= simdi - vakit < timedelta(minutes=GECIKME_DK):
        try:
            gonder(msg)
            durum["sent"].append(t)
        except Exception as e:
            print("Gönderilemedi:", e)

with open("state.json", "w") as f:
    json.dump(durum, f)
