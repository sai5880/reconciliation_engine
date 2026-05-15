import requests

url = "http://localhost:8000/reconcile"

files = {
    "bank_file": open("bank.csv", "rb"),
    "gl_file": open("gl.csv", "rb"),
}

data = {
    "enable_exact": True,
    "enable_fuzzy": True,
    "enable_complex": True,

    "amount_tolerance": 100,
    "date_tolerance_days": 10,
    "vendor_threshold": 80,

    "use_reference_match": False,
}

response = requests.post(
    url,
    files=files,
    data=data,
)

print(response.json())