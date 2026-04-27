import yaml
import json

# arquivo de entrada (YMAL)
with open("../frontend/swagger.yaml", "r") as f:
   data = yaml.safe_load(f)

# arquivo de saída
with open("../frontend/swagger.json", "w") as f:
   json.dump(data, f, indent=2)

print("Conversão concluída: swagger.json criado!")

