from pathlib import Path

import requests

base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
data_dir_out = Path("data/toronto/input/mapping/")
data_dir_out.mkdir(parents=True, exist_ok=True)

datasets = [
    {"id": "property-boundaries", "file_name": "property_boundaries"},
    {"id": "toronto-centreline-tcl", "file_name": "centreline"},
    {
        "id": "address-points-municipal-toronto-one-address-repository",
        "file_name": "address_points",
    },
]

url = base_url + "/api/3/action/package_show"

for dataset in datasets:
    package = requests.get(url, params={"id": dataset["id"]}).json()

    for resource in package["result"]["resources"]:
        # skip anything that isn't a downloadable geo file (docs, readmes, etc.)
        if resource["format"].lower() not in {"gpkg"}:
            continue

        print(resource["name"], resource["last_modified"])

        file_resp = requests.get(resource["url"])
        file_resp.raise_for_status()

        out_path = (
            data_dir_out
            / f"{dataset['file_name']}_{resource['format'].lower()}.{resource['format'].lower()}"
        )
        out_path.write_bytes(file_resp.content)
