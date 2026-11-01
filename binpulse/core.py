"""Offline-first waste bin telemetry and collection planning."""
import math
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BINS = [
    ('BIN-101','Model Town',31.4847,74.3239),
    ('BIN-102','Johar Town',31.4697,74.2728),
    ('BIN-103','Gulberg',31.5160,74.3455),
    ('BIN-104','DHA Phase 5',31.4575,74.4091),
    ('BIN-105','Wapda Town',31.4316,74.2635),
]

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS bins (id TEXT PRIMARY KEY, area TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, capacity_cm REAL NOT NULL DEFAULT 100);
    CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY AUTOINCREMENT, bin_id TEXT NOT NULL REFERENCES bins(id), fill_pct INTEGER NOT NULL CHECK(fill_pct BETWEEN 0 AND 100), battery_pct INTEGER NOT NULL CHECK(battery_pct BETWEEN 0 AND 100), created_at TEXT NOT NULL, synced INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX IF NOT EXISTS readings_bin_idx ON readings(bin_id, id DESC);
    ''')
    db.executemany('INSERT OR IGNORE INTO bins(id,area,latitude,longitude) VALUES(?,?,?,?)',DEFAULT_BINS)
    db.commit()

def fill_from_distance(distance_cm, capacity_cm=100):
    if not isinstance(distance_cm,(int,float)) or not math.isfinite(distance_cm) or not 0 <= distance_cm <= capacity_cm:
        raise ValueError('distance must be finite and within sensor depth')
    return round((1 - distance_cm / capacity_cm) * 100)

def status(fill):
    return 'critical' if fill >= 90 else 'collect' if fill >= 75 else 'normal'

def record(db,bin_id,fill_pct,battery_pct=100):
    if type(fill_pct) is not int or not 0 <= fill_pct <= 100 or type(battery_pct) is not int or not 0 <= battery_pct <= 100:
        raise ValueError('fill_pct and battery_pct must be integers between 0 and 100')
    if not db.execute('SELECT 1 FROM bins WHERE id=?',(bin_id,)).fetchone():
        raise ValueError('Unknown bin')
    time = datetime.now(timezone.utc).isoformat()
    with db:
        cur=db.execute('INSERT INTO readings(bin_id, fill_pct, battery_pct, created_at) VALUES (?,?,?,?)',(bin_id,fill_pct,battery_pct,time))
    return cur.lastrowid

def snapshot(db):
    rows=db.execute('''SELECT b.id,b.area,b.latitude,b.longitude,b.capacity_cm,r.fill_pct,r.battery_pct,r.created_at,r.synced FROM bins b LEFT JOIN readings r ON r.id=(SELECT MAX(id) FROM readings WHERE bin_id=b.id) ORDER BY b.id''').fetchall()
    return [dict(row, status=status(row['fill_pct']) if row['fill_pct'] is not None else 'unknown') for row in rows]

def pending(db):
    return [dict(r) for r in db.execute('SELECT * FROM readings WHERE synced=0 ORDER BY id')]

def mark_synced(db,ids):
    ids=list(ids)
    if not ids: return 0
    if any(type(i) is not int or i <= 0 for i in ids): raise ValueError('invalid IDs')
    with db:
        cur=db.executemany('UPDATE readings SET synced=1 WHERE id=?',[(i,) for i in ids])
    return len(ids)

def simulate(db,seed=None):
    rng=random.Random(seed)
    output=[]
    for b in snapshot(db):
        prev=b['fill_pct'] if b['fill_pct'] is not None else rng.randint(10,80)
        fill=min(100,max(0,prev + rng.randint(3,20)))
        battery=max(0,(b['battery_pct'] if b['battery_pct'] is not None else 100)-rng.randint(0,2))
        record(db,b['id'],fill,battery)
        output.append({'bin_id':b['id'],'fill_pct':fill,'status':status(fill)})
    return output
