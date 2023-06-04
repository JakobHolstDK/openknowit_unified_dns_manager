from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import requests


app = Flask(__name__)

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
collection = db['records']

def get_zoneid(domain):
  response = requests.get("https://dns.hetzner.com/api/v1/zones", headers={"Auth-API-Token": DNSTOKEN })
  zones = response.json()
  for zone in zones['zones']:
    if zone['name'] == domain:   
        ZONEID = zone['id']
        return ZONEID
    

def get_records(domain):
  ZONEID = get_zoneid(domain)
  response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID}", headers={"Auth-API-Token": DNSTOKEN })
  records = response.json()
  return records

def get_record(domain, hostname, ip):
  ZONEID = get_zoneid(domain)
  response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID},ip={ip} ", headers={"Auth-API-Token": DNSTOKEN })
  records = response.json()
  return records

def get_record(domain, hostname):
  records = get_records(domain)
  record = next((rec for rec in records if rec["name"] == hostname), None)
  return record

# API endpoint to update DNS records
@app.route('/dns', methods=['POST'])
def update_dns():
    
    zoneid = get_zoneid(DOMAIN)
    records = get_records(DOMAIN)
    for record in records['zones ']:
      print(record)

    try:
      dns_record = request.json
      domain = dns_record.get('name')
      ip = dns_record.get('ip')
      collection.update_one({'domain': domain}, {'$set': {'ip': ip}}, upsert=True)
      return jsonify({'message': 'DNS record updated successfully.'}), 200
    except Exception as e:
       print(str(e))
       return jsonify({'message': 'Failed to update DNS record.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

