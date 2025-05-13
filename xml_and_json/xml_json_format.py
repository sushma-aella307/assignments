import json
import xmltodict
import os

with open("employees.xml") as xml_file:
     
    data_dict = xmltodict.parse(xml_file.read())

    json_data = json.dumps(data_dict)

    with open("data.json", "w") as json_file:
        json_file.write(json_data)
        # json_file.close()
 
