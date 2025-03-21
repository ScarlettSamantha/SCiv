import gzip
from argparse import ArgumentParser
from pprint import pprint

import dill

uuid_path = "saves/{uuid}/data.pickle.gz"  # This might be merged with direct_path but they are separate for now as they might be used differently.
direct_path = "saves/{name}/data.pickle.gz"


def save_inspect(path):
    if len(path) == 32 and "/" not in path:
        path = uuid_path.format(uuid=path)
    elif "/" not in path:
        path = direct_path.format(name=path)

    if path.endswith(".gz"):
        with gzip.open(path, "rb") as f:
            pprint(dill.loads(f.read()))
    else:
        with open(path, "rb") as f:
            pprint(dill.loads(f.read()))


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("path", type=str)
    args = arg_parser.parse_args()

    if not args.path:
        print("No path provided.")
        exit(1)

    save_inspect(args.path)
