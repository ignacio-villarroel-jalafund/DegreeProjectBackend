import argparse
import sys

DEFAULT_ENDPOINT = "http://localhost:8000/api/v1/allergies/"

EU_ALLERGENS = [
    {"name": "Sin gluten", "description": "Alergia dedicada a reemplazar ingredientes que contengan gluten, como trigo y harinas."},
    {"name": "Sin crustáceos", "description": "Alergia relacionada con mariscos tipo crustáceos (camarones, langostas, etc.)."},
    {"name": "Sin huevo", "description": "Alergia a productos que contengan huevo o derivados."},
    {"name": "Sin pescado", "description": "Alergia a productos que contengan pescado o derivados."},
    {"name": "Sin cacahuetes", "description": "Alergia a cacahuetes (maní) y productos que los contengan."},
    {"name": "Sin soja", "description": "Alergia a la soja y productos derivados."},
    {"name": "Sin lactosa", "description": "Alergia dedicada a reemplazar ingredientes que contengan lactosa, como leche, queso o yogurts."},
    {"name": "Sin frutos secos", "description": "Alergia a frutos secos de árbol (almendra, nuez, avellana, etc.)."},
    {"name": "Sin apio", "description": "Alergia a apio y productos que lo contengan."},
    {"name": "Sin mostaza", "description": "Alergia a la mostaza y sus derivados."},
    {"name": "Sin sésamo", "description": "Alergia a semillas de sésamo y productos que las contengan."},
    {"name": "Sin sulfitos", "description": "Alergia o sensibilidad a dióxido de azufre y sulfitos (cuando superan ciertos niveles)."},
    {"name": "Sin altramuz", "description": "Alergia a altramuces (lupin) y productos que lo contengan."},
    {"name": "Sin moluscos", "description": "Alergia a moluscos (mejillones, almejas, etc.)."}
]

def normalize(name):
    return "".join(name.lower().strip().split())

def main():
    parser = argparse.ArgumentParser(description="Añadir alergias faltantes al endpoint")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Endpoint para POST/GET de alergias.")
    parser.add_argument("--dry-run", action="store_true", help="No realiza POST; sólo muestra acciones.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout en segundos para peticiones HTTP.")
    args = parser.parse_args()

    try:
        import requests
    except Exception:
        print("ERROR: The 'requests' package is not installed. Install it with: pip install requests", file=sys.stderr)
        sys.exit(1)

    endpoint = args.endpoint.rstrip("/") + "/"
    existing = []

    try:
        response = requests.get(endpoint, timeout=args.timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "results" in data:
            data = data["results"]
        if isinstance(data, list):
            existing = data
    except Exception as e:
        print(f"Error adding allergens", file=sys.stderr)

    existing_norm = {normalize(x.get("name", "")): x for x in existing if "name" in x}
    to_create = [a for a in EU_ALLERGENS if normalize(a["name"]) not in existing_norm]

    if not to_create:
        return

    if args.dry_run:
        return

    headers = {"Content-Type": "application/json"}
    for allergen in to_create:
        payload = {"name": allergen["name"], "description": allergen["description"]}
        try:
            r = requests.post(endpoint, json=payload, headers=headers, timeout=args.timeout)
            if r.status_code not in (200, 201):
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
                print(f"Failed to create {allergen['name']}: status {r.status_code} -> {detail}", file=sys.stderr)
        except Exception as e:
            print(f"Connection error while creating {allergen['name']}: {e}", file=sys.stderr)
