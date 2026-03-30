from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
import json, os, uuid

app = Flask(__name__)
app.secret_key = 'collabhub_secret_key_2024'
app.jinja_env.globals['enumerate'] = enumerate
app.jinja_env.filters['max'] = max
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

# ── Badge definitions ─────────────────────────────────────
BADGES = {
    'first_post':     {'icon':'🗣️',  'name':'First Post',      'desc':'Posted to the community feed'},
    'team_player':    {'icon':'🤝',  'name':'Team Player',     'desc':'Joined your first project'},
    'note_taker':     {'icon':'📝',  'name':'Note Taker',      'desc':'Created 5 sticky notes'},
    'task_master':    {'icon':'✅',  'name':'Task Master',     'desc':'Completed 10 tasks'},
    'helper':         {'icon':'📚',  'name':'Helper',          'desc':'Shared 3 materials'},
    'communicator':   {'icon':'💬',  'name':'Communicator',    'desc':'Sent 20 messages'},
    'project_lead':   {'icon':'🚀',  'name':'Project Lead',    'desc':'Created a project'},
    'course_star':    {'icon':'⭐',  'name':'Course Star',     'desc':'Joined a course room'},
    'poll_master':    {'icon':'🗳️',  'name':'Poll Master',     'desc':'Created a poll'},
    'showcase':       {'icon':'🏆',  'name':'Showcase Star',   'desc':'Project featured in showcase'},
}

XP_TABLE = {
    'post':10, 'join_project':15, 'create_project':25, 'share_material':10,
    'complete_task':5, 'send_message':2, 'add_note':3, 'join_room':10,
    'create_poll':8, 'vote_poll':3, 'showcase':20
}

def level_from_xp(xp):
    if xp < 50:   return 1
    if xp < 150:  return 2
    if xp < 300:  return 3
    if xp < 500:  return 4
    if xp < 750:  return 5
    if xp < 1100: return 6
    if xp < 1500: return 7
    return 8

def xp_for_next(xp):
    thresholds = [50,150,300,500,750,1100,1500,9999]
    for t in thresholds:
        if xp < t: return t
    return 9999

# ── Data helpers ──────────────────────────────────────────
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return ensure_keys(json.load(f))
    default = {
        "users": [
            {"id":"u1","name":"Alice Johnson","email":"alice@uni.edu","password":"password",
             "course":"Computer Science","year":3,"skills":["Python","React","ML"],"avatar":"AJ",
             "xp":120,"badges":["team_player","project_lead"],"bio":"Passionate about AI and web dev."},
            {"id":"u2","name":"Bob Smith","email":"bob@uni.edu","password":"password",
             "course":"Data Science","year":2,"skills":["SQL","Tableau","R"],"avatar":"BS",
             "xp":75,"badges":["team_player"],"bio":"Data nerd, love visualizations."},
            {"id":"u3","name":"Carol White","email":"carol@uni.edu","password":"password",
             "course":"Design","year":4,"skills":["Figma","CSS","Branding"],"avatar":"CW",
             "xp":200,"badges":["project_lead","helper","course_star"],"bio":"UX/UI designer & visual storyteller."}
        ],
        "projects": [
            {"id":"p1","title":"AI Study Assistant",
             "description":"An AI-powered study tool that helps students revise notes and quiz themselves.",
             "owner_id":"u1","members":["u1","u2"],"tags":["AI","Python","React"],
             "status":"Active","created_at":"2024-08-01","showcase":False,
             "kanban":{"todo":[],"inprogress":[],"done":[]}},
            {"id":"p2","title":"Campus Event App",
             "description":"A mobile-friendly web app to discover and RSVP for campus events.",
             "owner_id":"u3","members":["u3"],"tags":["Design","Flask","Bootstrap"],
             "status":"Recruiting","created_at":"2024-08-15","showcase":True,
             "kanban":{"todo":[],"inprogress":[],"done":[]}}
        ],
        "messages": [],
        "posts": [
            {"id":"m1","author_id":"u1","content":"Anyone working on NLP? Let's connect!",
             "created_at":"2024-08-10T10:00:00","likes":["u2"],"category":"general"},
            {"id":"m2","author_id":"u3","content":"Looking for a developer to join my Campus Event App!",
             "created_at":"2024-08-16T14:30:00","likes":[],"category":"recruiting"}
        ],
        "sticky_notes": [], "todos": [], "material_requests": [],
        "shared_materials": [], "direct_messages": [],
        "notifications": [],
        "course_rooms": [
            {"id":"r1","name":"Machine Learning","code":"CS401","members":["u1"],"posts":[],"resources":[]},
            {"id":"r2","name":"Data Visualization","code":"DS301","members":["u2","u3"],"posts":[],"resources":[]},
            {"id":"r3","name":"UI/UX Design","code":"DES201","members":["u3"],"posts":[],"resources":[]},
            {"id":"r4","name":"Web Development","code":"CS302","members":["u1","u3"],"posts":[],"resources":[]}
        ],
        "polls": [],
        "skill_matches": []
    }
    save(default)
    return default

def ensure_keys(data):
    defaults = {
        'sticky_notes':[],'todos':[],'material_requests':[],
        'shared_materials':[],'direct_messages':[],'notifications':[],
        'course_rooms':[],'polls':[],'skill_matches':[]
    }
    for k,v in defaults.items():
        if k not in data: data[k] = v
    for u in data.get('users',[]):
        if 'xp' not in u: u['xp'] = 0
        if 'badges' not in u: u['badges'] = []
        if 'bio' not in u: u['bio'] = ''
    for p in data.get('projects',[]):
        if 'showcase' not in p: p['showcase'] = False
        if 'kanban' not in p: p['kanban'] = {"todo":[],"inprogress":[],"done":[]}
    for post in data.get('posts',[]):
        if 'category' not in post: post['category'] = 'general'
    return data

def save(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_user(uid, data):
    return next((u for u in data['users'] if u['id'] == uid), None)

def add_xp(user, action, data):
    pts = XP_TABLE.get(action, 0)
    user['xp'] = user.get('xp', 0) + pts
    check_badges(user, data)

def check_badges(user, data):
    uid = user['id']
    badges = user.get('badges', [])
    # count user actions
    posts_count    = len([p for p in data['posts'] if p['author_id'] == uid])
    projects_owned = len([p for p in data['projects'] if p['owner_id'] == uid])
    projects_joined= len([p for p in data['projects'] if uid in p.get('members',[])])
    notes_count    = len([n for n in data['sticky_notes'] if n['user_id'] == uid])
    done_tasks     = len([t for t in data['todos'] if t['user_id'] == uid and t.get('done')])
    mats_shared    = len([m for m in data['shared_materials'] if m['uploaded_by'] == uid])
    msgs_sent      = len([m for m in data['messages'] if m['author_id'] == uid]) + \
                     len([m for m in data['direct_messages'] if m['from_id'] == uid])
    rooms_joined   = len([r for r in data['course_rooms'] if uid in r.get('members',[])])
    polls_created  = len([p for p in data['polls'] if p['author_id'] == uid])
    showcased      = any(p['showcase'] and p['owner_id'] == uid for p in data['projects'])

    new_badges = []
    if posts_count >= 1     and 'first_post'   not in badges: new_badges.append('first_post')
    if projects_joined >= 1 and 'team_player'  not in badges: new_badges.append('team_player')
    if notes_count >= 5     and 'note_taker'   not in badges: new_badges.append('note_taker')
    if done_tasks >= 10     and 'task_master'  not in badges: new_badges.append('task_master')
    if mats_shared >= 3     and 'helper'       not in badges: new_badges.append('helper')
    if msgs_sent >= 20      and 'communicator' not in badges: new_badges.append('communicator')
    if projects_owned >= 1  and 'project_lead' not in badges: new_badges.append('project_lead')
    if rooms_joined >= 1    and 'course_star'  not in badges: new_badges.append('course_star')
    if polls_created >= 1   and 'poll_master'  not in badges: new_badges.append('poll_master')
    if showcased            and 'showcase'     not in badges: new_badges.append('showcase')

    for b in new_badges:
        user['badges'].append(b)
        add_notification(data, uid, f"🏅 New badge earned: {BADGES[b]['name']} {BADGES[b]['icon']}", 'badge')

def add_notification(data, uid, message, ntype='info'):
    notif = {"id": str(uuid.uuid4())[:8], "user_id": uid, "message": message,
             "type": ntype, "read": False,
             "created_at": datetime.now().strftime('%Y-%m-%d %H:%M')}
    data['notifications'].append(notif)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Auth ──────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data  = load()
        email = request.form.get('email','').strip()
        pwd   = request.form.get('password','')
        user  = next((u for u in data['users'] if u['email']==email and u['password']==pwd), None)
        if user:
            session['user_id'] = user['id']
            flash('Welcome back, '+user['name'].split()[0]+'!','success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.','danger')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data   = load()
        name   = request.form.get('name','').strip()
        email  = request.form.get('email','').strip()
        pwd    = request.form.get('password','')
        course = request.form.get('course','').strip()
        year   = int(request.form.get('year',1))
        if any(u['email']==email for u in data['users']):
            flash('Email already registered.','danger')
            return render_template('register.html')
        initials = ''.join(p[0].upper() for p in name.split()[:2])
        user = {"id":str(uuid.uuid4())[:8],"name":name,"email":email,"password":pwd,
                "course":course,"year":year,"skills":[],"avatar":initials,
                "xp":0,"badges":[],"bio":""}
        data['users'].append(user)
        save(data)
        session['user_id'] = user['id']
        flash('Welcome to CollabHub, '+name.split()[0]+'!','success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Dashboard ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    data = load()
    uid  = session['user_id']
    user = get_user(uid, data)
    my_projects   = [p for p in data['projects'] if uid in p['members']]
    open_projects = [p for p in data['projects'] if p['status']=='Recruiting' and uid not in p['members']]
    posts = sorted(data['posts'], key=lambda x: x['created_at'], reverse=True)
    posts_rich = [{**p,'author':get_user(p['author_id'],data)} for p in posts]
    my_todos  = [t for t in data['todos'] if t['user_id']==uid]
    my_notes  = [n for n in data['sticky_notes'] if n['user_id']==uid]
    unread    = len([n for n in data['notifications'] if n['user_id']==uid and not n['read']])
    leaderboard = sorted(data['users'], key=lambda u: u.get('xp',0), reverse=True)[:5]
    return render_template('dashboard.html', user=user, my_projects=my_projects,
        open_projects=open_projects, posts=posts_rich, all_users=data['users'],
        my_todos=my_todos, my_notes=my_notes, unread=unread,
        leaderboard=leaderboard, BADGES=BADGES,
        level=level_from_xp(user.get('xp',0)),
        xp_next=xp_for_next(user.get('xp',0)))

# ── Notifications ─────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
    data = load()
    uid  = session['user_id']
    user = get_user(uid, data)
    my_notifs = [n for n in data['notifications'] if n['user_id']==uid]
    my_notifs.sort(key=lambda x: x['created_at'], reverse=True)
    for n in data['notifications']:
        if n['user_id'] == uid: n['read'] = True
    save(data)
    return render_template('notifications.html', user=user, notifications=my_notifs)

@app.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    data = load()
    uid  = session['user_id']
    data['notifications'] = [n for n in data['notifications'] if n['user_id']!=uid]
    save(data)
    return redirect(url_for('notifications'))

# ── Projects ──────────────────────────────────────────────
@app.route('/projects')
@login_required
def projects():
    data = load()
    user = get_user(session['user_id'], data)
    projects_rich = [{**p,'owner':get_user(p['owner_id'],data),
        'members_detail':[get_user(mid,data) for mid in p['members']]}
        for p in data['projects']]
    return render_template('projects.html', user=user, projects=projects_rich)

@app.route('/projects/new', methods=['GET','POST'])
@login_required
def new_project():
    data = load()
    user = get_user(session['user_id'], data)
    if request.method == 'POST':
        title  = request.form.get('title','').strip()
        desc   = request.form.get('description','').strip()
        tags   = [t.strip() for t in request.form.get('tags','').split(',') if t.strip()]
        status = request.form.get('status','Active')
        roles  = request.form.get('roles','').strip()
        proj = {"id":str(uuid.uuid4())[:8],"title":title,"description":desc,
                "owner_id":session['user_id'],"members":[session['user_id']],
                "tags":tags,"status":status,"roles":roles,
                "created_at":datetime.now().strftime('%Y-%m-%d'),
                "showcase":False,"kanban":{"todo":[],"inprogress":[],"done":[]}}
        data['projects'].append(proj)
        add_xp(user, 'create_project', data)
        save(data)
        flash('Project created!','success')
        return redirect(url_for('projects'))
    return render_template('new_project.html', user=user)

@app.route('/projects/<pid>/edit', methods=['GET','POST'])
@login_required
def edit_project(pid):
    data = load()
    user = get_user(session['user_id'], data)
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if not proj: return redirect(url_for('projects'))
    if proj['owner_id'] != session['user_id']:
        flash('Only the project admin can edit.','danger')
        return redirect(url_for('project_detail', pid=pid))
    if request.method == 'POST':
        proj['title']       = request.form.get('title',proj['title']).strip()
        proj['description'] = request.form.get('description',proj['description']).strip()
        proj['tags']        = [t.strip() for t in request.form.get('tags','').split(',') if t.strip()]
        proj['status']      = request.form.get('status',proj['status'])
        proj['roles']       = request.form.get('roles','').strip()
        save(data)
        flash('Project updated!','success')
        return redirect(url_for('project_detail', pid=pid))
    return render_template('edit_project.html', user=user, project=proj)

@app.route('/projects/<pid>/delete', methods=['POST'])
@login_required
def delete_project(pid):
    data = load()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj and proj['owner_id']==session['user_id']:
        data['projects'] = [p for p in data['projects'] if p['id']!=pid]
        data['messages'] = [m for m in data['messages'] if m.get('project_id')!=pid]
        save(data)
        flash('Project deleted.','success')
    return redirect(url_for('projects'))

@app.route('/projects/<pid>')
@login_required
def project_detail(pid):
    data = load()
    user = get_user(session['user_id'], data)
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if not proj:
        flash('Project not found.','danger')
        return redirect(url_for('projects'))
    owner   = get_user(proj['owner_id'], data)
    members = [get_user(mid,data) for mid in proj['members']]
    msgs    = [m for m in data['messages'] if m.get('project_id')==pid]
    for m in msgs: m['author'] = get_user(m['author_id'],data)
    materials = [m for m in data['shared_materials'] if m.get('project_id')==pid]
    for m in materials: m['uploader'] = get_user(m['uploaded_by'],data)
    mat_requests = [r for r in data['material_requests'] if r.get('project_id')==pid]
    for r in mat_requests: r['requester'] = get_user(r['user_id'],data)
    project_polls = [p for p in data['polls'] if p.get('project_id')==pid]
    kanban = proj.get('kanban', {"todo":[],"inprogress":[],"done":[]})
    return render_template('project_detail.html', user=user, project=proj,
        owner=owner, members=members, messages=msgs,
        materials=materials, mat_requests=mat_requests,
        project_polls=project_polls, kanban=kanban)

@app.route('/projects/<pid>/join', methods=['POST'])
@login_required
def join_project(pid):
    data = load()
    user = get_user(session['user_id'], data)
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj and session['user_id'] not in proj['members']:
        proj['members'].append(session['user_id'])
        add_xp(user, 'join_project', data)
        add_notification(data, proj['owner_id'],
            f"👤 {user['name']} joined your project '{proj['title']}'", 'join')
        save(data)
        flash('You joined the project!','success')
    return redirect(url_for('projects'))

@app.route('/projects/<pid>/leave', methods=['POST'])
@login_required
def leave_project(pid):
    data = load()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    uid  = session['user_id']
    if proj and uid in proj['members'] and uid != proj['owner_id']:
        proj['members'].remove(uid)
        save(data)
        flash('You left the project.','success')
    return redirect(url_for('projects'))

@app.route('/projects/<pid>/showcase', methods=['POST'])
@login_required
def toggle_showcase(pid):
    data = load()
    user = get_user(session['user_id'], data)
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj and proj['owner_id']==session['user_id']:
        proj['showcase'] = not proj.get('showcase', False)
        if proj['showcase']:
            add_xp(user, 'showcase', data)
        save(data)
    return redirect(url_for('project_detail', pid=pid))

@app.route('/projects/<pid>/message', methods=['POST'])
@login_required
def send_message(pid):
    data    = load()
    user    = get_user(session['user_id'], data)
    content = request.form.get('content','').strip()
    if content:
        msg = {"id":str(uuid.uuid4())[:8],"project_id":pid,
               "author_id":session['user_id'],"content":content,
               "created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        data['messages'].append(msg)
        add_xp(user, 'send_message', data)
        save(data)
    return redirect(url_for('project_detail', pid=pid))

# ── Kanban ────────────────────────────────────────────────
@app.route('/projects/<pid>/kanban/add', methods=['POST'])
@login_required
def kanban_add(pid):
    data  = load()
    proj  = next((p for p in data['projects'] if p['id']==pid), None)
    if proj and session['user_id'] in proj['members']:
        col   = request.form.get('col','todo')
        title = request.form.get('title','').strip()
        if title and col in proj['kanban']:
            card = {"id":str(uuid.uuid4())[:8],"title":title,
                    "author_id":session['user_id'],
                    "created_at":datetime.now().strftime('%Y-%m-%d')}
            proj['kanban'][col].append(card)
            save(data)
    return redirect(url_for('project_detail', pid=pid))

@app.route('/projects/<pid>/kanban/move', methods=['POST'])
@login_required
def kanban_move(pid):
    data   = load()
    proj   = next((p for p in data['projects'] if p['id']==pid), None)
    card_id= request.form.get('card_id')
    to_col = request.form.get('to_col')
    if proj and to_col in proj['kanban']:
        card = None
        for col in proj['kanban']:
            for c in proj['kanban'][col]:
                if c['id'] == card_id:
                    card = c
                    proj['kanban'][col].remove(c)
                    break
            if card: break
        if card:
            proj['kanban'][to_col].append(card)
            save(data)
    return redirect(url_for('project_detail', pid=pid))

@app.route('/projects/<pid>/kanban/delete', methods=['POST'])
@login_required
def kanban_delete(pid):
    data   = load()
    proj   = next((p for p in data['projects'] if p['id']==pid), None)
    card_id= request.form.get('card_id')
    if proj:
        for col in proj['kanban']:
            proj['kanban'][col] = [c for c in proj['kanban'][col] if c['id']!=card_id]
        save(data)
    return redirect(url_for('project_detail', pid=pid))

# ── Materials ─────────────────────────────────────────────
@app.route('/projects/<pid>/share-material', methods=['POST'])
@login_required
def share_material(pid):
    data  = load()
    user  = get_user(session['user_id'], data)
    title = request.form.get('title','').strip()
    link  = request.form.get('link','').strip()
    mtype = request.form.get('mtype','link')
    desc  = request.form.get('desc','').strip()
    if title:
        mat = {"id":str(uuid.uuid4())[:8],"project_id":pid,
               "uploaded_by":session['user_id'],"title":title,
               "link":link,"mtype":mtype,"desc":desc,
               "created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        data['shared_materials'].append(mat)
        add_xp(user, 'share_material', data)
        save(data)
        flash('Material shared!','success')
    return redirect(url_for('project_detail', pid=pid))

@app.route('/projects/<pid>/request-material', methods=['POST'])
@login_required
def request_material(pid):
    data    = load()
    content = request.form.get('content','').strip()
    if content:
        req = {"id":str(uuid.uuid4())[:8],"project_id":pid,
               "user_id":session['user_id'],"content":content,"status":"open",
               "created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        data['material_requests'].append(req)
        save(data)
        flash('Request posted!','success')
    return redirect(url_for('project_detail', pid=pid))

# ── Polls ─────────────────────────────────────────────────
@app.route('/projects/<pid>/poll/create', methods=['POST'])
@login_required
def create_poll(pid):
    data      = load()
    user      = get_user(session['user_id'], data)
    question  = request.form.get('question','').strip()
    options   = [o.strip() for o in request.form.get('options','').split('\n') if o.strip()]
    if question and len(options) >= 2:
        poll = {"id":str(uuid.uuid4())[:8],"project_id":pid,
                "author_id":session['user_id'],"question":question,
                "options":[{"text":o,"votes":[]} for o in options],
                "created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        data['polls'].append(poll)
        add_xp(user,'create_poll',data)
        save(data)
        flash('Poll created!','success')
    return redirect(url_for('project_detail', pid=pid))

@app.route('/poll/<poll_id>/vote', methods=['POST'])
@login_required
def vote_poll(poll_id):
    data    = load()
    user    = get_user(session['user_id'], data)
    poll    = next((p for p in data['polls'] if p['id']==poll_id), None)
    opt_idx = int(request.form.get('option',0))
    uid     = session['user_id']
    if poll:
        # Remove existing vote
        for opt in poll['options']:
            if uid in opt['votes']: opt['votes'].remove(uid)
        if 0 <= opt_idx < len(poll['options']):
            poll['options'][opt_idx]['votes'].append(uid)
            add_xp(user,'vote_poll',data)
        save(data)
    pid = poll.get('project_id') if poll else None
    if pid: return redirect(url_for('project_detail', pid=pid))
    return redirect(url_for('dashboard'))

# ── Sticky Notes ──────────────────────────────────────────
@app.route('/notes')
@login_required
def notes():
    data = load()
    user = get_user(session['user_id'], data)
    my_notes = [n for n in data['sticky_notes'] if n['user_id']==session['user_id']]
    return render_template('notes.html', user=user,
        notes=[n for n in my_notes if not n.get('pinned')],
        pinned=[n for n in my_notes if n.get('pinned')])

@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    data    = load()
    user    = get_user(session['user_id'], data)
    content = request.form.get('content','').strip()
    color   = request.form.get('color','yellow')
    title   = request.form.get('title','').strip()
    if content:
        note = {"id":str(uuid.uuid4())[:8],"user_id":session['user_id'],
                "title":title,"content":content,"color":color,
                "created_at":datetime.now().strftime('%Y-%m-%d %H:%M'),"pinned":False}
        data['sticky_notes'].append(note)
        add_xp(user,'add_note',data)
        save(data)
        flash('Note added!','success')
    return redirect(url_for('notes'))

@app.route('/notes/<nid>/delete', methods=['POST'])
@login_required
def delete_note(nid):
    data = load()
    data['sticky_notes'] = [n for n in data['sticky_notes']
        if not (n['id']==nid and n['user_id']==session['user_id'])]
    save(data)
    return redirect(url_for('notes'))

@app.route('/notes/<nid>/pin', methods=['POST'])
@login_required
def pin_note(nid):
    data = load()
    for n in data['sticky_notes']:
        if n['id']==nid and n['user_id']==session['user_id']:
            n['pinned'] = not n.get('pinned',False)
    save(data)
    return redirect(url_for('notes'))

# ── Todos ─────────────────────────────────────────────────
@app.route('/todos')
@login_required
def todos():
    data = load()
    user = get_user(session['user_id'], data)
    my_todos = sorted([t for t in data['todos'] if t['user_id']==session['user_id']],
                      key=lambda x: x.get('due_date','9999'))
    my_projects = [p for p in data['projects'] if session['user_id'] in p['members']]
    return render_template('todos.html', user=user, todos=my_todos, my_projects=my_projects,
                           today=date.today().isoformat())

@app.route('/todos/add', methods=['POST'])
@login_required
def add_todo():
    data     = load()
    title    = request.form.get('title','').strip()
    due_date = request.form.get('due_date','').strip()
    priority = request.form.get('priority','medium')
    project  = request.form.get('project','').strip()
    if title:
        todo = {"id":str(uuid.uuid4())[:8],"user_id":session['user_id'],
                "title":title,"due_date":due_date,"priority":priority,
                "project":project,"done":False,
                "created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        data['todos'].append(todo)
        save(data)
    return redirect(url_for('todos'))

@app.route('/todos/<tid>/toggle', methods=['POST'])
@login_required
def toggle_todo(tid):
    data = load()
    user = get_user(session['user_id'], data)
    for t in data['todos']:
        if t['id']==tid and t['user_id']==session['user_id']:
            t['done'] = not t.get('done',False)
            if t['done']: add_xp(user,'complete_task',data)
    save(data)
    return redirect(url_for('todos'))

@app.route('/todos/<tid>/delete', methods=['POST'])
@login_required
def delete_todo(tid):
    data = load()
    data['todos'] = [t for t in data['todos']
        if not (t['id']==tid and t['user_id']==session['user_id'])]
    save(data)
    return redirect(url_for('todos'))

# ── Calendar ──────────────────────────────────────────────
@app.route('/calendar')
@login_required
def calendar():
    data = load()
    user = get_user(session['user_id'], data)
    my_todos = [t for t in data['todos']
                if t['user_id']==session['user_id'] and t.get('due_date')]
    events = [{"title":t['title'],"date":t['due_date'],
               "priority":t['priority'],"done":t.get('done',False)} for t in my_todos]
    return render_template('calendar.html', user=user, events_json=json.dumps(events),
                           today=date.today().isoformat())

# ── Course Rooms ──────────────────────────────────────────
@app.route('/rooms')
@login_required
def rooms():
    data = load()
    user = get_user(session['user_id'], data)
    uid  = session['user_id']
    my_rooms  = [r for r in data['course_rooms'] if uid in r.get('members',[])]
    all_rooms = [r for r in data['course_rooms'] if uid not in r.get('members',[])]
    return render_template('rooms.html', user=user, my_rooms=my_rooms, all_rooms=all_rooms)

@app.route('/rooms/create', methods=['POST'])
@login_required
def create_room():
    data = load()
    user = get_user(session['user_id'], data)
    name = request.form.get('name','').strip()
    code = request.form.get('code','').strip()
    if name:
        room = {"id":str(uuid.uuid4())[:8],"name":name,"code":code,
                "members":[session['user_id']],"posts":[],"resources":[]}
        data['course_rooms'].append(room)
        add_xp(user,'join_room',data)
        save(data)
        flash(f'Room "{name}" created!','success')
    return redirect(url_for('rooms'))

@app.route('/rooms/<rid>/join', methods=['POST'])
@login_required
def join_room(rid):
    data = load()
    user = get_user(session['user_id'], data)
    room = next((r for r in data['course_rooms'] if r['id']==rid), None)
    if room and session['user_id'] not in room['members']:
        room['members'].append(session['user_id'])
        add_xp(user,'join_room',data)
        save(data)
        flash(f'Joined {room["name"]}!','success')
    return redirect(url_for('rooms'))

@app.route('/rooms/<rid>')
@login_required
def room_detail(rid):
    data = load()
    user = get_user(session['user_id'], data)
    room = next((r for r in data['course_rooms'] if r['id']==rid), None)
    if not room:
        flash('Room not found.','danger')
        return redirect(url_for('rooms'))
    members = [get_user(mid,data) for mid in room.get('members',[])]
    posts   = room.get('posts',[])
    for p in posts: p['author'] = get_user(p['author_id'],data)
    return render_template('room_detail.html', user=user, room=room,
                           members=members, posts=posts)

@app.route('/rooms/<rid>/post', methods=['POST'])
@login_required
def room_post(rid):
    data    = load()
    user    = get_user(session['user_id'], data)
    room    = next((r for r in data['course_rooms'] if r['id']==rid), None)
    content = request.form.get('content','').strip()
    if room and content and session['user_id'] in room.get('members',[]):
        post = {"id":str(uuid.uuid4())[:8],"author_id":session['user_id'],
                "content":content,"created_at":datetime.now().strftime('%Y-%m-%d %H:%M')}
        room['posts'].append(post)
        add_xp(user,'post',data)
        save(data)
    return redirect(url_for('room_detail', rid=rid))

# ── Skill Matching ────────────────────────────────────────
@app.route('/match')
@login_required
def skill_match():
    data = load()
    user = get_user(session['user_id'], data)
    uid  = session['user_id']
    my_skills = set(s.lower() for s in user.get('skills',[]))
    matches = []
    for u in data['users']:
        if u['id'] == uid: continue
        their_skills = set(s.lower() for s in u.get('skills',[]))
        common = my_skills & their_skills
        unique = their_skills - my_skills
        score  = len(unique) * 2 + len(common)
        if score > 0:
            matches.append({'user':u,'common':list(common),'unique':list(unique),'score':score})
    matches.sort(key=lambda x: x['score'], reverse=True)
    # Project recommendations based on skills
    rec_projects = []
    for p in data['projects']:
        if uid in p['members']: continue
        tags_lower = [t.lower() for t in p.get('tags',[])]
        overlap = my_skills & set(tags_lower)
        if overlap:
            rec_projects.append({'project':p,'match':list(overlap),
                'owner':get_user(p['owner_id'],data)})
    return render_template('skill_match.html', user=user, matches=matches,
                           rec_projects=rec_projects)

# ── Showcase ──────────────────────────────────────────────
@app.route('/showcase')
@login_required
def showcase():
    data = load()
    user = get_user(session['user_id'], data)
    featured = [p for p in data['projects'] if p.get('showcase')]
    featured_rich = [{'project':p,'owner':get_user(p['owner_id'],data),
        'members':[get_user(mid,data) for mid in p['members']]} for p in featured]
    return render_template('showcase.html', user=user, featured=featured_rich)

# ── Public Profile ────────────────────────────────────────
@app.route('/profile/<uid>')
@login_required
def public_profile(uid):
    data = load()
    me   = get_user(session['user_id'], data)
    target = get_user(uid, data)
    if not target:
        flash('User not found.','danger')
        return redirect(url_for('members'))
    their_projects = [p for p in data['projects'] if uid in p['members']]
    their_posts    = [p for p in data['posts'] if p['author_id']==uid]
    return render_template('public_profile.html', user=me, target=target,
        their_projects=their_projects, their_posts=their_posts,
        BADGES=BADGES, level=level_from_xp(target.get('xp',0)))

# ── Feed ─────────────────────────────────────────────────
@app.route('/feed', methods=['GET','POST'])
@login_required
def feed():
    data = load()
    user = get_user(session['user_id'], data)
    cat  = request.args.get('cat','all')
    if request.method == 'POST':
        content  = request.form.get('content','').strip()
        category = request.form.get('category','general')
        if content:
            post = {"id":str(uuid.uuid4())[:8],"author_id":session['user_id'],
                    "content":content,"created_at":datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    "likes":[],"category":category}
            data['posts'].append(post)
            add_xp(user,'post',data)
            save(data)
        return redirect(url_for('feed'))
    posts = sorted(data['posts'], key=lambda x: x['created_at'], reverse=True)
    if cat != 'all': posts = [p for p in posts if p.get('category')==cat]
    posts_rich = [{**p,'author':get_user(p['author_id'],data)} for p in posts]
    return render_template('feed.html', user=user, posts=posts_rich, cat=cat)

@app.route('/feed/<pid>/like', methods=['POST'])
@login_required
def like_post(pid):
    data = load()
    post = next((p for p in data['posts'] if p['id']==pid), None)
    if post:
        uid = session['user_id']
        if uid in post['likes']: post['likes'].remove(uid)
        else: post['likes'].append(uid)
        save(data)
    return redirect(url_for('feed'))

# ── Members ───────────────────────────────────────────────
@app.route('/members')
@login_required
def members():
    data = load()
    user = get_user(session['user_id'], data)
    return render_template('members.html', user=user, all_users=data['users'], BADGES=BADGES)

# ── Profile ───────────────────────────────────────────────
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    data = load()
    user = get_user(session['user_id'], data)
    if request.method == 'POST':
        user['name']   = request.form.get('name',user['name']).strip()
        user['course'] = request.form.get('course',user['course']).strip()
        user['year']   = int(request.form.get('year',user['year']))
        user['bio']    = request.form.get('bio','').strip()
        user['skills'] = [s.strip() for s in request.form.get('skills','').split(',') if s.strip()]
        user['avatar'] = ''.join(p[0].upper() for p in user['name'].split()[:2])
        save(data)
        flash('Profile updated!','success')
        return redirect(url_for('profile'))
    my_projects = [p for p in data['projects'] if session['user_id'] in p['members']]
    return render_template('profile.html', user=user, my_projects=my_projects,
        BADGES=BADGES, level=level_from_xp(user.get('xp',0)),
        xp_next=xp_for_next(user.get('xp',0)))

# ── Messages ─────────────────────────────────────────────
@app.route('/messages')
@login_required
def messages():
    data = load()
    user = get_user(session['user_id'], data)
    uid  = session['user_id']
    partner_ids = set()
    for dm in data['direct_messages']:
        if dm['from_id']==uid: partner_ids.add(dm['to_id'])
        elif dm['to_id']==uid: partner_ids.add(dm['from_id'])
    conversations = []
    for pid in partner_ids:
        p = get_user(pid,data)
        if not p: continue
        thread = sorted([dm for dm in data['direct_messages']
            if (dm['from_id']==uid and dm['to_id']==pid) or
               (dm['from_id']==pid and dm['to_id']==uid)], key=lambda x: x['created_at'])
        conversations.append({'partner':p,'last':thread[-1] if thread else None,'thread':thread})
    conversations.sort(key=lambda x: x['last']['created_at'] if x['last'] else '', reverse=True)
    return render_template('messages.html', user=user, conversations=conversations,
        all_users=data['users'], active_partner=None, thread=[])

@app.route('/messages/<partner_id>', methods=['GET','POST'])
@login_required
def message_thread(partner_id):
    data    = load()
    user    = get_user(session['user_id'], data)
    partner = get_user(partner_id, data)
    if not partner: return redirect(url_for('messages'))
    uid = session['user_id']
    if request.method == 'POST':
        content = request.form.get('content','').strip()
        if content:
            dm = {"id":str(uuid.uuid4())[:8],"from_id":uid,"to_id":partner_id,
                  "content":content,"created_at":datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            data['direct_messages'].append(dm)
            add_notification(data, partner_id, f"💬 {user['name']}: {content[:50]}", 'message')
            save(data)
        return redirect(url_for('message_thread', partner_id=partner_id))
    thread = sorted([dm for dm in data['direct_messages']
        if (dm['from_id']==uid and dm['to_id']==partner_id) or
           (dm['from_id']==partner_id and dm['to_id']==uid)], key=lambda x: x['created_at'])
    all_pids = set()
    for dm in data['direct_messages']:
        if dm['from_id']==uid: all_pids.add(dm['to_id'])
        elif dm['to_id']==uid: all_pids.add(dm['from_id'])
    conversations = []
    for pid in all_pids:
        p = get_user(pid,data)
        if not p: continue
        t = sorted([dm for dm in data['direct_messages']
            if (dm['from_id']==uid and dm['to_id']==pid) or
               (dm['from_id']==pid and dm['to_id']==uid)], key=lambda x: x['created_at'])
        conversations.append({'partner':p,'last':t[-1] if t else None,'thread':t})
    conversations.sort(key=lambda x: x['last']['created_at'] if x['last'] else '', reverse=True)
    return render_template('messages.html', user=user, conversations=conversations,
        all_users=data['users'], active_partner=partner, thread=thread)

# ── API: unread count ─────────────────────────────────────
@app.context_processor
def inject_unread():
    if 'user_id' in session:
        try:
            data = load()
            uid  = session['user_id']
            unread = len([n for n in data['notifications'] if n['user_id']==uid and not n['read']])
            return {'unread_count': unread}
        except: pass
    return {'unread_count': 0}

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# ── Pomodoro ──────────────────────────────────────────────
@app.route('/pomodoro')
@login_required
def pomodoro():
    data = load()
    user = get_user(session['user_id'], data)
    return render_template('pomodoro.html', user=user)
