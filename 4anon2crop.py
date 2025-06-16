#!/usr/bin/env python3

import brainchop  # Ensure installed
import nibabel as nib
import numpy as np
from pathlib import Path
import shutil
import subprocess
import argparse
import sys

is_ct = True
border = 25

def compute_nonzero_bounds(data, is_ct):
    if is_ct:
        mask = data > -999
    else:
        mask = data > 0
    coords = np.argwhere(mask)
    if coords.size == 0:
        return None, mask
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0) + 1
    slices = tuple(slice(start, end) for start, end in zip(mins, maxs))
    return slices, mask

def remove_zero_margins(img_path, out_path="", is_ct=False, save_mask=False, recenter_origin=False):
    img = nib.load(str(img_path))
    data = img.dataobj[:] if is_ct else img.get_fdata()
    original_shape = data.shape
    slices, mask = compute_nonzero_bounds(data, is_ct)
    if save_mask:
        mask_img = nib.Nifti1Image(mask.astype(np.uint8), img.affine, header=img.header)
        mask_path = img_path.parent / f"mask_{img_path.name}"
        nib.save(mask_img, str(mask_path))
        print(f"Saved mask to {mask_path}")
    if slices is None:
        print(f"{img_path.name}: all voxels excluded — skipping.")
        return
    cropped_data = data[slices]
    cropped_shape = cropped_data.shape
    if cropped_shape == original_shape:
        print(f"{img_path.name}: no zero/air borders detected — skipping.")
        return
    crop_offset_voxel = [s.start for s in slices]
    new_affine = img.affine.copy()
    new_affine[:3, 3] = nib.affines.apply_affine(img.affine, crop_offset_voxel)
    if recenter_origin:
        center_voxel = (np.array(cropped_data.shape) - 1) / 2.0
        rotation = new_affine[:3, :3]
        translation = -rotation @ center_voxel
        new_affine[:3, 3] = translation
    cropped_img = nib.Nifti1Image(cropped_data, new_affine, header=img.header)
    cropped_img.set_data_dtype(img.get_data_dtype())
    if not out_path:
        out_path = img_path.parent / f"z{img_path.name}"
    nib.save(cropped_img, str(out_path))

    def shape_str(shape):
        return '×'.join(str(d) for d in shape)

    print(f"Cropped {shape_str(original_shape)} -> {shape_str(cropped_shape)} and saved as {out_path.name} recenter: {recenter_origin}")

def do_brainchop(input_path, out_path, is_ct=False, border=0, model="mindgrab"):
    cmd = ["brainchop", "-m", model, "-i", input_path, "-o", out_path]
    if is_ct:
        cmd.append("--ct")
    if border > 0:
        cmd += ["-b", str(border)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"brainchop failed: {e}")

def main(src_dir: Path, dst_dir: Path):
    if not src_dir.is_dir():
        print(f"ERROR: Input directory does not exist: {src_dir}")
        sys.exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)
    nii_files = sorted([f for f in src_dir.glob("*.nii*") if f.with_suffix(".json").exists()])
    print(f"Cropping {len(nii_files)} files from {src_dir} to {dst_dir}")

    for nii_file in nii_files:
        output_file = dst_dir / nii_file.name
        json_src = nii_file.with_suffix(".json")
        json_dst = output_file.with_suffix(".json")
        if json_dst.exists():
            print(f"Skipping {json_dst.name}, already exists.")
            continue
        do_brainchop(nii_file, output_file, is_ct, border)
        shutil.copy2(json_src, json_dst)
        if not output_file.exists():
            gz_file = output_file.with_suffix(output_file.suffix + ".gz")
            if gz_file.exists():
                output_file = gz_file
            else:
                print(f"WARNING: Output not found for {nii_file.name}")
                continue
        remove_zero_margins(output_file, output_file, is_ct, False, True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run brainchop and crop margins from NIfTI images.")
    parser.add_argument("input_dir", nargs="?", default="./anon", help="Input folder with NIfTI + JSON files")
    parser.add_argument("output_dir", nargs="?", default="./crop", help="Output folder for cropped images")
    args = parser.parse_args()

    main(Path(args.input_dir), Path(args.output_dir))
