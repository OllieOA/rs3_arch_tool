from pathlib import Path
import requests
import time

from tqdm import tqdm


ARTEFACT_PATH = Path("artefact_images")
ARTEFACT_PATH.mkdir(exist_ok=True)

HTTPS_ESCAPES = {
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "/": "%47",
    "-": "%45",
    " ": "_",
}

URL_FORMAT = "https://runescape.wiki/images/{}.png"
ARTEFACT_LIST_FILE = Path(__file__).parent / "artefact_list.csv"

EXCLUSIONS = [
    "spear_of_annihilation_damaged",
    "tetracompass_unpowered_damaged",
]

DRYRUN = False


def convert_name_to_filename(name: str) -> str:
    name = (
        name.replace(" ", "_").replace("(", "").replace(")", "").replace("'", "").replace("/", "_")
        + ".png"
    )
    return name.lower()


def convert_name_to_url(name: str) -> str:
    for k, v in HTTPS_ESCAPES.items():
        name = name.replace(k, v)
    return name


def download_image(url: str, local_path: Path) -> None:
    try:
        r = requests.get(url, allow_redirects=True)
        with open(local_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Failed to download from `{url}`: {e}")

    time.sleep(0.5)


def download_images() -> None:
    print("Downloading artefacts...")
    with open(ARTEFACT_LIST_FILE, "rt") as f:
        all_artefacts = [x.strip() for x in f.readlines()]

    for artefact in tqdm(all_artefacts):
        normal_artefact_path = convert_name_to_filename(artefact)
        damaged_artefact_path = normal_artefact_path.replace(".png", f"_damaged.png")

        normal_artefact_url = URL_FORMAT.format(convert_name_to_url(artefact))
        damaged_artefact_url = URL_FORMAT.format(convert_name_to_url(artefact + " (damaged)"))

        for artefact_path, artefact_url in zip(
            [normal_artefact_path, damaged_artefact_path],
            [normal_artefact_url, damaged_artefact_url],
        ):
            local_filename = artefact_path

            if Path(local_filename).stem in EXCLUSIONS:
                continue

            local_path = ARTEFACT_PATH / local_filename

            if local_path.exists():
                continue

            if DRYRUN:
                print(f"Would download {artefact_url} to {local_path}.")
                continue
            download_image(artefact_url, local_path)
