
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def get_json(url):
    request = Request(url, headers={"User-Agent": "ASE-entry-test"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            return None
        raise
    except URLError:
        return None


def version_tuple(version):
    return tuple(int(part) for part in version.split(".") if part.isdigit())


def is_compatible(requires_python):
    if not requires_python:
        return True

    current = (3, 11)

    for rule in requires_python.split(","):
        rule = rule.strip()

        if rule.startswith(">="):
            if current < version_tuple(rule[2:].strip()):
                return False
        elif rule.startswith(">"):
            if current <= version_tuple(rule[1:].strip()):
                return False
        elif rule.startswith("<="):
            if current > version_tuple(rule[2:].strip()):
                return False
        elif rule.startswith("<"):
            if current >= version_tuple(rule[1:].strip()):
                return False
        elif rule.startswith("=="):
            if current != version_tuple(rule[2:].strip()):
                return False

    return True


def get_minimum_python(requires_python):
    if not requires_python:
        return None

    minimum = None

    for rule in requires_python.split(","):
        rule = rule.strip()

        if rule.startswith(">="):
            version = rule[2:].strip()
            if minimum is None or version_tuple(version) > version_tuple(minimum):
                minimum = version

    return minimum


def main():
    with open("requirements.txt", "r", encoding="utf-8") as file:
        requirements = [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]

    not_found = 0
    incompatible = 0
    highest_name = None
    highest_version = None

    for requirement in requirements:
        if "==" not in requirement:
            not_found += 1
            continue

        name, version = requirement.split("==", 1)
        name = name.strip()
        version = version.strip()

        package = get_json(f"https://pypi.org/pypi/{name}/json")

        if package is None:
            not_found += 1
            continue

        release = get_json(
            f"https://pypi.org/pypi/{name}/{version}/json"
        )

        if release is None:
            not_found += 1
            continue

        requires_python = release.get("info", {}).get("requires_python") or ""

        if not is_compatible(requires_python):
            incompatible += 1

        minimum = get_minimum_python(requires_python)

        if minimum is not None:
            if (
                highest_version is None
                or version_tuple(minimum) > version_tuple(highest_version)
            ):
                highest_version = minimum
                highest_name = f"{name}=={version}"

    print(f"Dependencies checked: {len(requirements)}")
    print(f"Not found on PyPI: {not_found}")
    print(f"Incompatible with Python 3.11: {incompatible}")

    if highest_name:
        print(f"Highest requirement: {highest_name} (>{highest_version})")
    else:
        print("Highest requirement: None")


if __name__ == "__main__":
    main()
