import subprocess
import requests
import json
import os
import datetime
import pprint

pp = pprint.PrettyPrinter(indent=4)




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

# Get ARP table
response = subprocess.run(["arp", "-e"], capture_output=True, text=True)
arp_table = response.stdout

for DOM in subprocess.run(["virsh", "list"], capture_output=True, text=True).stdout.splitlines()[2:]:
    DOM = DOM.split()[1]
    print(f"{DOM}")
    response = subprocess.run(["virsh", "domiflist", DOM], capture_output=True, text=True)
    print(response.stdout)
    for line in response.stdout.split("\n"):
        print(line)

    MAC = next(line.split()[4] for line in response.stdout.splitlines() if "network" in line)
    IP = next(line.split()[0] for line in arp_table.splitlines() if MAC in line)
    record = next((rec for rec in records if rec["name"] == DOM), None)

    if not record:
        print("We need an A record")
        data = {
            "value": IP,
            "ttl": 86400,
            "type": "A",
            "name": DOM,
            "zone_id": ZONEID
        }
        response = requests.post("https://dns.hetzner.com/api/v1/records", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
        if response.status_code == 200:
            print(f"{datetime.now()}: A record created successfully")
        else:
            print(f"{datetime.now()}: Failed to create A record. Status code: {response.status_code}")
    else:
        if record["value"] != IP:
            RECORDID = record["id"]
            print(f"{datetime.now()}: We need to change the IP address on {RECORDID}")
            data = {
                "value": IP,
                "ttl": 0,
                "type": "A",
                "name": DOM,
                "zone_id": ZONEID
            }
            response = requests.put(f"https://dns.hetzner.com/api/v1/records/{RECORDID}", headers={"Content-Type": "application/json", "Auth-API-Token": DNSTOKEN }, json=data)
            if response.status_code == 200:
                print(f"IP address updated successfully for {RECORDID}")
            else:
                print(f"Failed to update IP address. Status code: {response.status_code}")
    
    print(f"{DOM: <20} ; {MAC: <20} ; {IP: <20}")

