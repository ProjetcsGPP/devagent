import os
import json
import yaml

INPUT_FILE = "swagger_backend.yaml"
OUTPUT_DIR = "rag/swagger_clean"

# =========================
# CARREGAR SWAGGER
# =========================

def load_swagger(path):
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f)

# =========================
# RESOLVER $ref
# =========================

def resolve_ref(ref, swagger):
    parts = ref.replace("#/", "").split("/")
    data = swagger
    for part in parts:
        data = data.get(part, {})
    return data

def deep_resolve(obj, swagger):
    if isinstance(obj, dict):
        if "$ref" in obj:
            return deep_resolve(resolve_ref(obj["$ref"], swagger), swagger)

        return {k: deep_resolve(v, swagger) for k, v in obj.items()}

    if isinstance(obj, list):
        return [deep_resolve(i, swagger) for i in obj]

    return obj

# =========================
# SCHEMA EXTRACTION
# =========================

def extract_schema(schema):
    if not schema:
        return {}

    if schema.get("type") == "object":
        props = schema.get("properties", {})
        required = set(schema.get("required", []))

        result = {}

        for name, prop in props.items():
            result[name] = {
                "type": prop.get("type", "object"),
                "required": name in required,
                "description": prop.get("description"),
                "example": prop.get("example"),
                "enum": prop.get("enum"),
                "format": prop.get("format"),
                "default": prop.get("default")
            }

        return result

    if schema.get("type") == "array":
        return {
            "type": "array",
            "items": extract_schema(schema.get("items"))
        }

    return schema

# =========================
# AUTH DETECTION
# =========================

def is_auth_required(path, details, swagger):
    if details.get("security"):
        return True

    if swagger.get("security"):
        return True

    keywords = ["login", "logout", "auth", "token", "session"]
    if any(k in path.lower() for k in keywords):
        return True

    return False

# =========================
# CHUNK BUILDER (RAG INTELIGENTE)
# =========================

def build_chunks(doc):

    intent = f"""
TYPE: INTENT

SUMMARY:
{doc.get('summary')}

DESCRIPTION:
{doc.get('description')}

TAGS:
{doc['metadata']['category']}
"""

    execution = f"""
TYPE: EXECUTION

METHOD: {doc['method']}
PATH: {doc['path']}
TOOL: {doc['tool']['name']}
AUTH_REQUIRED: {doc['metadata']['is_auth']}
"""

    params = f"""
TYPE: PARAMETERS

PARAMETERS:
{json.dumps(doc.get('parameters', []), ensure_ascii=False)}

REQUEST_SCHEMA:
{json.dumps(doc.get('request', {}), ensure_ascii=False)}
"""

    return [
        ("intent", intent.strip()),
        ("execution", execution.strip()),
        ("params", params.strip())
    ]

# =========================
# PROCESSAR ENDPOINTS
# =========================

def process_paths(swagger):
    paths = swagger.get("paths", {})
    chunks_output = []

    for path, methods in paths.items():
        for method, details in methods.items():

            details = deep_resolve(details, swagger)

            endpoint = {
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "description": details.get("description", ""),
                "request": {},
                "responses": {},
                "parameters": [],
                "metadata": {},
                "tool": {}
            }

            # REQUEST BODY
            request_body = details.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                app_json = content.get("application/json", {})
                schema = app_json.get("schema", {})
                endpoint["request"] = extract_schema(schema)

            # PARAMETERS
            params = details.get("parameters", [])
            if params:
                endpoint["parameters"] = [
                    {
                        "name": p.get("name"),
                        "in": p.get("in"),
                        "required": p.get("required", False),
                        "type": p.get("schema", {}).get("type", "string"),
                        "description": p.get("description")
                    }
                    for p in params
                ]

            # RESPONSES
            responses = details.get("responses", {})
            for status, resp in responses.items():
                content = resp.get("content", {})
                app_json = content.get("application/json", {})
                schema = app_json.get("schema", {})
                endpoint["responses"][status] = extract_schema(schema)

            # METADATA
            endpoint["metadata"] = {
                "is_auth": is_auth_required(path, details, swagger),
                "category": details.get("tags", []),
                "operation": method.upper(),
                "complexity": (
                    len(endpoint["parameters"]) * 2 +
                    (1 if endpoint["request"] else 0) +
                    (2 if any(k in path.lower() for k in ["login", "auth", "token", "session"]) else 0)
                ),
                "has_body": bool(endpoint["request"]),
                "has_params": len(endpoint["parameters"]) > 0
            }

            # TOOL
            endpoint["tool"] = {
                "name": details.get("operationId"),
                "method": method.upper(),
                "path": path,
                "summary": endpoint["summary"],
                "description": endpoint["description"],
                "parameters": endpoint["parameters"],
                "request_body": {
                    k: v["type"] if isinstance(v, dict) and "type" in v else "object"
                    for k, v in endpoint["request"].items()
                } if endpoint["request"] else {},
                "responses": list(endpoint["responses"].keys()),
                "auth_required": endpoint["metadata"]["is_auth"],
                "complexity": endpoint["metadata"]["complexity"]
            }

            # =========================
            # 🔥 AQUI ENTRA O RAG DE VERDADE
            # =========================
            chunks = build_chunks(endpoint)

            for chunk_type, chunk_text in chunks:
                chunks_output.append({
                    "id": f"{endpoint['method']}_{path}_{chunk_type}",
                    "type": chunk_type,
                    "text": chunk_text,
                    "tool": endpoint["tool"]
                })

    return chunks_output

# =========================
# SALVAR RAG CHUNKS
# =========================

def save_docs(chunks):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for c in chunks:
        safe_name = c["id"].replace("/", "_").replace(" ", "_")
        filepath = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(c["text"])

    print(f"\n✅ {len(chunks)} chunks gerados em {OUTPUT_DIR}\n")

# =========================
# MAIN
# =========================

def main():
    swagger = load_swagger(INPUT_FILE)
    chunks = process_paths(swagger)
    save_docs(chunks)

if __name__ == "__main__":
    main()