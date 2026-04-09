from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
from functools import wraps
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crm-secret-key-2024'

# ── Přihlášení ──────────────────────────────────────────────────────────────

LOGIN_USERNAME = 'admin'
LOGIN_PASSWORD = 'ProlusiDynamika'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        if (request.form['username'] == LOGIN_USERNAME and
                request.form['password'] == LOGIN_PASSWORD):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = 'Špatné jméno nebo heslo.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ── Models ─────────────────────────────────────────────────────────────────

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200))
    ico = db.Column(db.String(20))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(500))
    web_description = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interactions = db.relationship('Interaction', backref='client', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('ContactPerson', backref='client', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='client', lazy=True, cascade='all, delete-orphan')


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
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('team_member.id'), nullable=True)
    title = db.Column(db.String(300), nullable=False)
    due_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Routes: Dashboard ───────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    clients_count = Client.query.count()
    interactions_count = Interaction.query.count()
    pending_count = Reminder.query.filter_by(done=False).count()
    recent = (Interaction.query
              .order_by(Interaction.date.desc())
              .limit(10).all())
    upcoming = (Reminder.query
                .filter_by(done=False)
                .order_by(Reminder.due_at)
                .limit(5).all())
    return render_template('dashboard.html',
                           clients_count=clients_count,
                           interactions_count=interactions_count,
                           pending_count=pending_count,
                           recent=recent,
                           upcoming=upcoming,
                           now=datetime.utcnow())


# ── Routes: Clients ─────────────────────────────────────────────────────────

@app.route('/clients')
@login_required
def clients():
    q = request.args.get('q', '').strip()
    query = Client.query
    if q:
        query = query.filter(
            (Client.name.ilike(f'%{q}%')) |
            (Client.company.ilike(f'%{q}%')) |
            (Client.email.ilike(f'%{q}%'))
        )
    all_clients = query.order_by(Client.name).all()
    return render_template('clients.html', clients=all_clients, q=q)


@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    if request.method == 'POST':
        company = request.form.get('company', '').strip()
        client = Client(
            name=company,
            company=company,
            ico=request.form.get('ico', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            website=request.form.get('website', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Klient „{client.name}" byl přidán.', 'success')
        return redirect(url_for('client_detail', id=client.id))
    return render_template('client_form.html', client=None)


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
    members = TeamMember.query.order_by(TeamMember.name).all()
    now = datetime.utcnow()
    return render_template('client_detail.html', client=client,
                           interactions=interactions, reminders=reminders,
                           members=members, now=now)


@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        company = request.form.get('company', '').strip()
        client.name = company
        client.company = company
        client.ico = request.form.get('ico', '').strip()
        client.email = request.form.get('email', '').strip()
        client.phone = request.form.get('phone', '').strip()
        client.website = request.form.get('website', '').strip()
        client.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Klient byl upraven.', 'success')
        return redirect(url_for('client_detail', id=client.id))
    return render_template('client_form.html', client=client)


@app.route('/clients/<int:id>/load-ares', methods=['POST'])
@login_required
def load_ares(id):
    client = Client.query.get_or_404(id)
    ico = client.ico.strip() if client.ico else ''
    if not ico:
        flash('Nejdříve zadej IČO a ulož klienta.', 'warning')
        return redirect(url_for('client_detail', id=id))
    proxies = {
        'http': 'http://proxy.server:3128',
        'https': 'http://proxy.server:3128',
    }
    try:
        resp = requests.get(
            f'https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}',
            timeout=10,
            proxies=proxies,
        )
        if resp.status_code == 404:
            flash('IČO nebylo nalezeno v ARES.', 'danger')
            return redirect(url_for('client_detail', id=id))
        resp.raise_for_status()
        data = resp.json()
        nazev = data.get('obchodniJmeno', '')
        adresa = (data.get('sidlo') or {}).get('textovaAdresa', '')
        if nazev:
            client.name = nazev
            client.company = nazev
        if adresa and not client.notes:
            client.notes = adresa
        db.session.commit()
        flash(f'Údaje z ARES načteny: {nazev}', 'success')
    except Exception as e:
        flash(f'Chyba při načítání z ARES: {e}', 'danger')
    return redirect(url_for('client_detail', id=id))


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
    proxies = {
        'http': 'http://proxy.server:3128',
        'https': 'http://proxy.server:3128',
    }
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, proxies=proxies)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        description = ''
        meta = soup.find('meta', attrs={'name': 'description'}) or \
               soup.find('meta', attrs={'property': 'og:description'})
        if meta and meta.get('content'):
            description = meta['content'].strip()
        if not description:
            title = soup.title.string.strip() if soup.title else ''
            paras = [p.get_text(' ', strip=True) for p in soup.find_all('p') if len(p.get_text()) > 60]
            description = title + ('\n' + paras[0] if paras else '')
        client.web_description = description[:1000]
        db.session.commit()
        flash('Popis webu byl načten.', 'success')
    except Exception as e:
        flash(f'Chyba při načítání webu: {e}', 'danger')
    return redirect(url_for('client_detail', id=id))


@app.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    name = client.name
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
        contact = ContactPerson(
            client_id=client_id,
            name=request.form['name'].strip(),
            role=request.form.get('role', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
        )
        db.session.add(contact)
        db.session.commit()
        flash(f'Kontaktní osoba „{contact.name}" byla přidána.', 'success')
        return redirect(url_for('client_detail', id=client_id))
    return render_template('contact_form.html', client=client, contact=None)


@app.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
    contact = ContactPerson.query.get_or_404(id)
    if request.method == 'POST':
        contact.name = request.form['name'].strip()
        contact.role = request.form.get('role', '').strip()
        contact.email = request.form.get('email', '').strip()
        contact.phone = request.form.get('phone', '').strip()
        db.session.commit()
        flash('Kontaktní osoba byla upravena.', 'success')
        return redirect(url_for('client_detail', id=contact.client_id))
    return render_template('contact_form.html', client=contact.client, contact=contact)


@app.route('/contacts/<int:id>/delete', methods=['POST'])
@login_required
def delete_contact(id):
    contact = ContactPerson.query.get_or_404(id)
    client_id = contact.client_id
    db.session.delete(contact)
    db.session.commit()
    flash('Kontaktní osoba byla smazána.', 'warning')
    return redirect(url_for('client_detail', id=client_id))


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
    now = datetime.utcnow()
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
                           members=members, default_due=default_due)


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


# ── Init ────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    with db.engine.connect() as conn:
        for sql in [
            'ALTER TABLE interaction ADD COLUMN contact_person_id INTEGER REFERENCES contact_person(id)',
            'ALTER TABLE client ADD COLUMN ico VARCHAR(20)',
            'ALTER TABLE client ADD COLUMN website VARCHAR(500)',
            'ALTER TABLE client ADD COLUMN web_description TEXT',
        ]:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
