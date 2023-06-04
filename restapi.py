from flask import Flask, jsonify, request
import requests
import datetime


from pymongo import MongoClient
import os



MONGO = os.getenv("MONGO")
DNSTOKEN = os.getenv("DNSTOKEN")
DOMAIN = os.getenv("DOMAIN")


# Get ZONEID
def get_zoneid(domain):
  response = requests.get("https://dns.hetzner.com/api/v1/zones", headers={"Auth-API-Token": DNSTOKEN })
  zones = response.json()
  for zone in zones['zones']:
    if zone['name'] == domain: 
      return zone['id']
    
def get_records(domain):
  ZONEID = get_zoneid(domain)
  response = requests.get(f"https://dns.hetzner.com/api/v1/records?zone_id={ZONEID}", headers={"Auth-API-Token": DNSTOKEN })
  records = response.json()
  return records

# Get records
zoneid = get_zoneid(DOMAIN)
records = get_records(DOMAIN)




app = Flask(__name__)
client = MongoClient(MONGO)
db = client['dns_db']
collection = db['dns_entries']

def get_domain_id(domain):
  response = requests.get("https://dns.hetzner.com/api/v1/zones", headers={"Auth-API-Token": DNSTOKEN })
  zones = response.json()
  for zone in zones['zones']:
    if zone['name'] == domain: 
      return zone['id']
    
def create_the_dns_entry(hostname, zoneid, ip):
  print("We need an A record")
  data = {
     "value": ip,
     "ttl": 86400,
     "type": "A",
     "name": hostname,
     "zone_id": ZONEID
    }
  response = requests.post("https://dns.hetzner.com/api/v1/records", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
  if response.status_code == 200:
    print(f"{datetime.now()}: A record created successfully")
  else:
    print(f"{datetime.now()}: Failed to create A record. Status code: {response.status_code}")

def get_the_dns_entry(hostname):
    records = get_records(DOMAIN)
    for entry in records['records']:
        if entry['name'] == hostname:
            return entry
    return None



def update_the_dns_entry(hostname, ip):   
  record_id = get_the_dns_entry(hostname)['id']
  record_ip = get_the_dns_entry(hostname)['value']
  if record_ip != ip:
      data = {
       "value": ip,
       "ttl": 0,
       "type": "A",
       "name": hostname,
       "zone_id": zoneid
     }
      response = requests.put(f"https://dns.hetzner.com/api/v1/records/{record_id}", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
      if response.status_code == 200:
        print(f"IP address updated successfully for {record_id}")
        return True
      else:
        print(f"Failed to update IP address. Status code: {response.status_code}")
        return False
      


def add_the_dns_entry(hostname, ip):
    if not get_the_dns_entry(hostname):
        print("We need an A record")
        data = {
          "value": ip,
          "ttl": 86400,
          "type": "A",
          "name": hostname,
          "zone_id": zoneid
        }
        response = requests.post("https://dns.hetzner.com/api/v1/records", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
        if response.status_code == 200:
          return True
        else:
          return False
    else:
       update_dns_entry(hostname, ip)

def change_the_dns_entry(hostname, ip):
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
    
def delete_the_dns_entry(hostname):
    record = next((rec for rec in records if rec["name"] == hostname), None)
    RECORDID = record["id"]
    response = requests.delete(f"https://dns.hetzner.com/api/v1/records/{RECORDID}", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN })
    if response.status_code == 200:
        return True
    else:
        return False


record = get_the_dns_entry("test")
add_the_dns_entry("test", "127.0.0.1")
record = get_the_dns_entry("test")
print(record)




@app.route('/dns', methods=['GET'])
def get_dns_entries():
    dns_entries = list(collection.find({}, {'_id': 0}))
    return jsonify(dns_entries)


@app.route('/dns', methods=['POST'])
def add_dns_entry():
    new_entry = request.json
    print(new_entry)
    if add_the_dns_entry(new_entry['hostname'], new_entry['ip_address']):
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
        if update_the_dns_entry(updated_entry['hostname'], updated_entry['ip']):
            return jsonify({'message': 'DNS entry updated successfully.'})
        else:
            return jsonify({'message': 'DNS entry not updated.'}), 404
    else:
        if add_the_dns_entry(updated_entry['hostname'], updated_entry['ip_address']):
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

