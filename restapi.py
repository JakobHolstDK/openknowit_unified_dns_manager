from flask import Flask, jsonify, request
from pymongo import MongoClient
import os

MONGO = os.getenv("MONGO")


app = Flask(__name__)
client = MongoClient(MONGO)
db = client['dns_db']
collection = db['dns_entries']


@app.route('/dns', methods=['GET'])
def get_dns_entries():
    dns_entries = list(collection.find({}, {'_id': 0}))
    return jsonify(dns_entries)


@app.route('/dns', methods=['POST'])
def add_dns_entry():
    new_entry = request.json
    collection.insert_one(new_entry)
    return jsonify({'message': 'DNS entry added successfully.'})


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
    else:
        return jsonify({'message': 'DNS entry not found.'}), 404


@app.route('/dns/<hostname>', methods=['DELETE'])
def delete_dns_entry(hostname):
    result = collection.delete_one({'hostname': hostname})
    if result.deleted_count > 0:
        return jsonify({'message': 'DNS entry deleted successfully.'})
    else:
        return jsonify({'message': 'DNS entry not found.'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

