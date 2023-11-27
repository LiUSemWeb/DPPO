from pyshacl import validate
import os
import yaml

with open("config.yml") as f:
    config = yaml.safe_load(f)

for shape, value in config["shapes"].items():
    print(f"Validate: {shape}")
    shapes_file = os.path.abspath(value["shape"])
    for f in value["valid"]:
        conforms, v_graph, v_text = validate(f, shacl_graph=shapes_file)
        if conforms:
            print(f"Passed: {f}")
        else:
            print(f"Failed: {f} should validate to true")
            print(v_text)
    
    for f in value["invalid"]:
        conforms, v_graph, v_text = validate(f, shacl_graph=shapes_file)
        if conforms:
            print(f"Failed: {f} should validate to false")
        else:
            print(f"Passed: {f}")
    print()
