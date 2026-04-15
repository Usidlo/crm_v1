from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup

# ── České jmeniny ─────────────────────────────────────────────────────────
# Zdroj: standardní český kalendář jmenin
NAME_DAYS = {
    "01-01": "Nový rok",  "01-02": "Karina",     "01-03": "Radmila",
    "01-04": "Diana",     "01-05": "Dalimil",    "01-06": "Kašpar",
    "01-07": "Vilma",     "01-08": "Čestmír",    "01-09": "Vladan",
    "01-10": "Břetislav", "01-11": "Bohdana",    "01-12": "Pravoslav",
    "01-13": "Edita",     "01-14": "Radovan",    "01-15": "Alice",
    "01-16": "Ctirad",    "01-17": "Drahoslav",  "01-18": "Vladislav",
    "01-19": "Doubravka", "01-20": "Ilona",      "01-21": "Běla",
    "01-22": "Slavomír",  "01-23": "Zdeněk",     "01-24": "Milena",
    "01-25": "Miloš",     "01-26": "Zora",       "01-27": "Ingrid",
    "01-28": "Otýlie",    "01-29": "Zdislava",   "01-30": "Robin",
    "01-31": "Marika",
    "02-01": "Hynek",     "02-02": "Nela",       "02-03": "Blažej",
    "02-04": "Jarmila",   "02-05": "Dobromila",  "02-06": "Vanda",
    "02-07": "Veronika",  "02-08": "Milada",     "02-09": "Apolena",
    "02-10": "Mojmír",    "02-11": "Božena",     "02-12": "Slavěna",
    "02-13": "Věnceslava","02-14": "Valentýn",   "02-15": "Jiřina",
    "02-16": "Ljuba",     "02-17": "Miloslava",  "02-18": "Gizela",
    "02-19": "Patrik",    "02-20": "Oldřich",    "02-21": "Lenka",
    "02-22": "Isabela",   "02-23": "Svatopluk",  "02-24": "Matěj",
    "02-25": "Liliana",   "02-26": "Dorota",     "02-27": "Alexandr",
    "02-28": "Lumír",     "02-29": "Horymír",
    "03-01": "Bedřich",   "03-02": "Anežka",     "03-03": "Kamil",
    "03-04": "Stela",     "03-05": "Kazimír",    "03-06": "Miroslav",
    "03-07": "Tomáš",     "03-08": "Gabriela",   "03-09": "Františka",
    "03-10": "Viktorie",  "03-11": "Anděla",     "03-12": "Řehoř",
    "03-13": "Růžena",    "03-14": "Rút",        "03-15": "Ida",
    "03-16": "Elena",     "03-17": "Vlastimil",  "03-18": "Eduard",
    "03-19": "Josef",     "03-20": "Světlana",   "03-21": "Radek",
    "03-22": "Leona",     "03-23": "Ivona",      "03-24": "Gabriel",
    "03-25": "Marián",    "03-26": "Emanuel",    "03-27": "Dita",
    "03-28": "Soňa",      "03-29": "Taťána",     "03-30": "Arnošt",
    "03-31": "Kvido",
    "04-01": "Hugo",      "04-02": "Erika",      "04-03": "Richard",
    "04-04": "Ivana",     "04-05": "Miroslava",  "04-06": "Vendula",
    "04-07": "Heřman",    "04-08": "Ema",        "04-09": "Dušan",
    "04-10": "Dáša",      "04-11": "Izabela",    "04-12": "Julius",
    "04-13": "Aleš",      "04-14": "Vincenc",    "04-15": "Anastázie",
    "04-16": "Irena",     "04-17": "Rudolf",     "04-18": "Valerie",
    "04-19": "Rostislav", "04-20": "Marcela",    "04-21": "Alexandra",
    "04-22": "Evženie",   "04-23": "Vojtěch",    "04-24": "Jiří",
    "04-25": "Marek",     "04-26": "Oto",        "04-27": "Jaroslava",
    "04-28": "Vlastislav","04-29": "Robert",     "04-30": "Blahoslav",
    "05-01": "Svátek práce","05-02": "Zikmund",  "05-03": "Alexej",
    "05-04": "Květoslava","05-05": "Klaudie",    "05-06": "Radoslav",
    "05-07": "Stanislav", "05-08": "Den vítězství","05-09": "Ctibor",
    "05-10": "Blažena",   "05-11": "Svatava",    "05-12": "Pankrác",
    "05-13": "Servác",    "05-14": "Bonifác",    "05-15": "Žofie",
    "05-16": "Přemysl",   "05-17": "Aneta",      "05-18": "Nataša",
    "05-19": "Ivo",       "05-20": "Zbyšek",     "05-21": "Monika",
    "05-22": "Emil",      "05-23": "Vladimír",   "05-24": "Jana",
    "05-25": "Viola",     "05-26": "Filip",      "05-27": "Valdemar",
    "05-28": "Vilém",     "05-29": "Maxmilián",  "05-30": "Ferdinand",
    "05-31": "Kamila",
    "06-01": "Laura",     "06-02": "Jarmil",     "06-03": "Tamara",
    "06-04": "Dalibor",   "06-05": "Dobroslav",  "06-06": "Norbert",
    "06-07": "Iveta",     "06-08": "Medard",     "06-09": "Stanislava",
    "06-10": "Gita",      "06-11": "Bohuslav",   "06-12": "Antonie",
    "06-13": "Antonín",   "06-14": "Roland",     "06-15": "Vít",
    "06-16": "Zbyněk",    "06-17": "Adolf",      "06-18": "Milan",
    "06-19": "Leoš",      "06-20": "Květa",      "06-21": "Alois",
    "06-22": "Pavla",     "06-23": "Zdeňka",     "06-24": "Jan",
    "06-25": "Ivan",      "06-26": "Adriana",    "06-27": "Ladislav",
    "06-28": "Lubomír",   "06-29": "Petr",       "06-30": "Pavel",
    "07-01": "Jaroslava", "07-02": "Patricie",   "07-03": "Radomír",
    "07-04": "Prokop",    "07-05": "Cyrila Metoděje","07-06": "Mistr Jan Hus",
    "07-07": "Bohuslava", "07-08": "Nora",       "07-09": "Drahomíra",
    "07-10": "Libuše",    "07-11": "Olga",       "07-12": "Bořek",
    "07-13": "Markéta",   "07-14": "Karolína",   "07-15": "Jindřich",
    "07-16": "Luboš",     "07-17": "Martina",    "07-18": "Drahomír",
    "07-19": "Čeněk",     "07-20": "Ilja",       "07-21": "Vítězslav",
    "07-22": "Magdaléna", "07-23": "Libor",      "07-24": "Kristýna",
    "07-25": "Jakub",     "07-26": "Anna",       "07-27": "Věroslav",
    "07-28": "Viktor",    "07-29": "Marta",      "07-30": "Bořivoj",
    "07-31": "Ignác",
    "08-01": "Oskar",     "08-02": "Gustav",     "08-03": "Miluše",
    "08-04": "Dominik",   "08-05": "Kristián",   "08-06": "Oldřiška",
    "08-07": "Lada",      "08-08": "Soběslav",   "08-09": "Roman",
    "08-10": "Vavřinec",  "08-11": "Zuzana",     "08-12": "Klára",
    "08-13": "Alena",     "08-14": "Mojžíš",     "08-15": "Hana",
    "08-16": "Jáchym",    "08-17": "Petra",      "08-18": "Helena",
    "08-19": "Ludvík",    "08-20": "Bernard",    "08-21": "Johana",
    "08-22": "Bohuslava", "08-23": "Sandra",     "08-24": "Bartoloměj",
    "08-25": "Radim",     "08-26": "Luděk",      "08-27": "Otakar",
    "08-28": "Augustýn",  "08-29": "Evelína",    "08-30": "Vladěna",
    "08-31": "Pavlína",
    "09-01": "Linda",     "09-02": "Adéla",      "09-03": "Bronislav",
    "09-04": "Jindřiška", "09-05": "Boris",      "09-06": "Boleslav",
    "09-07": "Regína",    "09-08": "Mariana",    "09-09": "Daniela",
    "09-10": "Irma",      "09-11": "Denisa",     "09-12": "Marie",
    "09-13": "Lubor",     "09-14": "Radka",      "09-15": "Jolana",
    "09-16": "Ludmila",   "09-17": "Naděžda",    "09-18": "Kryštof",
    "09-19": "Zita",      "09-20": "Oleg",       "09-21": "Matouš",
    "09-22": "Darina",    "09-23": "Bořislava",  "09-24": "Jaromír",
    "09-25": "Zlata",     "09-26": "Andrea",     "09-27": "Jonáš",
    "09-28": "Václav",    "09-29": "Michal",     "09-30": "Jeroným",
    "10-01": "Igor",      "10-02": "Olívie",     "10-03": "Bohumil",
    "10-04": "František", "10-05": "Eliška",     "10-06": "Hanuš",
    "10-07": "Justýna",   "10-08": "Věra",       "10-09": "Štefan",
    "10-10": "Marina",    "10-11": "Andrej",     "10-12": "Marcel",
    "10-13": "Renáta",    "10-14": "Agáta",      "10-15": "Tereza",
    "10-16": "Havel",     "10-17": "Hedvika",    "10-18": "Lukáš",
    "10-19": "Michaela",  "10-20": "Vendelín",   "10-21": "Brigita",
    "10-22": "Sabina",    "10-23": "Teodor",     "10-24": "Taťána",
    "10-25": "Beáta",     "10-26": "Erik",       "10-27": "Šarlota",
    "10-28": "Den vzniku","10-29": "Silvie",     "10-30": "Tadeáš",
    "10-31": "Štěpánka",
    "11-01": "Felix",     "11-02": "Dušičky",    "11-03": "Hubert",
    "11-04": "Karel",     "11-05": "Miriam",     "11-06": "Liběna",
    "11-07": "Saskie",    "11-08": "Bohumír",    "11-09": "Bohdan",
    "11-10": "Evžen",     "11-11": "Martin",     "11-12": "Benedikt",
    "11-13": "Tibor",     "11-14": "Sáva",       "11-15": "Leopold",
    "11-16": "Otmar",     "11-17": "Mahulena",   "11-18": "Romana",
    "11-19": "Alžběta",   "11-20": "Nikola",     "11-21": "Albert",
    "11-22": "Cecílie",   "11-23": "Klement",    "11-24": "Emílie",
    "11-25": "Kateřina",  "11-26": "Artur",      "11-27": "Xenie",
    "11-28": "René",      "11-29": "Zina",       "11-30": "Ondřej",
    "12-01": "Iva",       "12-02": "Blanka",     "12-03": "Svatoslav",
    "12-04": "Barbora",   "12-05": "Jitka",      "12-06": "Mikuláš",
    "12-07": "Ambrož",    "12-08": "Květoslava", "12-09": "Vratislav",
    "12-10": "Julie",     "12-11": "Dana",       "12-12": "Simona",
    "12-13": "Lucie",     "12-14": "Lýdie",      "12-15": "Radana",
    "12-16": "Albína",    "12-17": "Daniel",     "12-18": "Miloslav",
    "12-19": "Ester",     "12-20": "Dagmar",     "12-21": "Natálie",
    "12-22": "Šimon",     "12-23": "Vlasta",     "12-24": "Adam",
    "12-25": "Boží hod",  "12-26": "Štěpán",     "12-27": "Žaneta",
    "12-28": "Bohumila",  "12-29": "Judita",     "12-30": "David",
    "12-31": "Silvestr",
}


_PRAGUE = ZoneInfo('Europe/Prague')


def now_prague():
    """Aktuální čas v pražském časovém pásmu (naive)."""
    return datetime.now(tz=_PRAGUE).replace(tzinfo=None)


def utc_to_prague(dt):
    """Převede UTC naive datetime na Prague naive datetime pro zobrazení."""
    if dt is None:
        return dt
    return dt.replace(tzinfo=ZoneInfo('UTC')).astimezone(_PRAGUE).replace(tzinfo=None)


_CZ_MONTHS_GEN = [
    'ledna','února','března','dubna','května','června',
    'července','srpna','září','října','listopadu','prosince',
]

def format_czech_date(dt):
    return f"{dt.day}. {_CZ_MONTHS_GEN[dt.month - 1]}"

def get_todays_nameday_name():
    """Vrátí jméno dnešního svátku (nebo prázdný řetězec)."""
    return NAME_DAYS.get(now_prague().strftime('%m-%d'), '')


def get_nameday_contacts(name):
    """Vrátí seznam kontaktních osob jejichž křestní jméno odpovídá svátku."""
    if not name:
        return []
    name_lower = name.lower()
    matches = []
    for c in ContactPerson.query.all():
        first = c.name.split()[0].lower() if c.name else ''
        if first == name_lower:
            matches.append(c)
    return matches


EMPLOYEE_CODE_TO_SIZE = {
    '1': 'freelancer',
    '2': 'micro', '3': 'micro',
    '4': 'small', '5': 'small', '6': 'small',
    '7': 'medium', '8': 'medium',
    '9': 'large', '10': 'large', '11': 'large',
    '12': 'enterprise', '13': 'enterprise', '14': 'enterprise', '15': 'enterprise',
}

SIZE_LABELS = {
    'freelancer': 'Freelancer (1 os.)',
    'micro':      'Mikro (2–9 zam.)',
    'small':      'Malá (10–49 zam.)',
    'medium':     'Střední (50–249 zam.)',
    'large':      'Velká (250–999 zam.)',
    'enterprise': 'Korporace (1 000+ zam.)',
}

SIZE_COLORS = {
    'freelancer': 'secondary',
    'micro':      'light',
    'small':      'info',
    'medium':     'warning',
    'large':      'success',
    'enterprise': 'primary',
}

TEMP_LABELS = {
    'hot':     '🔥 Hot',
    'neutral': 'Neutrální',
    'cold':    '❄️ Cold',
}

TEMP_COLORS = {
    'hot':     'danger',
    'neutral': 'secondary',
    'cold':    'info',
}

TEMP_ORDER = {'hot': 0, 'neutral': 1, 'cold': 2, None: 3}

PIPELINE_LABELS = {
    'new_lead':    'Nový lead',
    'ready':       'Připraveno',
    'contacted':   'Osloveno',
    'responded':   'Reagoval',
    'negotiation': 'Jednání',
    'offer':       'Nabídka',
    'won':         'Vyhráno',
    'onboarding':  'Zajišťování rozjezdu',
    'running':     'Běžící zakázka',
    'completed':   'Ukončená zakázka',
    'lost':        'Prohráno',
    'blacklist':   'Blacklist',
}

PIPELINE_COLORS = {
    'new_lead':    'light',
    'ready':       'info',
    'contacted':   'primary',
    'responded':   'warning',
    'negotiation': 'warning',
    'offer':       'success',
    'won':         'success',
    'onboarding':  'info',
    'running':     'success',
    'completed':   'secondary',
    'lost':        'danger',
    'blacklist':   'dark',
}

PIPELINE_ACTIVE   = ['new_lead', 'ready', 'contacted', 'responded', 'negotiation', 'offer', 'won']
PIPELINE_RUNNING  = ['onboarding', 'running', 'completed']
PIPELINE_INACTIVE = ['lost', 'blacklist']
# Pořadí zobrazení aktivních: Vyhráno nejdřív, Nový lead poslední
PIPELINE_ACTIVE_DISPLAY_ORDER = {k: i for i, k in enumerate(
    ['won', 'offer', 'negotiation', 'responded', 'contacted', 'ready', 'new_lead']
)}

PIPELINE_ORDER = {k: i for i, k in enumerate(PIPELINE_LABELS)}

SIZE_QUALITY_LABELS = {
    'manual':        'Ručně potvrzeno',
    'public_source': 'Veřejný zdroj',
    'estimate':      'Odhad',
}
SIZE_QUALITY_COLORS = {
    'manual':        'success',
    'public_source': 'info',
    'estimate':      'secondary',
}

CONTACT_TYPE_LABELS = {
    'verified':        'Ověřený',
    'unverified':      'Neověřený',
    'generic_email':   'Generický email',
    'estimated_email': 'Odhadnutý email',
}
CONTACT_TYPE_COLORS = {
    'verified':        'success',
    'unverified':      'secondary',
    'generic_email':   'warning',
    'estimated_email': 'warning',
}

CONTACT_ROLE_LABELS = {
    'hr':           'HR',
    'management':   'Management',
    'production':   'Výroba / produkce',
    'sales':        'Obchod',
    'other':        'Jiná',
}

TRUST_LEVEL_LABELS = {
    'confirmed': 'Potvrzený',
    'probable':  'Pravděpodobný',
    'auto':      'Automatický odhad',
}
TRUST_LEVEL_COLORS = {
    'confirmed': 'success',
    'probable':  'warning',
    'auto':      'secondary',
}

NEWS_PRIORITY_LABELS = {'high': 'Vysoká', 'medium': 'Střední', 'low': 'Nízká'}
NEWS_PRIORITY_COLORS = {'high': 'danger', 'medium': 'warning', 'low': 'secondary'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crm-secret-key-2024'
app.jinja_env.filters['prague'] = utc_to_prague

# ── Přihlášení & Uživatelé ──────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Tato stránka je přístupná pouze administrátorovi.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.is_active and check_password_hash(user.password_hash, password):
            session['user_id']        = user.id
            session['username']       = user.username
            session['is_admin']       = user.is_admin
            session['team_member_id'] = user.team_member_id
            ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
            db.session.add(LoginLog(user_id=user.id, ip_address=ip))
            db.session.commit()
            return redirect(url_for('dashboard'))
        error = 'Špatné jméno nebo heslo, nebo účet je deaktivován.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


@app.context_processor
def inject_globals():
    current_user = None
    unread_news_count = 0
    if session.get('user_id'):
        current_user = {
            'id':       session['user_id'],
            'username': session.get('username'),
            'is_admin': session.get('is_admin', False),
        }
        unread_news_count = ClientNews.query.filter_by(is_read=False).count()
    nameday_name = get_todays_nameday_name()
    return dict(
        nameday_name=nameday_name,
        size_labels=SIZE_LABELS, size_colors=SIZE_COLORS,
        temp_labels=TEMP_LABELS, temp_colors=TEMP_COLORS,
        pipeline_labels=PIPELINE_LABELS, pipeline_colors=PIPELINE_COLORS,
        size_quality_labels=SIZE_QUALITY_LABELS, size_quality_colors=SIZE_QUALITY_COLORS,
        contact_type_labels=CONTACT_TYPE_LABELS, contact_type_colors=CONTACT_TYPE_COLORS,
        contact_role_labels=CONTACT_ROLE_LABELS,
        trust_level_labels=TRUST_LEVEL_LABELS, trust_level_colors=TRUST_LEVEL_COLORS,
        news_priority_labels=NEWS_PRIORITY_LABELS, news_priority_colors=NEWS_PRIORITY_COLORS,
        current_user=current_user,
        unread_news_count=unread_news_count,
    )


# ── Models ─────────────────────────────────────────────────────────────────

class User(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(100), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    is_admin       = db.Column(db.Boolean, default=False, nullable=False)
    is_active      = db.Column(db.Boolean, default=True, nullable=False)
    team_member_id = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    team_member    = db.relationship('TeamMember', backref='user', uselist=False)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200))
    ico = db.Column(db.String(20))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(500))
    web_description = db.Column(db.Text)
    address = db.Column(db.String(500))
    statutory = db.Column(db.Text)
    branches = db.Column(db.Text)
    size_category     = db.Column(db.String(20))  # micro, small, medium, large
    size_quality      = db.Column(db.String(20))  # manual, public_source, estimate
    temperature       = db.Column(db.String(10))  # hot, neutral, cold
    pipeline_status   = db.Column(db.String(30))  # new_lead, ready, contacted, ...
    owner_id          = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=True)
    notes             = db.Column(db.Text)
    last_refreshed_at = db.Column(db.DateTime)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    interactions = db.relationship('Interaction', backref='client', lazy=True, cascade='all, delete-orphan')
    contacts     = db.relationship('ContactPerson', backref='client', lazy=True, cascade='all, delete-orphan')
    reminders    = db.relationship('Reminder', backref='client', lazy=True, cascade='all, delete-orphan')
    news         = db.relationship('ClientNews', backref='client', lazy=True, cascade='all, delete-orphan',
                                   order_by='ClientNews.created_at.desc()')
    owner        = db.relationship('TeamMember', foreign_keys=[owner_id], backref='owned_clients')


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    interactions = db.relationship('Interaction', backref='member', lazy=True)
    reminders = db.relationship('Reminder', backref='assigned_member', lazy=True)


class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=False)
    contact_person_id = db.Column(db.Integer, db.ForeignKey('contact_person.id'), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    method = db.Column(db.String(50), nullable=False)  # email, telefon, osobně, video
    subject = db.Column(db.String(300))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contact_person = db.relationship('ContactPerson', backref='interactions', lazy=True)


class ContactPerson(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    client_id    = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    name         = db.Column(db.String(200), nullable=False)
    role         = db.Column(db.String(200))
    email        = db.Column(db.String(200))
    phone        = db.Column(db.String(50))
    contact_type = db.Column(db.String(30))   # verified, unverified, generic_email, estimated_email
    contact_role = db.Column(db.String(20))   # hr, management, other
    trust_level  = db.Column(db.String(20))   # confirmed, probable, auto


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=True)
    title = db.Column(db.String(300), nullable=False)
    due_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    done = db.Column(db.Boolean, default=False, nullable=False)
    notified = db.Column(db.Boolean, default=False, nullable=False)
    notified_day = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClientNews(db.Model):
    id                 = db.Column(db.Integer, primary_key=True)
    client_id          = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    category           = db.Column(db.String(50))    # address, size, statutory, hr_contact, jobs
    priority           = db.Column(db.String(10), default='medium')   # high, medium, low
    title              = db.Column(db.String(300), nullable=False)
    body               = db.Column(db.Text)
    source             = db.Column(db.String(50))    # ares, kurzy_cz, website, hr_finder
    old_value          = db.Column(db.Text)
    new_value          = db.Column(db.Text)
    confidence         = db.Column(db.String(10))    # high, medium, low
    requires_action    = db.Column(db.Boolean, default=False)
    recommended_action = db.Column(db.String(300))
    contact_id         = db.Column(db.Integer, db.ForeignKey('contact_person.id'), nullable=True)
    deal_id            = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=True)
    is_read            = db.Column(db.Boolean, default=False, nullable=False)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    contact            = db.relationship('ContactPerson', backref='news_items')
    deal               = db.relationship('Deal', backref='news_items')


deal_contact = db.Table('deal_contact',
    db.Column('deal_id',    db.Integer, db.ForeignKey('deal.id'),           primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contact_person.id'), primary_key=True),
)

client_cluster = db.Table('client_cluster',
    db.Column('client_id',  db.Integer, db.ForeignKey('client.id'),  primary_key=True),
    db.Column('cluster_id', db.Integer, db.ForeignKey('cluster.id'), primary_key=True),
)


class Deal(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    client_id        = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    owner_id         = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=True)
    title            = db.Column(db.String(300), nullable=False)
    status           = db.Column(db.String(30), default='new_lead')
    notes            = db.Column(db.Text)
    next_step        = db.Column(db.String(300))
    last_activity_at = db.Column(db.DateTime)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow)
    client           = db.relationship('Client', backref='deals')
    owner            = db.relationship('TeamMember', backref='deals')
    contacts         = db.relationship('ContactPerson', secondary='deal_contact', backref='deals')


class Cluster(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    color       = db.Column(db.String(20), default='primary')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    clients     = db.relationship('Client', secondary='client_cluster', backref='clusters')


class AuditLog(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    entity_type = db.Column(db.String(50))   # client, contact, deal, reminder, user, team
    entity_id   = db.Column(db.Integer)
    action      = db.Column(db.String(20))   # create, update, delete
    field_name  = db.Column(db.String(100))
    old_value   = db.Column(db.Text)
    new_value   = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user        = db.relationship('User', backref='audit_logs')


class LoginLog(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship('User', backref='login_logs')


# ── Audit log helper ────────────────────────────────────────────────────────

def _audit(entity_type, entity_id, action, changes=None):
    """Zaznamená změnu do audit logu.
    changes = dict {field: (old_value, new_value)} nebo None pro create/delete."""
    uid = session.get('user_id')
    if changes:
        for field, (old, new) in changes.items():
            o, n = str(old or ''), str(new or '')
            if o != n:
                db.session.add(AuditLog(
                    user_id=uid, entity_type=entity_type, entity_id=entity_id,
                    action=action, field_name=field,
                    old_value=o if o else None, new_value=n if n else None,
                ))
    else:
        db.session.add(AuditLog(
            user_id=uid, entity_type=entity_type, entity_id=entity_id, action=action,
        ))


# ── Routes: Dashboard ───────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    view = request.args.get('view', 'all')  # 'all' nebo 'mine'

    # Zjisti team_member_id přihlášeného uživatele
    user = User.query.get(session.get('user_id'))
    my_member_id = user.team_member_id if user else None

    clients_count = Client.query.count()
    interactions_count = Interaction.query.count()

    if view == 'mine' and my_member_id:
        pending_count = Reminder.query.filter_by(done=False, member_id=my_member_id).count()
        upcoming = (Reminder.query
                    .filter_by(done=False, member_id=my_member_id)
                    .order_by(Reminder.due_at)
                    .limit(5).all())
        recent = (Interaction.query
                  .filter_by(member_id=my_member_id)
                  .order_by(Interaction.date.desc())
                  .limit(10).all())
        recent_deals = (Deal.query
                        .filter_by(owner_id=my_member_id)
                        .order_by(Deal.updated_at.desc())
                        .limit(5).all())
        my_client_ids = [c.id for c in Client.query.filter_by(owner_id=my_member_id).all()]
        recent_news = (ClientNews.query
                       .filter(ClientNews.is_read == False,
                               ClientNews.client_id.in_(my_client_ids))
                       .order_by(ClientNews.created_at.desc())
                       .limit(5).all())
    else:
        pending_count = Reminder.query.filter_by(done=False).count()
        upcoming = (Reminder.query
                    .filter_by(done=False)
                    .order_by(Reminder.due_at)
                    .limit(5).all())
        recent = (Interaction.query
                  .order_by(Interaction.date.desc())
                  .limit(10).all())
        recent_deals = (Deal.query
                        .order_by(Deal.updated_at.desc())
                        .limit(5).all())
        recent_news = (ClientNews.query
                       .filter_by(is_read=False)
                       .order_by(ClientNews.created_at.desc())
                       .limit(5).all())

    nd_name = get_todays_nameday_name()
    nd_contacts = get_nameday_contacts(nd_name)
    today = now_prague()
    nd_date_str = format_czech_date(today)
    nd_tomorrow_name = NAME_DAYS.get((today + timedelta(days=1)).strftime('%m-%d'), '')

    return render_template('dashboard.html',
                           clients_count=clients_count,
                           interactions_count=interactions_count,
                           pending_count=pending_count,
                           recent=recent,
                           upcoming=upcoming,
                           recent_deals=recent_deals,
                           recent_news=recent_news,
                           view=view,
                           has_member=bool(my_member_id),
                           now=now_prague(),
                           nd_name=nd_name,
                           nd_contacts=nd_contacts,
                           nd_date_str=nd_date_str,
                           nd_tomorrow_name=nd_tomorrow_name)


# ── Routes: Clients ─────────────────────────────────────────────────────────

@app.route('/clients')
@login_required
def clients():
    q          = request.args.get('q', '').strip()
    size       = request.args.get('size', '').strip()
    temp       = request.args.get('temp', '').strip()
    pipeline   = request.args.get('pipeline', '').strip()
    cluster_id = request.args.get('cluster', '').strip()
    sort       = request.args.get('sort', 'category')
    query = Client.query
    if q:
        query = query.filter(
            (Client.name.ilike(f'%{q}%')) |
            (Client.company.ilike(f'%{q}%')) |
            (Client.email.ilike(f'%{q}%'))
        )
    if size:
        query = query.filter(Client.size_category == size)
    if temp:
        query = query.filter(Client.temperature == temp)
    if pipeline:
        query = query.filter(Client.pipeline_status == pipeline)
    if cluster_id:
        query = query.filter(Client.clusters.any(Cluster.id == int(cluster_id)))
    all_clients = query.all()

    SIZE_ORDER = {'freelancer': 0, 'micro': 1, 'small': 2,
                  'medium': 3, 'large': 4, 'enterprise': 5}
    if sort == 'alpha':
        all_clients.sort(key=lambda c: (c.name or '').lower())
    elif sort == 'size':
        all_clients.sort(key=lambda c: (SIZE_ORDER.get(c.size_category, 99), (c.name or '').lower()))
    elif sort == 'contacts':
        all_clients.sort(key=lambda c: (-len(c.interactions), (c.name or '').lower()))
    elif sort == 'pipeline':
        all_clients.sort(key=lambda c: (PIPELINE_ORDER.get(c.pipeline_status, 99), (c.name or '').lower()))
    else:  # category (default)
        all_clients.sort(key=lambda c: (TEMP_ORDER.get(c.temperature, 3), (c.name or '').lower()))

    all_clusters = Cluster.query.order_by(Cluster.name).all()
    return render_template('clients.html', clients=all_clients,
                           q=q, size=size, temp=temp, pipeline=pipeline,
                           cluster_id=cluster_id, all_clusters=all_clusters, sort=sort)


@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        company  = request.form.get('company', '').strip()
        temp_val = request.form.get('temperature', '').strip()
        pipe_val = request.form.get('pipeline_status', '').strip()
        sq_val   = request.form.get('size_quality', '').strip()
        owner_id = request.form.get('owner_id') or None
        client = Client(
            name=company,
            company=company,
            ico=request.form.get('ico', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            website=request.form.get('website', '').strip(),
            notes=request.form.get('notes', '').strip(),
            temperature=temp_val if temp_val in TEMP_LABELS else None,
            pipeline_status=pipe_val if pipe_val in PIPELINE_LABELS else None,
            size_quality=sq_val if sq_val in SIZE_QUALITY_LABELS else None,
            owner_id=int(owner_id) if owner_id else None,
        )
        db.session.add(client)
        db.session.flush()   # získej ID před audit logem
        _audit('client', client.id, 'create')
        db.session.commit()
        flash(f'Klient „{client.name}" byl přidán.', 'success')
        return redirect(url_for('client_detail', id=client.id))
    return render_template('client_form.html', client=None, members=members)


@app.route('/clients/<int:id>')
@login_required
def client_detail(id):
    client = Client.query.get_or_404(id)
    interactions = (Interaction.query
                    .filter_by(client_id=id)
                    .order_by(Interaction.date.desc()).all())
    reminders = (Reminder.query
                 .filter_by(client_id=id)
                 .order_by(Reminder.done, Reminder.due_at).all())
    deals = (Deal.query.filter_by(client_id=id)
             .order_by(Deal.updated_at.desc()).all())
    audit_log = (AuditLog.query
                 .filter(AuditLog.entity_type.in_(['client', 'contact', 'deal']),
                         AuditLog.entity_id == id)
                 .order_by(AuditLog.created_at.desc()).limit(50).all())
    members = TeamMember.query.order_by(TeamMember.name).all()
    all_clusters = Cluster.query.order_by(Cluster.name).all()
    creator_log = (AuditLog.query
                   .filter_by(entity_type='client', entity_id=id, action='create')
                   .order_by(AuditLog.created_at.asc()).first())
    now = now_prague()
    return render_template('client_detail.html', client=client,
                           interactions=interactions, reminders=reminders,
                           deals=deals, audit_log=audit_log,
                           members=members, all_clusters=all_clusters,
                           creator_log=creator_log, now=now)


@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        old = {
            'company': client.company, 'ico': client.ico, 'email': client.email,
            'phone': client.phone, 'website': client.website, 'notes': client.notes,
            'size_category': client.size_category, 'size_quality': client.size_quality,
            'temperature': client.temperature, 'pipeline_status': client.pipeline_status,
            'owner_id': client.owner_id,
        }
        company = request.form.get('company', '').strip()
        client.name = company
        client.company = company
        client.ico     = request.form.get('ico', '').strip()
        client.email   = request.form.get('email', '').strip()
        client.phone   = request.form.get('phone', '').strip()
        client.website = request.form.get('website', '').strip()
        client.notes   = request.form.get('notes', '').strip()
        size_val = request.form.get('size_category', '').strip()
        client.size_category = size_val if size_val in SIZE_LABELS else None
        sq_val = request.form.get('size_quality', '').strip()
        client.size_quality = sq_val if sq_val in SIZE_QUALITY_LABELS else None
        temp_val = request.form.get('temperature', '').strip()
        client.temperature = temp_val if temp_val in TEMP_LABELS else None
        pipe_val = request.form.get('pipeline_status', '').strip()
        client.pipeline_status = pipe_val if pipe_val in PIPELINE_LABELS else None
        owner_id = request.form.get('owner_id') or None
        client.owner_id = int(owner_id) if owner_id else None
        new = {
            'company': client.company, 'ico': client.ico, 'email': client.email,
            'phone': client.phone, 'website': client.website, 'notes': client.notes,
            'size_category': client.size_category, 'size_quality': client.size_quality,
            'temperature': client.temperature, 'pipeline_status': client.pipeline_status,
            'owner_id': client.owner_id,
        }
        _audit('client', client.id, 'update', {k: (old[k], new[k]) for k in old})
        db.session.commit()
        flash('Klient byl upraven.', 'success')
        return redirect(url_for('client_detail', id=client.id))
    return render_template('client_form.html', client=client, members=members)


@app.route('/clients/<int:id>/set-temperature', methods=['POST'])
@login_required
def set_temperature(id):
    client = Client.query.get_or_404(id)
    val = request.form.get('temperature', '').strip()
    client.temperature = val if val in TEMP_LABELS else None
    db.session.commit()
    return redirect(request.referrer or url_for('clients'))


@app.route('/clients/<int:id>/debug-ares')
@login_required
def debug_ares(id):
    client = Client.query.get_or_404(id)
    ico = client.ico.strip() if client.ico else ''
    if not ico:
        return jsonify({'error': 'Chybí IČO'})
    try:
        resp = _fetch(f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}')
        data = resp.json()
        presp = _fetch(f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}/provozovny')
        pdata = presp.json() if presp.status_code == 200 else {'status': presp.status_code}
        return jsonify({'zakladni': data, 'provozovny': pdata})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/clients/<int:id>/load-ares', methods=['POST'])
@login_required
def load_ares(id):
    client = Client.query.get_or_404(id)
    ico = client.ico.strip() if client.ico else ''
    if not ico:
        flash('Nejdříve zadej IČO a ulož klienta.', 'warning')
        return redirect(url_for('client_detail', id=id))
    parts = []
    errors = []

    data = {}
    nazev = client.name

    # 1) ARES — základní údaje
    try:
        resp = _fetch(f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}')
        if resp.status_code == 404:
            flash('IČO nebylo nalezeno v ARES.', 'danger')
            return redirect(url_for('client_detail', id=id))
        resp.raise_for_status()
        data = resp.json()
        nazev = data.get('obchodniJmeno', '') or client.name
        sidlo = data.get('sidlo') or {}
        adresa = sidlo.get('textovaAdresa', '')
        # Přepisujeme název vždy (officiální zdroj), adresu jen pokud prázdná
        if nazev:
            client.name = nazev
            client.company = nazev
        if adresa and not client.address:
            client.address = adresa
        # Velikost — jen pokud není ručně zadaná
        if not client.size_category:
            stat = data.get('statistickeUdaje') or {}
            emp_code = str(stat.get('pocetZamestnancuKod', ''))
            if emp_code in EMPLOYEE_CODE_TO_SIZE:
                client.size_category = EMPLOYEE_CODE_TO_SIZE[emp_code]
        parts.append('základní údaje')
    except Exception as e:
        errors.append(f'ARES: {e}')

    # 2a) Statutáři z ARES JSON (zastupciSubjektu)
    statutory_found = False
    try:
        zastupci = data.get('zastupciSubjektu') or []
        lines = []
        for z in zastupci:
            funkce = (z.get('typFunkce') or z.get('clenstvi', {}).get('nazev') or '').strip()
            osoba = z.get('zastupce') or z.get('fyzickaOsoba') or {}
            jmeno = ' '.join(filter(None, [
                osoba.get('jmeno', ''), osoba.get('prijmeni', '')
            ])).strip()
            if not jmeno:
                jmeno = str(osoba.get('obchodniJmeno', '')).strip()
            if jmeno:
                lines.append(f'{funkce}: {jmeno}' if funkce else jmeno)
        if lines:
            client.statutory = '\n'.join(lines)
            parts.append('statutáři (ARES)')
            statutory_found = True
    except Exception:
        pass

    # 2b) Statutáři z kurzy.cz jako záložka
    if not statutory_found:
        try:
            scraped_statutory, scraped_size = _scrape_statutory_and_size(ico)
            if scraped_statutory:
                client.statutory = scraped_statutory
                parts.append('statutáři (kurzy.cz)')
            if scraped_size and not client.size_category:
                client.size_category = scraped_size
        except Exception as e:
            errors.append(f'statutáři kurzy.cz: {e}')

    # 3) ARES — pobočky/provozovny
    try:
        presp = _fetch(
            f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}/provozovny'
        )
        if presp.status_code == 200:
            pdata = presp.json()
            provozovny = pdata.get('provozovny') or (pdata if isinstance(pdata, list) else [])
            branch_lines = []
            for p in provozovny[:20]:
                nazev_p = p.get('nazevProvozovny', '')
                adresa_p = (p.get('adresa') or {}).get('textovaAdresa', '')
                line = nazev_p or adresa_p
                if line:
                    branch_lines.append(line)
            if branch_lines:
                client.branches = '\n'.join(branch_lines)
                parts.append('pobočky')
    except Exception as e:
        errors.append(f'pobočky: {e}')

    db.session.commit()
    if parts:
        flash(f'Načteno z ARES: {", ".join(parts)}.', 'success')
    if errors:
        flash(f'Část dat se nepodařilo načíst: {"; ".join(errors)}', 'warning')
    return redirect(url_for('client_detail', id=id))


CAREER_KEYWORDS = [
    'kariera', 'kariéra', 'prace', 'práce', 'volne-pozice', 'volné-pozice',
    'jobs', 'careers', 'career', 'job', 'hiring', 'work-with-us',
    'join-us', 'join', 'team', 'tym', 'tým', 'recruit', 'employment',
    'pozice', 'nabidka', 'nabídka',
]


BRANCH_KEYWORDS = [
    'pobocky', 'pobočky', 'prodejny', 'provozovny', 'kde-nas-najdete',
    'kde-nas-najdou', 'kontakty', 'contacts', 'locations', 'offices',
    'nase-pobocky', 'nase-prodejny', 'kde-jsme', 'kamenné-prodejny',
]


def _scrape_branches(website_url):
    """
    Načte pobočky/provozovny z webu firmy.
    Hledá stránku s pobočkami a extrahuje adresy.
    """
    from urllib.parse import urljoin, urlparse
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url
    try:
        resp = _fetch(website_url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Hledej odkaz na stránku s pobočkami
        branch_url = None
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text(strip=True).lower()
            if any(kw in href or kw in text for kw in BRANCH_KEYWORDS):
                full = urljoin(website_url, a['href'])
                if urlparse(full).netloc == urlparse(website_url).netloc:
                    branch_url = full
                    break

        target_url = branch_url or website_url
        if branch_url:
            resp = _fetch(branch_url)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')

        # Extrahuj adresy — hledej PSČ vzor (123 45 nebo 12345)
        text = soup.get_text(' ', strip=True)
        psc_pattern = re.compile(r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^.!?\n]{5,80}\d{3}\s?\d{2}[^.!?\n]{0,30}', re.I)
        addresses = []
        for m in psc_pattern.finditer(text):
            addr = m.group(0).strip()
            # Odfiltruj duplikáty a příliš dlouhé
            if addr not in addresses and len(addr) < 120:
                addresses.append(addr)
            if len(addresses) >= 15:
                break

        if addresses:
            prefix = f'(zdroj: {target_url})\n' if branch_url else ''
            return prefix + '\n'.join(addresses)

        # Fallback — nadpisy na kontaktní stránce jako názvy poboček
        if branch_url:
            headings = []
            for tag in ['h2', 'h3']:
                for h in soup.find_all(tag):
                    t = h.get_text(strip=True)
                    if 5 < len(t) < 80:
                        headings.append(t)
            if headings:
                return f'(zdroj: {branch_url})\n' + '\n'.join(headings[:15])

        return None
    except Exception:
        return None


STATUTORY_ROLES = [
    'Předseda představenstva', 'Místopředseda představenstva', 'Člen představenstva',
    'Předseda dozorčí rady', 'Místopředseda dozorčí rady', 'Člen dozorčí rady',
    'Jednatel', 'Prokurista', 'Ředitel', 'Správce',
]

COUNTRIES = [
    'Česká republika', 'Spolková republika Německo', 'Slovenská republika',
    'Rakouská republika', 'Polská republika', 'Francouzská republika',
    'Spojené království', 'Spojené státy', 'Švýcarská konfederace',
]


def _scrape_statutory_and_size(ico):
    """
    Načte statutáře a velikost firmy z kurzy.cz.
    Vrátí (statutory_text, size_category).
    """
    try:
        resp = _fetch(f'https://rejstrik-firem.kurzy.cz/{ico}/')
        if resp.status_code not in (200, 301, 302):
            return None, None
        soup = BeautifulSoup(resp.content, 'html.parser')
        text = soup.get_text(' ', strip=True)

        # ── Statutáři ──────────────────────────────────────────────
        statutory = []
        idx = text.lower().find('statutární orgán')
        if idx < 0:
            idx = text.lower().find('statutár')
        if idx >= 0:
            block = text[idx:idx+3000]
            # Pro každou roli najdi jméno které po ní následuje
            role_pattern = '|'.join(re.escape(r) for r in STATUTORY_ROLES)
            matches = list(re.finditer(role_pattern, block, re.I))
            for i, m in enumerate(matches):
                role = m.group(0)
                # Jméno = text mezi koncem role a dalším matchem nebo "Den vzniku"
                end = matches[i+1].start() if i+1 < len(matches) else min(m.end()+200, len(block))
                name_chunk = block[m.end():end].strip()
                # Odstraň země a "Den vzniku..." texty
                for country in COUNTRIES:
                    name_chunk = name_chunk.replace(country, '')
                name_chunk = re.sub(r'Den vzniku.*', '', name_chunk, flags=re.I)
                name_chunk = re.sub(r'Počet členů.*', '', name_chunk, flags=re.I)
                name_chunk = re.sub(r'Způsob jednání.*', '', name_chunk, flags=re.I)
                name = name_chunk.strip().strip(',').strip()
                # Odfiltruj příliš dlouhé nebo prázdné
                if name and len(name) < 80:
                    statutory.append(f'{role}: {name}')
                # Zastav u dozorčí rady — zobrazíme jen představenstvo/jednatele
                if 'dozorčí rada' in role.lower() and len(statutory) > 5:
                    break

        statutory_text = '\n'.join(statutory) if statutory else None

        # ── Velikost ───────────────────────────────────────────────
        size = None
        m = re.search(r'po[čc]et\s+zam[eě]stnanc[ůu][^\d]*(\d[\d\s]*)', text, re.I)
        if m:
            count = int(re.sub(r'\s', '', m.group(1)))
            if count <= 1:
                size = 'freelancer'
            elif count < 10:
                size = 'micro'
            elif count < 50:
                size = 'small'
            elif count < 250:
                size = 'medium'
            elif count < 1000:
                size = 'large'
            else:
                size = 'enterprise'

        return statutory_text, size

    except Exception:
        return None, None


def _scrape_size(ico, company_name=''):
    """
    Pokusí se zjistit velikost firmy z více zdrojů.
    Vrátí (size_category, zdroj) nebo (None, None).
    """
    # 1. kurzy.cz — rejstřík firem
    try:
        resp = _fetch(f'https://rejstrik-firem.kurzy.cz/ico/{ico}/')
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(' ')
            # Hledáme vzor "Počet zaměstnanců: 123" nebo "zaměstnanci 50-249"
            m = re.search(r'po[čc]et\s+zam[eě]stnanc[ůu][^\d]*(\d[\d\s]*)', text, re.I)
            if m:
                count = int(re.sub(r'\s', '', m.group(1)))
                if count < 10:
                    return 'micro', 'kurzy.cz'
                elif count < 50:
                    return 'small', 'kurzy.cz'
                elif count < 500:
                    return 'medium', 'kurzy.cz'
                else:
                    return 'large', 'kurzy.cz'
            # Hledáme rozsahy jako "50 - 249"
            m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*zam', text, re.I)
            if m:
                avg = (int(m.group(1)) + int(m.group(2))) // 2
                if avg < 10:
                    return 'micro', 'kurzy.cz'
                elif avg < 50:
                    return 'small', 'kurzy.cz'
                elif avg < 500:
                    return 'medium', 'kurzy.cz'
                else:
                    return 'large', 'kurzy.cz'
    except Exception:
        pass

    # 2. Firmy.cz — hledání podle IČO
    try:
        resp = _fetch(f'https://www.firmy.cz/detail/{ico}')
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(' ')
            m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*zam', text, re.I)
            if m:
                avg = (int(m.group(1)) + int(m.group(2))) // 2
                if avg < 10:
                    return 'micro', 'firmy.cz'
                elif avg < 50:
                    return 'small', 'firmy.cz'
                elif avg < 500:
                    return 'medium', 'firmy.cz'
                else:
                    return 'large', 'firmy.cz'
    except Exception:
        pass

    return None, None


def _get_proxies():
    if os.environ.get('PYTHONANYWHERE_SITE'):
        return {'http': 'http://proxy.server:3128', 'https': 'http://proxy.server:3128'}
    return {}


def _fetch(url, timeout=6):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; CRM-bot/1.0)'}
    return requests.get(url, timeout=timeout, headers=headers, proxies=_get_proxies())


# Slova typická pro pracovní pozice
JOB_ROLE_KEYWORDS = [
    'specialista', 'specialist', 'manažer', 'manager', 'developer', 'vývojář',
    'analytik', 'analyst', 'koordinátor', 'coordinator', 'asistent', 'assistant',
    'vedoucí', 'ředitel', 'director', 'inženýr', 'engineer', 'technik', 'technician',
    'konzultant', 'consultant', 'obchodní', 'sales', 'marketing', 'accountant',
    'účetní', 'projektový', 'project', 'senior', 'junior', 'lead', 'architect',
    'designer', 'tester', 'qa', 'devops', 'hr ', 'recruiter', 'logistik',
    'skladník', 'řidič', 'operátor', 'mistr', 'konstruktér', 'právník',
    'lawyer', 'finance', 'finanční', 'it ', 'správce', 'administrátor',
    'administrator', 'support', 'podpora', 'scrum', 'product owner',
]


def _looks_like_job(text):
    """Vrátí True pokud text vypadá jako název pracovní pozice."""
    t = text.lower()
    return any(kw in t for kw in JOB_ROLE_KEYWORDS)


HR_EMAIL_PREFIXES = [
    'hr', 'kariera', 'kariéra', 'jobs', 'job', 'recruiting', 'recruitment',
    'talent', 'prace', 'práce', 'nabor', 'nábor', 'personalni', 'personální',
    'people', 'humanresources', 'lidi', 'zamestnani', 'zaměstnání',
]

HR_ROLE_KEYWORDS = [
    'hr manažer', 'hr manager', 'hr ředitel', 'hr director',
    'personalista', 'personalistka', 'recruiter', 'recruiterka',
    'talent acquisition', 'nábor', 'nabor', 'human resources',
    'personální ředitel', 'people partner', 'hr business partner',
    'hr bp', 'hr koordinátor', 'hr specialist',
]


def _extract_hr_role(context):
    """Pokusí se z kontextu extrahovat HR roli."""
    c = context.lower()
    for role in HR_ROLE_KEYWORDS:
        if role in c:
            return role.title()
    if 'hr' in c:
        return 'HR'
    return 'HR kontakt'


def _find_page_link(soup, base_url, keywords):
    """Obecně najde odkaz na stránku podle klíčových slov."""
    from urllib.parse import urljoin, urlparse
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        txt = a.get_text(strip=True).lower()
        if any(kw in href or kw in txt for kw in keywords):
            full = urljoin(base_url, a['href'])
            if urlparse(full).netloc == urlparse(base_url).netloc:
                return full
    return None


NAME_RE = re.compile(
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,20}'
    r'\s+'
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,25}(?:ová|ová)?'
)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

HR_CONTEXT_WORDS = HR_ROLE_KEYWORDS + [
    'hr', 'personál', 'nábor', 'recruiter', 'personalista', 'personalní',
    'people', 'kariéra', 'kariera', 'talent', 'zaměstnanci',
]

# Kandidátní URL cesty pro HR/kontaktní stránky
HR_URL_PATHS = [
    '/kariera', '/kariéra', '/kariera/kontakt', '/jobs/contact', '/jobs/kontakt',
    '/kontakty', '/kontakt', '/contact', '/contact-us',
    '/tym', '/tým', '/team', '/o-nas/tym', '/about/team',
    '/lide', '/lidé', '/people', '/nase-lide',
    '/hr', '/human-resources',
]


def _collect_pages(website_url):
    """Sbírá URL stránek k prohledání — web, sitemap, časté cesty."""
    from urllib.parse import urlparse, urljoin
    base = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"
    pages = [website_url]
    seen = {website_url}

    # 1. Hlavní stránka → najdi kariérní + kontaktní stránku
    try:
        resp = _fetch(website_url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            for kw_list, label in [
                (['kontakt', 'contact', 'tym', 'tým', 'team', 'lide', 'lidé', 'people'], 'contact'),
                (CAREER_KEYWORDS, 'career'),
            ]:
                url = _find_page_link(soup, website_url, kw_list)
                if url and url not in seen:
                    pages.append(url)
                    seen.add(url)
    except Exception:
        pass

    # 2. Zkus časté HR cesty
    for path in HR_URL_PATHS:
        url = base + path
        if url not in seen:
            pages.append(url)
            seen.add(url)

    # 3. Sitemap.xml → hledej HR/kariérní/kontaktní stránky
    try:
        smap = _fetch(base + '/sitemap.xml')
        if smap.status_code == 200:
            for loc in re.findall(r'<loc>(.*?)</loc>', smap.text):
                loc_lower = loc.lower()
                if any(kw in loc_lower for kw in
                       ['kariera', 'career', 'job', 'kontakt', 'contact', 'team', 'tym', 'hr', 'lide']):
                    if loc not in seen:
                        pages.append(loc)
                        seen.add(loc)
                        if len(pages) > 15:
                            break
    except Exception:
        pass

    return pages[:15]


def _extract_contacts_from_page(soup, text, domain):
    """Z jedné stránky vytáhne HR kontakty — email + jméno + role."""
    found = {}

    # 1. Schema.org Person markup
    for person in soup.find_all(attrs={'itemtype': re.compile(r'Person', re.I)}):
        name_el = person.find(attrs={'itemprop': 'name'})
        email_el = person.find(attrs={'itemprop': 'email'})
        role_el = person.find(attrs={'itemprop': 'jobTitle'})
        name = name_el.get_text(strip=True) if name_el else ''
        email = email_el.get_text(strip=True).replace('mailto:', '') if email_el else ''
        role = role_el.get_text(strip=True) if role_el else ''
        if email and any(kw in (name + role).lower() for kw in HR_CONTEXT_WORDS):
            found[email] = {'name': name or 'HR kontakt', 'role': role or 'HR', 'email': email}

    # 2. Emaily v textu + kontext
    for email in EMAIL_RE.findall(text):
        if email in found:
            continue
        local = email.lower().split('@')[0]
        is_hr_email = any(local == p or local.startswith(p) for p in HR_EMAIL_PREFIXES)

        idx = text.lower().find(email.lower())
        context = text[max(0, idx - 300): idx + 150]
        is_hr_context = any(kw in context.lower() for kw in HR_CONTEXT_WORDS)

        if is_hr_email or is_hr_context:
            role = _extract_hr_role(context)
            name_match = NAME_RE.search(context)
            name = name_match.group(0) if name_match else 'HR kontakt'
            found[email] = {'name': name, 'role': role, 'email': email}

    # 3. LinkedIn profily na stránce → vytáhni jméno z URL
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'linkedin.com/in/' in href:
            slug = href.rstrip('/').split('linkedin.com/in/')[-1].split('?')[0]
            # slug → jméno: "jana-novakova" → "Jana Novakova"
            li_name = ' '.join(p.capitalize() for p in slug.replace('-', ' ').split())
            li_text = a.get_text(strip=True) or li_name
            context = a.parent.get_text(' ', strip=True) if a.parent else li_text
            if any(kw in context.lower() for kw in HR_CONTEXT_WORDS):
                key = f'linkedin:{slug}'
                if key not in found:
                    found[key] = {
                        'name': li_text if len(li_text) < 60 else li_name,
                        'role': _extract_hr_role(context),
                        'email': '',
                        'linkedin': href,
                    }

    return found


def _search_bing_hr(company_name, domain):
    """Hledá HR kontakty přes Bing."""
    found = {}
    queries = [
        f'"{company_name}" personalista OR recruiter OR "HR manager" email',
        f'site:{domain} HR OR personalista OR kariéra kontakt email',
    ]
    for q in queries:
        try:
            resp = _fetch(
                f'https://www.bing.com/search?q={requests.utils.quote(q)}&count=10',
            )
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, 'html.parser')
            text = soup.get_text(' ', strip=True)
            for email in EMAIL_RE.findall(text):
                if email in found:
                    continue
                local = email.lower().split('@')[0]
                if any(local.startswith(p) for p in HR_EMAIL_PREFIXES) or domain in email.lower():
                    idx = text.lower().find(email.lower())
                    ctx = text[max(0, idx - 200): idx + 100]
                    name_match = NAME_RE.search(ctx)
                    found[email] = {
                        'name': name_match.group(0) if name_match else 'HR kontakt',
                        'role': _extract_hr_role(ctx),
                        'email': email,
                    }
            if len(found) >= 3:
                break
        except Exception:
            continue
    return found


def _find_hr_contacts(website_url, company_name=''):
    """
    Hledá HR kontakty z více zdrojů:
    1. Web firmy (hlavní stránka, kariéra, kontakty, tým, sitemap)
    2. Schema.org Person markup
    3. LinkedIn profily na webu
    4. Bing vyhledávání
    5. Generické emaily jako záloha
    """
    from urllib.parse import urlparse
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    domain = urlparse(website_url).netloc.replace('www.', '')
    found = {}

    # Fáze 1: web firmy
    pages = _collect_pages(website_url)
    for page_url in pages:
        try:
            resp = _fetch(page_url)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, 'html.parser')
            text = soup.get_text(' ', strip=True)
            page_found = _extract_contacts_from_page(soup, text, domain)
            found.update(page_found)
            if len(found) >= 8:
                break
        except Exception:
            continue

    # Fáze 2: Bing (pokud málo výsledků)
    if len(found) < 3 and company_name:
        bing_found = _search_bing_hr(company_name, domain)
        found.update(bing_found)

    # Fáze 3: generické emaily jako záloha
    if not found:
        for prefix in ['hr', 'kariera', 'jobs', 'recruiting']:
            found[f'{prefix}@{domain}'] = {
                'name': 'HR oddělení',
                'role': 'HR (obecný kontakt)',
                'email': f'{prefix}@{domain}',
            }
            break

    # Seřaď — napřed kontakty s emailem
    result = sorted(found.values(), key=lambda x: (not x.get('email'), x['name']))
    return result[:10]


def _find_career_url(soup, base_url):
    """Najde odkaz na kariérní stránku — včetně externích kariérních domén."""
    from urllib.parse import urljoin, urlparse
    base_host = urlparse(base_url).netloc.replace('www.', '')

    candidates = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True).lower()
        href_lower = href.lower()

        if any(kw in href_lower or kw in text for kw in CAREER_KEYWORDS):
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            if not parsed.scheme.startswith('http'):
                continue
            link_host = parsed.netloc.replace('www.', '')
            # Stejná doména nebo kariérní subdoména/doména související s firmou
            same_domain = link_host == base_host
            career_domain = any(kw in link_host for kw in ['kariera', 'career', 'jobs', 'prace'])
            if same_domain or career_domain:
                candidates.append((0 if same_domain else 1, full))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _extract_jobs(soup):
    """Extrahuje seznam pracovních pozic ze stránky."""
    jobs = []

    # 1. Schema.org JobPosting — nejspolehlivější
    for el in soup.find_all(attrs={'itemtype': re.compile(r'JobPosting', re.I)}):
        title = el.find(attrs={'itemprop': 'title'})
        if title:
            jobs.append(title.get_text(strip=True))
    if jobs:
        return jobs

    # 2. Elementy s třídou obsahující "job" nebo "position"
    for el in soup.find_all(class_=re.compile(r'job|position|vacancy|pozic|role', re.I)):
        for tag in ['h2', 'h3', 'h4', 'a']:
            heading = el.find(tag)
            if heading:
                text = heading.get_text(strip=True)
                if 5 < len(text) < 120 and _looks_like_job(text):
                    jobs.append(text)
    if jobs:
        return list(dict.fromkeys(jobs))[:25]

    # 3. Nadpisy které vypadají jako pracovní pozice
    for tag in ['h2', 'h3', 'h4']:
        for heading in soup.find_all(tag):
            text = heading.get_text(strip=True)
            if 5 < len(text) < 120 and _looks_like_job(text):
                jobs.append(text)
    if jobs:
        return list(dict.fromkeys(jobs))[:25]

    # 4. Odkazy které vypadají jako pracovní pozice
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        if 5 < len(text) < 120 and _looks_like_job(text):
            jobs.append(text)

    return list(dict.fromkeys(jobs))[:25]


@app.route('/clients/<int:id>/load-website', methods=['POST'])
@login_required
def load_website(id):
    client = Client.query.get_or_404(id)
    url = client.website.strip() if client.website else ''
    if not url:
        flash('Nejdříve zadej adresu webu a ulož klienta.', 'warning')
        return redirect(url_for('client_detail', id=id))
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        resp = _fetch(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        parts = []

        # 1. Popis z meta tagů
        meta = (soup.find('meta', attrs={'name': 'description'}) or
                soup.find('meta', attrs={'property': 'og:description'}))
        if meta and meta.get('content'):
            parts.append(meta['content'].strip())

        # 2. Hledej stránku "O nás" / "About"
        about_keywords = ['o-nas', 'o-nás', 'o-spolecnosti', 'o-společnosti',
                          'about', 'about-us', 'kdo-jsme', 'about-company']
        about_url = None
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            txt = a.get_text(strip=True).lower()
            if any(kw in href or kw == txt for kw in about_keywords):
                from urllib.parse import urljoin, urlparse
                full = urljoin(url, a['href'])
                if urlparse(full).netloc == urlparse(url).netloc:
                    about_url = full
                    break

        if about_url:
            try:
                aresp = _fetch(about_url)
                if aresp.status_code == 200:
                    asoup = BeautifulSoup(aresp.content, 'html.parser')
                    paras = [p.get_text(' ', strip=True)
                             for p in asoup.find_all('p')
                             if len(p.get_text()) > 80]
                    if paras:
                        parts.append('\n'.join(paras[:3]))
            except Exception:
                pass

        # 3. Fallback — první odstavce z hlavní stránky
        if not parts:
            paras = [p.get_text(' ', strip=True)
                     for p in soup.find_all('p') if len(p.get_text()) > 80]
            if paras:
                parts.append('\n'.join(paras[:2]))

        if parts:
            client.web_description = '\n\n'.join(parts)[:2000]
            db.session.commit()
            flash('Popis firmy byl načten.', 'success')
        else:
            flash('Web načten, ale popis se nepodařilo extrahovat.', 'warning')

    except Exception as e:
        flash(f'Chyba při načítání webu: {e}', 'danger')
    return redirect(url_for('client_detail', id=id))


@app.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    name = client.name
    _audit('client', id, 'delete')
    db.session.delete(client)
    db.session.commit()
    flash(f'Klient „{name}" byl smazán.', 'warning')
    return redirect(url_for('clients'))


# ── Routes: Contact Persons ─────────────────────────────────────────────────

@app.route('/clients/<int:client_id>/contacts/new', methods=['GET', 'POST'])
@login_required
def new_contact(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        ct = request.form.get('contact_type', '').strip()
        cr = request.form.get('contact_role', '').strip()
        tl = request.form.get('trust_level', '').strip()
        contact = ContactPerson(
            client_id=client_id,
            name=request.form['name'].strip(),
            role=request.form.get('role', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            contact_type=ct if ct in CONTACT_TYPE_LABELS else None,
            contact_role=cr if cr in CONTACT_ROLE_LABELS else None,
            trust_level=tl if tl in TRUST_LEVEL_LABELS else None,
        )
        db.session.add(contact)
        db.session.flush()
        _audit('contact', contact.id, 'create')
        db.session.commit()
        flash(f'Kontaktní osoba „{contact.name}" byla přidána.', 'success')
        return redirect(url_for('client_detail', id=client_id))
    return render_template('contact_form.html', client=client, contact=None)


@app.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
    contact = ContactPerson.query.get_or_404(id)
    if request.method == 'POST':
        old = {k: getattr(contact, k) for k in
               ('name', 'role', 'email', 'phone', 'contact_type', 'contact_role', 'trust_level')}
        contact.name  = request.form['name'].strip()
        contact.role  = request.form.get('role', '').strip()
        contact.email = request.form.get('email', '').strip()
        contact.phone = request.form.get('phone', '').strip()
        ct = request.form.get('contact_type', '').strip()
        cr = request.form.get('contact_role', '').strip()
        tl = request.form.get('trust_level', '').strip()
        contact.contact_type = ct if ct in CONTACT_TYPE_LABELS else None
        contact.contact_role = cr if cr in CONTACT_ROLE_LABELS else None
        contact.trust_level  = tl if tl in TRUST_LEVEL_LABELS else None
        new = {k: getattr(contact, k) for k in old}
        _audit('contact', contact.id, 'update', {k: (old[k], new[k]) for k in old})
        db.session.commit()
        flash('Kontaktní osoba byla upravena.', 'success')
        return redirect(url_for('client_detail', id=contact.client_id))
    return render_template('contact_form.html', client=contact.client, contact=contact)


@app.route('/contacts/<int:id>/delete', methods=['POST'])
@login_required
def delete_contact(id):
    contact = ContactPerson.query.get_or_404(id)
    client_id = contact.client_id
    contact_name = contact.name
    try:
        # Raw SQL — nejspolehlivější, obchází ORM cache
        db.session.execute(text('DELETE FROM deal_contact WHERE contact_id = :id'), {'id': id})
        db.session.execute(text('UPDATE interaction SET contact_person_id = NULL WHERE contact_person_id = :id'), {'id': id})
        db.session.execute(text('UPDATE client_news SET contact_id = NULL WHERE contact_id = :id'), {'id': id})
        db.session.flush()
        # Expiruj ORM cache, aby delete neviděl staré FK
        db.session.expire(contact)
        contact = ContactPerson.query.get(id)
        _audit('contact', id, 'delete')
        db.session.delete(contact)
        db.session.commit()
        flash(f'Kontaktní osoba „{contact_name}" byla smazána.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {e}', 'danger')
    return redirect(url_for('client_detail', id=client_id))


# ── Routes: HR hledání + Export ─────────────────────────────────────────────

@app.route('/clients/<int:id>/find-hr', methods=['POST'])
@login_required
def find_hr(id):
    client = Client.query.get_or_404(id)
    url = client.website.strip() if client.website else ''
    if not url:
        flash('Klient nemá vyplněný web — nelze hledat HR kontakty.', 'warning')
        return redirect(url_for('client_detail', id=id))

    try:
        hr_contacts = _find_hr_contacts(url, client.company or client.name)
        added = 0
        for c in hr_contacts:
            # Nepřidávej duplicity (stejný email)
            if c['email']:
                exists = ContactPerson.query.filter_by(
                    client_id=id, email=c['email']
                ).first()
                if exists:
                    continue
            contact = ContactPerson(
                client_id=id,
                name=c['name'],
                role=c['role'],
                email=c['email'],
            )
            db.session.add(contact)
            added += 1
        db.session.commit()
        if added:
            flash(f'Nalezeno a přidáno {added} HR kontaktů.', 'success')
        else:
            flash('HR kontakty již byly přidány nebo nebyly nalezeny.', 'warning')
    except Exception as e:
        flash(f'Chyba při hledání HR kontaktů: {e}', 'danger')
    return redirect(url_for('client_detail', id=id))


@app.route('/export/contacts')
@login_required
def export_contacts():
    import csv
    from io import StringIO
    from flask import Response

    client_id = request.args.get('client_id', type=int)
    query = ContactPerson.query.join(Client).order_by(Client.name, ContactPerson.name)
    if client_id:
        query = query.filter(ContactPerson.client_id == client_id)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Jméno', 'Email', 'Telefon', 'Pozice', 'Firma', 'IČO', 'Web firmy', 'Sídlo'])
    for c in query.all():
        writer.writerow([
            c.name,
            c.email or '',
            c.phone or '',
            c.role or '',
            c.client.company or c.client.name,
            c.client.ico or '',
            c.client.website or '',
            c.client.address or '',
        ])

    filename = f'kontakty_klient{client_id}.csv' if client_id else 'kontakty_vsichni.csv'
    return Response(
        '\ufeff' + output.getvalue(),   # BOM pro správné zobrazení v Excelu
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ── Routes: Obchody (Deals) ─────────────────────────────────────────────────

@app.route('/deals')
@login_required
def deals():
    q             = request.args.get('q', '').strip()
    owner_filter  = request.args.get('owner', '').strip()
    status_filter = request.args.get('status', '').strip()
    group         = request.args.get('group', '').strip()  # active | running | inactive | ''

    def _fetch(statuses):
        qry = Deal.query.join(Client).filter(Deal.status.in_(statuses))
        if q:
            qry = qry.filter(Client.name.ilike(f'%{q}%') | Deal.title.ilike(f'%{q}%'))
        if owner_filter:
            qry = qry.filter(Deal.owner_id == int(owner_filter))
        if status_filter and status_filter in statuses:
            qry = qry.filter(Deal.status == status_filter)
        return qry.order_by(Deal.updated_at.desc()).all()

    LIMIT = 10
    active_all   = _fetch(PIPELINE_ACTIVE)
    active_all.sort(key=lambda d: (
        PIPELINE_ACTIVE_DISPLAY_ORDER.get(d.status, 99),
        -(d.updated_at.timestamp() if d.updated_at else 0),
    ))
    running_all  = _fetch(PIPELINE_RUNNING)
    inactive_all = _fetch(PIPELINE_INACTIVE)

    members = TeamMember.query.order_by(TeamMember.name).all()
    return render_template('deals.html',
        active_deals   = active_all   if group == 'active'   else active_all[:LIMIT],
        active_total   = len(active_all),
        running_deals  = running_all  if group == 'running'  else running_all[:LIMIT],
        running_total  = len(running_all),
        inactive_deals = inactive_all if group == 'inactive' else inactive_all[:LIMIT],
        inactive_total = len(inactive_all),
        members=members,
        q=q, owner_filter=owner_filter, status_filter=status_filter, group=group,
    )


@app.route('/deals/new', methods=['GET', 'POST'])
@login_required
def new_deal():
    client_id = request.args.get('client_id', type=int)
    clients_list = Client.query.order_by(Client.name).all()
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        owner_id  = request.form.get('owner_id') or None
        client_id = int(request.form['client_id'])
        deal = Deal(
            client_id=client_id,
            title=request.form['title'].strip(),
            status=request.form.get('status', 'new_lead'),
            notes=request.form.get('notes', '').strip(),
            next_step=request.form.get('next_step', '').strip(),
            owner_id=int(owner_id) if owner_id else None,
            last_activity_at=datetime.utcnow(),
        )
        db.session.add(deal)
        db.session.flush()
        contact_ids = request.form.getlist('contact_ids')
        deal.contacts = ContactPerson.query.filter(ContactPerson.id.in_(
            [int(i) for i in contact_ids if i])).all()
        _audit('deal', deal.id, 'create')
        db.session.commit()
        flash(f'Obchod „{deal.title}" byl přidán.', 'success')
        return redirect(url_for('client_detail', id=client_id))
    # Pro nový obchod s předvybraným klientem načti jeho kontakty
    preselected_contacts = []
    if client_id:
        preselected_contacts = ContactPerson.query.filter_by(client_id=client_id).all()
    return render_template('deal_form.html', deal=None, clients=clients_list,
                           members=members, preselected_client_id=client_id,
                           client_contacts=preselected_contacts)


@app.route('/deals/<int:id>')
@login_required
def deal_detail(id):
    deal = Deal.query.get_or_404(id)
    audit_log = (AuditLog.query
                 .filter_by(entity_type='deal', entity_id=id)
                 .order_by(AuditLog.created_at.desc()).limit(30).all())
    return render_template('deal_detail.html', deal=deal, audit_log=audit_log)


@app.route('/deals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_deal(id):
    deal = Deal.query.get_or_404(id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    client_contacts = ContactPerson.query.filter_by(client_id=deal.client_id).all()
    if request.method == 'POST':
        old = {k: getattr(deal, k) for k in ('title', 'status', 'notes', 'next_step', 'owner_id')}
        deal.title     = request.form['title'].strip()
        deal.status    = request.form.get('status', deal.status)
        deal.notes     = request.form.get('notes', '').strip()
        deal.next_step = request.form.get('next_step', '').strip()
        owner_id = request.form.get('owner_id') or None
        deal.owner_id  = int(owner_id) if owner_id else None
        deal.updated_at = datetime.utcnow()
        deal.last_activity_at = datetime.utcnow()
        contact_ids = request.form.getlist('contact_ids')
        deal.contacts = ContactPerson.query.filter(ContactPerson.id.in_(
            [int(i) for i in contact_ids if i])).all()
        new = {k: getattr(deal, k) for k in old}
        _audit('deal', deal.id, 'update', {k: (old[k], new[k]) for k in old})
        db.session.commit()
        flash('Obchod byl upraven.', 'success')
        return redirect(url_for('client_detail', id=deal.client_id))
    return render_template('deal_form.html', deal=deal, members=members,
                           clients=None, preselected_client_id=deal.client_id,
                           client_contacts=client_contacts)


@app.route('/deals/<int:id>/delete', methods=['POST'])
@login_required
def delete_deal(id):
    deal = Deal.query.get_or_404(id)
    client_id = deal.client_id
    _audit('deal', id, 'delete')
    db.session.delete(deal)
    db.session.commit()
    flash('Obchod byl smazán.', 'warning')
    return redirect(url_for('client_detail', id=client_id))


# ── Routes: Novinky ─────────────────────────────────────────────────────────

@app.route('/novinky')
@login_required
def novinky():
    client_filter = request.args.get('client_id', type=int)
    show = request.args.get('show', 'unread')   # unread | all
    query = ClientNews.query
    if client_filter:
        query = query.filter_by(client_id=client_filter)
    if show == 'unread':
        query = query.filter_by(is_read=False)
    items = query.order_by(ClientNews.created_at.desc()).limit(200).all()
    clients_with_news = (db.session.query(Client)
                         .join(ClientNews, Client.id == ClientNews.client_id)
                         .distinct().order_by(Client.name).all())
    return render_template('novinky.html', items=items, show=show,
                           client_filter=client_filter,
                           clients_with_news=clients_with_news,
                           news_icons=NEWS_ICONS, news_labels=NEWS_LABELS)


@app.route('/novinky/mark-all-read', methods=['POST'])
@login_required
def novinky_mark_all_read():
    ClientNews.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('Vše označeno jako přečtené.', 'success')
    return redirect(url_for('novinky'))


@app.route('/novinky/<int:id>/mark-read', methods=['POST'])
@login_required
def novinky_mark_read(id):
    item = ClientNews.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('novinky'))


@app.route('/novinky/refresh', methods=['POST'])
@admin_required
def novinky_refresh():
    """Manuální spuštění aktualizace (admin only)."""
    import threading
    def run():
        weekly_refresh_all()
    threading.Thread(target=run, daemon=True).start()
    flash('Aktualizace spuštěna na pozadí. Výsledky se objeví za několik minut.', 'info')
    return redirect(url_for('novinky'))


@app.route('/admin/email-debug')
@admin_required
def email_debug():
    return {
        'GMAIL_USER_set': bool(os.environ.get('GMAIL_USER')),
        'GMAIL_PASS_set': bool(os.environ.get('GMAIL_PASS')),
        'DEBUG_EMAIL_set': bool(os.environ.get('DEBUG_EMAIL')),
        'DEBUG_EMAIL_value': os.environ.get('DEBUG_EMAIL', ''),
        'all_env_keys': [k for k in os.environ.keys() if 'GMAIL' in k or 'EMAIL' in k or 'DEBUG' in k],
    }


@app.route('/admin/test-email', methods=['POST'])
@admin_required
def test_email():
    """Odešle testovací e-mail pro ověření konfigurace (admin only)."""
    recipient = os.environ.get('TEST_EMAIL', '').strip()
    if not recipient:
        flash('Není nastavena proměnná TEST_EMAIL.', 'danger')
        return redirect(url_for('admin_users'))
    sent_to, error = _send_email(
        recipient,
        'Sales PD — test e-mailu',
        '<p>Ahoj,</p><p>tento e-mail potvrzuje, že odesílání z aplikace <strong>Sales PD</strong> funguje správně.</p><p style="color:#888;font-size:12px">— Sales PD</p>'
    )
    if error:
        flash(f'Chyba odesílání: {error}', 'danger')
    else:
        flash(f'Testovací e-mail odeslán na {sent_to}.', 'success')
    return redirect(url_for('admin_users'))


# ── Routes: Export klientů ───────────────────────────────────────────────────

@app.route('/export/clients')
@login_required
def export_clients():
    import csv
    from io import StringIO
    from flask import Response
    clients = Client.query.order_by(Client.name).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Název firmy', 'IČO', 'E-mail', 'Telefon', 'Web',
                     'Kategorie', 'Velikost', 'Kvalita velikosti', 'Sídlo',
                     'Pobočky', 'Pipeline', 'Vlastník', 'Statutáři',
                     'Počet kontaktů', 'Poznámky', 'Přidán'])
    for c in clients:
        owner_name = c.owner.name if c.owner else ''
        writer.writerow([
            c.company or c.name,
            c.ico or '',
            c.email or '',
            c.phone or '',
            c.website or '',
            TEMP_LABELS.get(c.temperature, '') if c.temperature else '',
            SIZE_LABELS.get(c.size_category, '') if c.size_category else '',
            SIZE_QUALITY_LABELS.get(c.size_quality, '') if c.size_quality else '',
            c.address or '',
            c.branches or '',
            PIPELINE_LABELS.get(c.pipeline_status, '') if c.pipeline_status else '',
            owner_name,
            c.statutory or '',
            len(c.contacts),
            c.notes or '',
            c.created_at.strftime('%d.%m.%Y'),
        ])
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=klienti.csv'}
    )


# ── Routes: Import klientů ──────────────────────────────────────────────────

@app.route('/import/clients', methods=['GET', 'POST'])
@login_required
def import_clients():
    import csv
    from io import StringIO, TextIOWrapper

    if request.method == 'GET':
        return render_template('import_clients.html')

    f = request.files.get('csvfile')
    if not f or not f.filename.endswith('.csv'):
        flash('Nahraj prosím soubor ve formátu .csv', 'danger')
        return redirect(url_for('import_clients'))

    try:
        stream = TextIOWrapper(f.stream, encoding='utf-8-sig')  # utf-8-sig zvládne BOM z Excelu
        reader = csv.DictReader(stream)

        EXPECTED = {'Název firmy', 'IČO', 'E-mail', 'Telefon', 'Web',
                    'Kategorie', 'Velikost', 'Poznámky'}
        if not EXPECTED.issubset(set(reader.fieldnames or [])):
            flash('Soubor nemá správné sloupce. Stáhni šablonu a použij ji.', 'danger')
            return redirect(url_for('import_clients'))

        added = skipped = errors = 0
        for row in reader:
            name = row['Název firmy'].strip()
            if not name:
                continue
            ico = row['IČO'].strip()

            # Kontrola duplicit — podle IČO (pokud je), jinak podle názvu
            if ico:
                exists = Client.query.filter_by(ico=ico).first()
            else:
                exists = Client.query.filter(Client.name.ilike(name)).first()
            if exists:
                skipped += 1
                continue

            temp_val = row['Kategorie'].strip().lower()
            size_val = row['Velikost'].strip().lower()

            try:
                client = Client(
                    name=name,
                    company=name,
                    ico=ico or None,
                    email=row['E-mail'].strip() or None,
                    phone=row['Telefon'].strip() or None,
                    website=row['Web'].strip() or None,
                    notes=row['Poznámky'].strip() or None,
                    temperature=temp_val if temp_val in TEMP_LABELS else None,
                    size_category=size_val if size_val in SIZE_LABELS else None,
                )
                db.session.add(client)
                db.session.flush()
                _audit('client', client.id, 'create')
                added += 1
            except Exception:
                errors += 1

        db.session.commit()

        parts = [f'Přidáno {added} klientů.']
        if skipped:
            parts.append(f'{skipped} přeskočeno (duplicita).')
        if errors:
            parts.append(f'{errors} chyb.')
        flash(' '.join(parts), 'success' if added else 'warning')

    except Exception as e:
        flash(f'Chyba při čtení souboru: {e}', 'danger')

    return redirect(url_for('clients'))


# ── Routes: Reminders ───────────────────────────────────────────────────────

@app.route('/reminders')
@login_required
def all_reminders():
    member_filter = request.args.get('member', '').strip()
    pending_q = Reminder.query.filter_by(done=False)
    if member_filter:
        pending_q = pending_q.filter_by(member_id=int(member_filter))
    pending = pending_q.order_by(Reminder.due_at).all()
    done_recent = (Reminder.query
                   .filter_by(done=True)
                   .order_by(Reminder.due_at.desc())
                   .limit(30).all())
    members = TeamMember.query.order_by(TeamMember.name).all()
    now = now_prague()
    return render_template('reminders.html', pending=pending, done_recent=done_recent,
                           members=members, now=now, member_filter=member_filter)


@app.route('/clients/<int:client_id>/reminders/new', methods=['GET', 'POST'])
@login_required
def new_reminder(client_id):
    client = Client.query.get_or_404(client_id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        due_str = request.form['due_at']
        due_at = datetime.strptime(due_str, '%Y-%m-%dT%H:%M')
        member_id = request.form.get('member_id') or None
        reminder = Reminder(
            client_id=client_id,
            member_id=int(member_id) if member_id else None,
            title=request.form['title'].strip(),
            due_at=due_at,
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(reminder)
        db.session.commit()
        flash('Reminder byl přidán.', 'success')
        return redirect(url_for('client_detail', id=client_id))
    default_due = datetime.now().strftime('%Y-%m-%dT%H:%M')
    return render_template('reminder_form.html', client=client, reminder=None,
                           members=members, default_due=default_due,
                           default_member_id=session.get('team_member_id'))


@app.route('/reminders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        reminder.title = request.form['title'].strip()
        due_str = request.form['due_at']
        reminder.due_at = datetime.strptime(due_str, '%Y-%m-%dT%H:%M')
        member_id = request.form.get('member_id') or None
        reminder.member_id = int(member_id) if member_id else None
        reminder.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Reminder byl upraven.', 'success')
        return redirect(url_for('client_detail', id=reminder.client_id))
    return render_template('reminder_form.html', client=reminder.client, reminder=reminder,
                           members=members,
                           default_due=reminder.due_at.strftime('%Y-%m-%dT%H:%M'))


@app.route('/reminders/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    reminder.done = not reminder.done
    db.session.commit()
    return redirect(request.referrer or url_for('client_detail', id=reminder.client_id))


@app.route('/reminders/<int:id>/delete', methods=['POST'])
@login_required
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    client_id = reminder.client_id
    db.session.delete(reminder)
    db.session.commit()
    flash('Reminder byl smazán.', 'warning')
    return redirect(request.referrer or url_for('client_detail', id=client_id))


# ── Routes: Interactions ────────────────────────────────────────────────────

@app.route('/interactions')
@login_required
def all_interactions():
    q          = request.args.get('q', '').strip()
    member_id  = request.args.get('member', '').strip()
    default_from = (now_prague() - timedelta(days=14)).strftime('%Y-%m-%d')
    date_from  = request.args.get('date_from', default_from).strip()
    date_to    = request.args.get('date_to', '').strip()

    query = Interaction.query.join(Client).join(TeamMember)
    if q:
        query = query.filter(
            Client.name.ilike(f'%{q}%') |
            Interaction.subject.ilike(f'%{q}%') |
            Interaction.notes.ilike(f'%{q}%')
        )
    if member_id:
        query = query.filter(Interaction.member_id == int(member_id))
    if date_from:
        try:
            query = query.filter(Interaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Interaction.date <= datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59))
        except ValueError:
            pass

    interactions = query.order_by(Interaction.date.desc()).limit(200).all()
    members = TeamMember.query.order_by(TeamMember.name).all()
    return render_template('all_interactions.html', interactions=interactions,
                           members=members, q=q, member_id=member_id,
                           date_from=date_from, date_to=date_to)


@app.route('/clients/<int:client_id>/interactions/new', methods=['GET', 'POST'])
@login_required
def new_interaction(client_id):
    client = Client.query.get_or_404(client_id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    contacts = ContactPerson.query.filter_by(client_id=client_id).order_by(ContactPerson.name).all()
    if request.method == 'POST':
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        contact_person_id = request.form.get('contact_person_id') or None
        interaction = Interaction(
            client_id=client_id,
            member_id=int(request.form['member_id']),
            contact_person_id=int(contact_person_id) if contact_person_id else None,
            date=date,
            method=request.form['method'],
            subject=request.form.get('subject', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(interaction)
        db.session.commit()
        flash('Kontakt byl zaznamenán.', 'success')
        return redirect(url_for('client_detail', id=client_id))
    return render_template('interaction_form.html', client=client, members=members,
                           contacts=contacts, interaction=None,
                           default_member_id=session.get('team_member_id'),
                           now=datetime.now().strftime('%Y-%m-%dT%H:%M'))


@app.route('/interactions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_interaction(id):
    interaction = Interaction.query.get_or_404(id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    contacts = ContactPerson.query.filter_by(client_id=interaction.client_id).order_by(ContactPerson.name).all()
    if request.method == 'POST':
        date_str = request.form['date']
        interaction.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        interaction.member_id = int(request.form['member_id'])
        contact_person_id = request.form.get('contact_person_id') or None
        interaction.contact_person_id = int(contact_person_id) if contact_person_id else None
        interaction.method = request.form['method']
        interaction.subject = request.form.get('subject', '').strip()
        interaction.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Kontakt byl upraven.', 'success')
        return redirect(url_for('client_detail', id=interaction.client_id))
    return render_template('interaction_form.html', client=interaction.client,
                           members=members, contacts=contacts, interaction=interaction,
                           now=interaction.date.strftime('%Y-%m-%dT%H:%M'))


@app.route('/interactions/<int:id>/delete', methods=['POST'])
@login_required
def delete_interaction(id):
    interaction = Interaction.query.get_or_404(id)
    client_id = interaction.client_id
    db.session.delete(interaction)
    db.session.commit()
    flash('Kontakt byl smazán.', 'warning')
    return redirect(url_for('client_detail', id=client_id))


# ── Routes: Team Members ────────────────────────────────────────────────────

@app.route('/team')
@login_required
def team():
    members = TeamMember.query.order_by(TeamMember.name).all()
    return render_template('team.html', members=members)


@app.route('/team/new', methods=['GET', 'POST'])
@login_required
def new_member():
    if request.method == 'POST':
        member = TeamMember(
            name=request.form['name'].strip(),
            email=request.form.get('email', '').strip(),
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Člen týmu „{member.name}" byl přidán.', 'success')
        return redirect(url_for('team'))
    return render_template('member_form.html', member=None)


@app.route('/team/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = TeamMember.query.get_or_404(id)
    if request.method == 'POST':
        member.name = request.form['name'].strip()
        member.email = request.form.get('email', '').strip()
        db.session.commit()
        flash('Člen týmu byl upraven.', 'success')
        return redirect(url_for('team'))
    return render_template('member_form.html', member=member)


@app.route('/team/<int:id>/delete', methods=['POST'])
@login_required
def delete_member(id):
    member = TeamMember.query.get_or_404(id)
    if member.interactions:
        flash('Nelze smazat — člen má zaznamenané kontakty.', 'danger')
        return redirect(url_for('team'))
    name = member.name
    db.session.delete(member)
    db.session.commit()
    flash(f'Člen „{name}" byl smazán.', 'warning')
    return redirect(url_for('team'))


# ── Automatická aktualizace klientů ─────────────────────────────────────────

NEWS_ICONS = {
    'address':    'bi-geo-alt',
    'size':       'bi-bar-chart',
    'statutory':  'bi-person-check',
    'hr_contact': 'bi-person-plus',
    'jobs':       'bi-briefcase',
}

NEWS_LABELS = {
    'address':    'Změna adresy',
    'size':       'Změna velikosti',
    'statutory':  'Změna statutárů',
    'hr_contact': 'Nový HR kontakt',
    'jobs':       'Nabídky práce',
}


def _news_exists(client_id, category, title, days=7):
    """Vrátí True pokud stejná novinka již existuje v posledních N dnech."""
    from datetime import timedelta
    cutoff = now_prague() - timedelta(days=days)
    return ClientNews.query.filter(
        ClientNews.client_id == client_id,
        ClientNews.category  == category,
        ClientNews.title     == title,
        ClientNews.created_at >= cutoff,
    ).first() is not None


def _refresh_client_news(client):
    """Porovná aktuální data klienta s čerstvě načtenými, vytvoří novinky o změnách."""
    new_items = []

    # ── 1. ARES ──────────────────────────────────────────────────────────────
    if client.ico:
        try:
            ico = client.ico.strip()
            resp = _fetch(f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}',
                          timeout=10)
            if resp and resp.status_code == 200:
                data = resp.json()
                sidlo = data.get('sidlo') or {}
                new_addr = sidlo.get('textovaAdresa', '').strip()
                if new_addr and new_addr != (client.address or '').strip():
                    title = 'Změna adresy sídla'
                    if not _news_exists(client.id, 'address', title):
                        new_items.append(ClientNews(
                            client_id=client.id, category='address', title=title,
                            body=f'Dříve: {client.address or "—"}\nNově: {new_addr}',
                            priority='low', source='ares', confidence='high',
                            requires_action=False,
                            old_value=client.address or '', new_value=new_addr))
                    client.address = new_addr

            # Statutáři + velikost z kurzy.cz
            statutory, size = _scrape_statutory_and_size(ico)
            if statutory and statutory.strip() != (client.statutory or '').strip():
                title = 'Změna statutárních zástupců'
                if not _news_exists(client.id, 'statutory', title):
                    new_items.append(ClientNews(
                        client_id=client.id, category='statutory', title=title,
                        body=statutory[:500],
                        priority='medium', source='kurzy_cz', confidence='high',
                        requires_action=False,
                        old_value=client.statutory or '', new_value=statutory[:500]))
                client.statutory = statutory
            if size and size != client.size_category:
                old_label = SIZE_LABELS.get(client.size_category, client.size_category or '—')
                new_label = SIZE_LABELS.get(size, size)
                title = f'Změna velikosti: {old_label} → {new_label}'
                if not _news_exists(client.id, 'size', title):
                    new_items.append(ClientNews(
                        client_id=client.id, category='size', title=title,
                        priority='medium', source='kurzy_cz', confidence='high',
                        requires_action=False,
                        old_value=old_label, new_value=new_label))
                client.size_category = size
        except Exception:
            pass

    # ── 2. Nové HR kontakty ───────────────────────────────────────────────────
    if client.website:
        try:
            found = _find_hr_contacts(client.website, client.company or client.name)
            for c in found:
                if not c.get('email'):
                    continue
                exists = ContactPerson.query.filter_by(
                    client_id=client.id, email=c['email']).first()
                if not exists:
                    new_contact = ContactPerson(
                        client_id=client.id, name=c['name'],
                        role=c['role'], email=c['email'],
                        contact_type='estimated_email', contact_role='hr',
                        trust_level='auto')
                    db.session.add(new_contact)
                    title = f'Nový HR kontakt: {c["name"]}'
                    if not _news_exists(client.id, 'hr_contact', title):
                        new_items.append(ClientNews(
                            client_id=client.id, category='hr_contact', title=title,
                            body=f'{c["role"] or ""}\n{c["email"]}',
                            priority='high', source='hr_finder', confidence='medium',
                            requires_action=True,
                            recommended_action='Ověřit kontakt a oslovit'))
        except Exception:
            pass

    # ── 3. Nabídky práce (indikátor náboru) ──────────────────────────────────
    if client.website:
        try:
            resp = _fetch(client.website, timeout=10)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                career_url = _find_career_url(soup, client.website)
                if career_url:
                    cresp = _fetch(career_url, timeout=10)
                    if cresp and cresp.status_code == 200:
                        csoup = BeautifulSoup(cresp.content, 'html.parser')
                        texts = [t.get_text(strip=True) for t in
                                 csoup.find_all(['h2', 'h3', 'h4', 'li', 'a'])]
                        job_count = sum(1 for t in texts if _looks_like_job(t))
                        if job_count > 0:
                            title = f'Aktivní nábor: {job_count} nabídek práce'
                            if not _news_exists(client.id, 'jobs', title):
                                new_items.append(ClientNews(
                                    client_id=client.id, category='jobs', title=title,
                                    body=f'Kariérní stránka: {career_url}',
                                    priority='high', source='website', confidence='medium',
                                    requires_action=True,
                                    recommended_action='Firma aktivně nabírá — vhodný čas na oslovení'))
        except Exception:
            pass

    client.last_refreshed_at = datetime.utcnow()
    for item in new_items:
        db.session.add(item)
    return new_items


def weekly_refresh_all():
    """Spouštěno APSchedulerem každou neděli — aktualizuje data všech klientů."""
    with app.app_context():
        clients = Client.query.filter(
            (Client.ico.isnot(None)) | (Client.website.isnot(None))
        ).all()
        for client in clients:
            try:
                _refresh_client_news(client)
                db.session.commit()
            except Exception:
                db.session.rollback()


# ── Routes: Admin — správa uživatelů ────────────────────────────────────────

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/login-log')
@admin_required
def admin_login_log():
    logs = (LoginLog.query
            .order_by(LoginLog.created_at.desc())
            .limit(200).all())
    return render_template('admin_login_log.html', logs=logs)


@app.route('/admin/audit-log')
@admin_required
def admin_audit_log():
    entity_type = request.args.get('entity_type', '').strip()
    user_id     = request.args.get('user_id', '').strip()
    query = AuditLog.query
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if user_id:
        query = query.filter_by(user_id=int(user_id))
    logs  = query.order_by(AuditLog.created_at.desc()).limit(300).all()
    users = User.query.order_by(User.username).all()
    return render_template('admin_audit_log.html', logs=logs, users=users,
                           entity_type=entity_type, user_id=user_id)


@app.route('/report')
@login_required
def report():
    period = request.args.get('period', 'month')  # week, month, quarter
    now = now_prague()
    if period == 'week':
        since = now - timedelta(days=7)
        label = 'Tento týden'
    elif period == 'quarter':
        since = now - timedelta(days=90)
        label = 'Poslední čtvrtletí'
    else:
        since = now - timedelta(days=30)
        label = 'Posledních 30 dní'

    members = TeamMember.query.order_by(TeamMember.name).all()
    stats = []
    for m in members:
        interactions = Interaction.query.filter(
            Interaction.member_id == m.id,
            Interaction.date >= since).count()
        deals_active = Deal.query.filter(
            Deal.owner_id == m.id,
            Deal.status.notin_(['won', 'lost', 'blacklist'])).count()
        deals_won = Deal.query.filter(
            Deal.owner_id == m.id,
            Deal.status == 'won',
            Deal.updated_at >= since).count()
        clients_added = Client.query.filter(
            Client.owner_id == m.id,
            Client.created_at >= since).count()
        stats.append({
            'member': m,
            'interactions': interactions,
            'deals_active': deals_active,
            'deals_won': deals_won,
            'clients_added': clients_added,
        })

    # Pipeline přehled
    pipeline_counts = {}
    for key in PIPELINE_LABELS:
        pipeline_counts[key] = Deal.query.filter_by(status=key).count()

    return render_template('report.html', stats=stats, period=period, label=label,
                           pipeline_counts=pipeline_counts)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@admin_required
def admin_new_user():
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = bool(request.form.get('is_admin'))
        tm_id    = request.form.get('team_member_id') or None
        if not username or not password:
            flash('Uživatelské jméno a heslo jsou povinné.', 'danger')
            return render_template('admin_user_form.html', user=None, members=members)
        if User.query.filter_by(username=username).first():
            flash(f'Uživatel „{username}" již existuje.', 'danger')
            return render_template('admin_user_form.html', user=None, members=members)
        user = User(username=username,
                    password_hash=generate_password_hash(password),
                    is_admin=is_admin,
                    is_active=True,
                    team_member_id=int(tm_id) if tm_id else None)
        db.session.add(user)
        db.session.commit()
        flash(f'Uživatel „{username}" byl vytvořen.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin_user_form.html', user=None, members=members)


@app.route('/admin/users/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(id):
    user = User.query.get_or_404(id)
    members = TeamMember.query.order_by(TeamMember.name).all()
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        # Admin nemůže sám sobě odebrat admin práva ani deaktivovat sám sebe
        if user.id != session['user_id']:
            user.is_admin  = bool(request.form.get('is_admin'))
            user.is_active = bool(request.form.get('is_active'))
        tm_id = request.form.get('team_member_id') or None
        user.team_member_id = int(tm_id) if tm_id else None
        db.session.commit()
        # Aktualizuj session pokud admin mění sám sebe
        if user.id == session['user_id']:
            session['team_member_id'] = user.team_member_id
        flash(f'Uživatel „{user.username}" byl upraven.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin_user_form.html', user=user, members=members)


@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        flash('Nemůžeš smazat sám sebe.', 'danger')
        return redirect(url_for('admin_users'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Uživatel „{username}" byl smazán.', 'warning')
    return redirect(url_for('admin_users'))


# ── Init ────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    # Migrace — přidej sloupce, které v starší DB chybí
    # PostgreSQL: IF NOT EXISTS zabrání chybě při opakovaném spuštění
    is_pg = 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']
    if is_pg:
        migrations = [
            'ALTER TABLE interaction ADD COLUMN IF NOT EXISTS contact_person_id INTEGER REFERENCES contact_person(id)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS ico VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS website VARCHAR(500)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS web_description TEXT',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS address VARCHAR(500)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS statutory TEXT',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS branches TEXT',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS size_category VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS temperature VARCHAR(10)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMP',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS team_member_id INTEGER REFERENCES team_member(id)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS size_quality VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS pipeline_status VARCHAR(30)',
            'ALTER TABLE client ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES team_member(id)',
            'ALTER TABLE contact_person ADD COLUMN IF NOT EXISTS contact_type VARCHAR(30)',
            'ALTER TABLE contact_person ADD COLUMN IF NOT EXISTS contact_role VARCHAR(20)',
            'ALTER TABLE contact_person ADD COLUMN IF NOT EXISTS trust_level VARCHAR(20)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS priority VARCHAR(10)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS source VARCHAR(50)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS old_value TEXT',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS new_value TEXT',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS confidence VARCHAR(10)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS requires_action BOOLEAN',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS recommended_action VARCHAR(300)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contact_person(id)',
            'ALTER TABLE client_news ADD COLUMN IF NOT EXISTS deal_id INTEGER REFERENCES deal(id)',
            'ALTER TABLE reminder ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT FALSE',
            'ALTER TABLE reminder ADD COLUMN IF NOT EXISTS notified_day BOOLEAN DEFAULT FALSE',
        ]
    else:
        migrations = [
            'ALTER TABLE interaction ADD COLUMN contact_person_id INTEGER REFERENCES contact_person(id)',
            'ALTER TABLE client ADD COLUMN ico VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN website VARCHAR(500)',
            'ALTER TABLE client ADD COLUMN web_description TEXT',
            'ALTER TABLE client ADD COLUMN address VARCHAR(500)',
            'ALTER TABLE client ADD COLUMN statutory TEXT',
            'ALTER TABLE client ADD COLUMN branches TEXT',
            'ALTER TABLE client ADD COLUMN size_category VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN temperature VARCHAR(10)',
            'ALTER TABLE client ADD COLUMN last_refreshed_at DATETIME',
            'ALTER TABLE user ADD COLUMN team_member_id INTEGER REFERENCES team_member(id)',
            'ALTER TABLE client ADD COLUMN size_quality VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN pipeline_status VARCHAR(30)',
            'ALTER TABLE client ADD COLUMN owner_id INTEGER REFERENCES team_member(id)',
            'ALTER TABLE contact_person ADD COLUMN contact_type VARCHAR(30)',
            'ALTER TABLE contact_person ADD COLUMN contact_role VARCHAR(20)',
            'ALTER TABLE contact_person ADD COLUMN trust_level VARCHAR(20)',
            'ALTER TABLE client_news ADD COLUMN priority VARCHAR(10)',
            'ALTER TABLE client_news ADD COLUMN source VARCHAR(50)',
            'ALTER TABLE client_news ADD COLUMN old_value TEXT',
            'ALTER TABLE client_news ADD COLUMN new_value TEXT',
            'ALTER TABLE client_news ADD COLUMN confidence VARCHAR(10)',
            'ALTER TABLE client_news ADD COLUMN requires_action BOOLEAN',
            'ALTER TABLE client_news ADD COLUMN recommended_action VARCHAR(300)',
            'ALTER TABLE client_news ADD COLUMN contact_id INTEGER REFERENCES contact_person(id)',
            'ALTER TABLE client_news ADD COLUMN deal_id INTEGER REFERENCES deal(id)',
            'ALTER TABLE reminder ADD COLUMN notified BOOLEAN DEFAULT 0',
            'ALTER TABLE reminder ADD COLUMN notified_day BOOLEAN DEFAULT 0',
        ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                conn.rollback()
    # Vytvoř výchozího admina, pokud žádný uživatel neexistuje
    if User.query.count() == 0:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('ProlusiDynamika'),
            is_admin=True,
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()

# ── E-mail helpers ───────────────────────────────────────────────────────────

def _send_email(to: str, subject: str, body_html: str):
    """Odešle e-mail přes Resend API."""
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        return None, 'Chybí RESEND_API_KEY'
    recipient = to
    if not recipient:
        return None, 'Chybí příjemce'
    try:
        resp = requests.post(
            'https://api.resend.com/emails',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'from': 'Sales PD <noreply@prolus.cz>', 'to': [recipient],
                  'subject': subject, 'html': body_html},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return recipient, None
        return None, f'Resend API chyba {resp.status_code}: {resp.text}'
    except Exception as e:
        app.logger.error(f'[email] Chyba odesílání na {recipient}: {e}')
        return None, str(e)


def _reminder_notify():
    """Pošle upozornění na remindry — den předem a hodinu předem."""
    with app.app_context():
        now = now_prague()

        def _send_reminder(r, label):
            if not r.assigned_member or not r.assigned_member.email:
                return
            due_str = r.due_at.strftime('%d.%m.%Y %H:%M')
            client_name = r.client.name if r.client else '—'
            notes_row = f'<tr><td style="padding:4px 12px 4px 0;color:#666;font-weight:bold">Poznámka:</td><td>{r.notes}</td></tr>' if r.notes else ''
            body = f"""
<p>Ahoj,</p>
<p>připomínáme reminder, který máš <strong>{label}</strong>:</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:4px 12px 4px 0;color:#666;font-weight:bold">Klient:</td><td>{client_name}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666;font-weight:bold">Název:</td><td>{r.title}</td></tr>
  <tr><td style="padding:4px 12px 4px 0;color:#666;font-weight:bold">Termín:</td><td>{due_str}</td></tr>
  {notes_row}
</table>
<p style="color:#888;font-size:12px">— Sales PD</p>
"""
            _send_email(r.assigned_member.email, f'⏰ Reminder: {r.title} ({due_str})', body)

        # Upozornění den předem (24–25 hodin)
        day_reminders = Reminder.query.filter(
            Reminder.done == False,
            Reminder.notified_day == False,
            Reminder.due_at >= now + timedelta(hours=24),
            Reminder.due_at <= now + timedelta(hours=25),
        ).all()
        for r in day_reminders:
            _send_reminder(r, 'za 1 den')
            r.notified_day = True

        # Upozornění hodinu předem (1–2 hodiny)
        hour_reminders = Reminder.query.filter(
            Reminder.done == False,
            Reminder.notified == False,
            Reminder.due_at >= now + timedelta(hours=1),
            Reminder.due_at <= now + timedelta(hours=2),
        ).all()
        for r in hour_reminders:
            _send_reminder(r, 'za méně než hodinu')
            r.notified = True

        db.session.commit()


def _weekly_digest():
    """Každé pondělí ráno pošle souhrn novinek z posledního týdne všem členům týmu."""
    with app.app_context():
        since = now_prague() - timedelta(days=7)
        items = (ClientNews.query
                 .filter(ClientNews.created_at >= since)
                 .order_by(ClientNews.client_id, ClientNews.created_at.desc())
                 .all())
        if not items:
            return
        members = TeamMember.query.filter(TeamMember.email.isnot(None)).all()
        if not members:
            return

        rows = ''
        for item in items:
            priority_color = {'high': '#dc3545', 'medium': '#fd7e14', 'low': '#6c757d'}.get(item.priority, '#6c757d')
            rows += f"""
<tr>
  <td style="padding:6px 10px;border-bottom:1px solid #eee">{item.client.name}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee">{NEWS_LABELS.get(item.category, item.category)}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee">{item.title}</td>
  <td style="padding:6px 10px;border-bottom:1px solid #eee;color:{priority_color};font-weight:bold">
    {NEWS_PRIORITY_LABELS.get(item.priority, '')}
  </td>
</tr>"""

        body = f"""
<p>Ahoj,</p>
<p>zde je přehled novinek z posledního týdne ({since.strftime('%d.%m.')} – {now_prague().strftime('%d.%m.%Y')}):</p>
<table style="border-collapse:collapse;width:100%;font-size:14px">
  <thead>
    <tr style="background:#f5f7fa;color:#666;text-transform:uppercase;font-size:12px">
      <th style="padding:8px 10px;text-align:left">Firma</th>
      <th style="padding:8px 10px;text-align:left">Typ</th>
      <th style="padding:8px 10px;text-align:left">Novinka</th>
      <th style="padding:8px 10px;text-align:left">Priorita</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
<p style="margin-top:16px;color:#888;font-size:12px">— Sales PD</p>
"""
        count = len(items)
        noun = 'novinka' if count == 1 else 'novinky' if count < 5 else 'novinek'
        subject = f'\U0001f4f0 T\u00fddenn\u00ed p\u0159ehled novinek ({count} {noun})'
        for m in members:
            _send_email(m.email, subject, body)


# ── Routes: Clusters ────────────────────────────────────────────────────────

CLUSTER_COLORS = ['primary', 'success', 'danger', 'warning', 'info', 'secondary',
                  'dark', 'indigo', 'teal', 'orange']

@app.route('/clusters')
@login_required
def clusters():
    all_clusters = Cluster.query.order_by(Cluster.name).all()
    return render_template('clusters.html', clusters=all_clusters)


@app.route('/clusters/new', methods=['GET', 'POST'])
@login_required
def new_cluster():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        desc  = request.form.get('description', '').strip()
        color = request.form.get('color', 'primary').strip()
        if not name:
            flash('Název clusteru je povinný.', 'danger')
            return redirect(url_for('new_cluster'))
        cluster = Cluster(name=name, description=desc or None, color=color)
        db.session.add(cluster)
        db.session.commit()
        flash(f'Cluster „{cluster.name}" byl vytvořen.', 'success')
        return redirect(url_for('cluster_detail', id=cluster.id))
    return render_template('cluster_form.html', cluster=None, colors=CLUSTER_COLORS)


@app.route('/clusters/<int:id>')
@login_required
def cluster_detail(id):
    cluster = Cluster.query.get_or_404(id)
    # All clients for the assign-modal
    all_clients = Client.query.order_by(Client.name).all()
    return render_template('cluster_detail.html', cluster=cluster, all_clients=all_clients)


@app.route('/clusters/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_cluster(id):
    cluster = Cluster.query.get_or_404(id)
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        desc  = request.form.get('description', '').strip()
        color = request.form.get('color', 'primary').strip()
        if not name:
            flash('Název clusteru je povinný.', 'danger')
            return redirect(url_for('edit_cluster', id=id))
        cluster.name        = name
        cluster.description = desc or None
        cluster.color       = color
        db.session.commit()
        flash(f'Cluster „{cluster.name}" byl uložen.', 'success')
        return redirect(url_for('cluster_detail', id=cluster.id))
    return render_template('cluster_form.html', cluster=cluster, colors=CLUSTER_COLORS)


@app.route('/clusters/<int:id>/delete', methods=['POST'])
@login_required
def delete_cluster(id):
    cluster = Cluster.query.get_or_404(id)
    name = cluster.name
    try:
        db.session.execute(text('DELETE FROM client_cluster WHERE cluster_id = :id'), {'id': id})
        db.session.flush()
        db.session.delete(cluster)
        db.session.commit()
        flash(f'Cluster „{name}" byl smazán.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {e}', 'danger')
    return redirect(url_for('clusters'))


@app.route('/clusters/<int:id>/set-clients', methods=['POST'])
@login_required
def cluster_set_clients(id):
    """Uloží seznam klientů patřících do clusteru (z checkboxů)."""
    cluster = Cluster.query.get_or_404(id)
    selected_ids = request.form.getlist('client_ids', type=int)
    cluster.clients = Client.query.filter(Client.id.in_(selected_ids)).all() if selected_ids else []
    db.session.commit()
    flash('Klienti v clusteru aktualizováni.', 'success')
    return redirect(url_for('cluster_detail', id=id))


@app.route('/clients/<int:id>/set-clusters', methods=['POST'])
@login_required
def client_set_clusters(id):
    """Uloží clustery klienta (voláno z detailu klienta)."""
    client = Client.query.get_or_404(id)
    selected_ids = request.form.getlist('cluster_ids', type=int)
    client.clusters = Cluster.query.filter(Cluster.id.in_(selected_ids)).all() if selected_ids else []
    db.session.commit()
    flash('Clustery klienta aktualizovány.', 'success')
    return redirect(url_for('client_detail', id=id))


# ── APScheduler — týdenní refresh ────────────────────────────────────────────
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(weekly_refresh_all, 'cron', day_of_week='sun', hour=2, minute=0,
                  id='weekly_refresh', replace_existing=True)
scheduler.add_job(_reminder_notify, 'interval', minutes=15,
                  id='reminder_notify', replace_existing=True)
scheduler.add_job(_weekly_digest, 'cron', day_of_week='mon', hour=7, minute=0,
                  id='weekly_digest', replace_existing=True)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
