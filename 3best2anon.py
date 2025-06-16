#!/usr/bin/env python3

import random
from pathlib import Path
import shutil
import csv
import json
import argparse
import sys

def main(src_dir: Path, dst_dir: Path):
    if not src_dir.exists():
        print(f"ERROR: Input directory does not exist: {src_dir}")
        sys.exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)
    lookup_file = dst_dir / "lookup.tsv"
    modality = "ct"

    nii_files = sorted([f for f in src_dir.glob("*.nii*") if f.with_suffix(".json").exists()])

    random.seed(42)
    random.shuffle(nii_files)
    pad_width = len(str(len(nii_files)))

    with open(lookup_file, "w", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter="\t")
        writer.writerow(["original_name", "anonymized_name"])

        for i, nii in enumerate(nii_files, start=1):
            anon_id = f"{i:0{pad_width}}_{modality}"
            new_nii = dst_dir / f"{anon_id}{nii.suffix}"
            new_json = dst_dir / f"{anon_id}.json"
            old_json = nii.with_suffix(".json")

            shutil.copy2(nii, new_nii)
            shutil.copy2(old_json, new_json)

            try:
                with open(new_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "AcquisitionTime" in data:
                    del data["AcquisitionTime"]
                    with open(new_json, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not sanitize {new_json}: {e}")

            writer.writerow([nii.stem, anon_id])

    print(f"Copied {len(nii_files)} image pairs to {dst_dir}")
    print(f"Audit log saved to {lookup_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymize filenames and clean metadata.")
    parser.add_argument("input_dir", nargs="?", default="./best", help="Input folder with NIfTI + JSON pairs")
    parser.add_argument("output_dir", nargs="?", default="./anon", help="Output folder for anonymized files")
    args = parser.parse_args()

    main(Path(args.input_dir), Path(args.output_dir))
