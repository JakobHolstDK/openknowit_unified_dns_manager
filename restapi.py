from flask import Flask, jsonify, request
import requests
import requests

from pymongo import MongoClient
import os

MONGO = os.getenv("MONGO")
DNSTOKEN = os.getenv("DNSTOKEN")

# Get ZONEID
response = requests.get("https://dns.hetzner.com/api/v1/zones", headers={"Auth-API-Token": DNSTOKEN })
zones = response.json()

for zone in zones['zones']:
    if zone['name'] == "openknowit.com": 
        ZONEID = zone['id']

# Get records
response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID}", headers={"Auth-API-Token": DNSTOKEN })
records = response.json()



app = Flask(__name__)
client = MongoClient(MONGO)
db = client['dns_db']
collection = db['dns_entries']

def add_dns_entry(hostname, ip):
    data = {
        "value": ip,
        "ttl": 86400,
        "type": "A",
        "name": hostname,
        "zone_id": ZONEID
    }
    response = requests.post("https://dns.hetzner.com/api/v1/records", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
    if response.status_code == 200:
        return True
    else:
        return False

def change_dns_entry(hostname, ip):
    record = next((rec for rec in records if rec["name"] == hostname), None)
    if record["value"] != ip:
        RECORDID = record["id"]
        data = {
            "value": ip,
            "ttl": 0,
            "type": "A",
            "name": hostname,
            "zone_id": ZONEID
        }
        response = requests.put(f"https://dns.hetzner.com/api/v1/records/{RECORDID}", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
        if response.status_code == 200:
            return True
        else:
            return False
    else:
        return True
    
def delete_dns_entry(hostname):
    record = next((rec for rec in records if rec["name"] == hostname), None)
    RECORDID = record["id"]
    response = requests.delete(f"https://dns.hetzner.com/api/v1/records/{RECORDID}", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN })
    if response.status_code == 200:
        return True
    else:
        return False

@app.route('/dns', methods=['GET'])
def get_dns_entries():
    dns_entries = list(collection.find({}, {'_id': 0}))
    return jsonify(dns_entries)


@app.route('/dns', methods=['POST'])
def add_dns_entry():
    new_entry = request.json
    if add_dns_entry(new_entry['hostname'], new_entry['ip']):
        collection.insert_one(new_entry)
        return jsonify({'message': 'DNS entry added successfully.'})
    else:
        return jsonify({'message': 'DNS entry not added.'}), 404


@app.route('/dns/<hostname>', methods=['GET'])
def get_dns_entry(hostname):
    dns_entry = collection.find_one({'hostname': hostname}, {'_id': 0})
    if dns_entry:
        return jsonify(dns_entry)
    else:
        return jsonify({'message': 'DNS entry not found.'}), 404


@app.route('/dns/<hostname>', methods=['PUT'])
def update_dns_entry(hostname):
    updated_entry = request.json
    result = collection.update_one({'hostname': hostname}, {'$set': updated_entry})
    if result.modified_count > 0:
        return jsonify({'message': 'DNS entry updated successfully.'})
        if update_dns_entry(updated_entry['hostname'], updated_entry['ip']):
            return jsonify({'message': 'DNS entry updated successfully.'})
        else:
            return jsonify({'message': 'DNS entry not updated.'}), 404
    else:
        if add_dns_entry(updated_entry['hostname'], updated_entry['ip']):
            return jsonify({'message': 'DNS entry added successfully.'})
        else:
            return jsonify({'message': 'DNS entry not added.'}), 404



@app.route('/dns/<hostname>', methods=['DELETE'])
def delete_dns_entry(hostname):
    result = collection.delete_one({'hostname': hostname})
    if result.deleted_count > 0:
        return jsonify({'message': 'DNS entry deleted successfully.'})
    else:
        return jsonify({'message': 'DNS entry not found.'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

