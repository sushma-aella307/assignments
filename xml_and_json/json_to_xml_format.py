import json
import xmltodict
import os

# Load JSON data from file
with open("data.json", "r") as json_file:
    json_data = json.load(json_file)

# Convert JSON (dict) to XML string
xml_data = xmltodict.unparse(json_data, pretty=True)

# Save XML string to file
with open("output.xml", "w") as xml_file:
    xml_file.write(xml_data)

print("✅ JSON successfully converted to XML!")
