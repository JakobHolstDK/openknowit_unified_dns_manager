# backend for the application

import sqlite3
import redis
import json
import os
import requests
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta



DNSTOKEN = os.getenv("DNSTOKEN")
DOMAIN = os.getenv("DOMAIN")

mongo_port = 27017
mongo_database = 'dns_records'
mongo_host = os.getenv("MONGO")
mongo_port = 27017
mongo_database = 'dns_records'

# MongoDB client
client = MongoClient(mongo_host, mongo_port)
db = client[mongo_database]
collection = db['dns_records']

def get_zoneid(domain):
    response = requests.get("https://dns.hetzner.com/api/v1/zones", headers={"Auth-API-Token": DNSTOKEN })
    zones = response.json()
    for zone in zones['zones']:
        if zone['name'] == domain:   
            ZONEID = zone['id']
            return ZONEID
        

def get_record(domain, hostname, ip):
    ZONEID = get_zoneid(domain)
    response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID},ip={ip} ", headers={"Auth-API-Token": DNSTOKEN })
    records = response.json()
    return records

def get_records(domain):
    ZONEID = get_zoneid(domain)
    response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID}", headers={"Auth-API-Token": DNSTOKEN })
    records = response.json()
    return records

if __name__ == '__main__':
    records = get_records(DOMAIN)
    print(records)
    exit(0)




