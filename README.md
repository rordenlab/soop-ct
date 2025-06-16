## About

This repository provides tools for converting CT scans from DICOM format to NIfTI using BIDS organization. The goal is to support scientific and medical discovery by enabling standardized analysis pipelines. While the DICOM format is the clinical standard for medical imaging, it is complex and not broadly supported by most neuroimaging tools. In contrast, the NIfTI format is simpler, and the Brain Imaging Data Structure (BIDS) allows automated and reproducible analysis.

## Caveats

This script uses emerging methods, so users should be aware of a few caveats:

 - The BIDS Computed Tomography specification has not yet been finalized. This repository will adapt as [BEP 024](https://bids.neuroimaging.io/extensions/beps/bep_024.html) evolves. The [BIDS validator](https://bids-website.readthedocs.io/en/latest/tools/validator.html) may currently report errors.
 - These scripts require Python 3.10 or later (due to the BrainChop dependency).
 - As of writing, ANTsPyX requires [numpy <= 2.0.1](https://github.com/ANTsX/ANTsPy/pull/816), which may not be supported by some newer Python releases. Developers suggest more recent versions may still work.
 - The `bids2norm` script depends on FreeSurfer's SynthSR module. This requires installing the full FreeSurfer software stack and license. Alternatively, SynthSR can be installed separately, but has [complex dependencies](https://github.com/BBillot/SynthSR).

## Installation

Install the scripts and example data by running the following:

```
git clone https://github.com/rordenlab/soop-ct.git
cd soop-ct
pip install -r requirements.txt
unzip DICOM.zip
```

If you wish to use `bids2norm`, you must also install [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) and its license file.

## Usage

The repository includes a sample DICOM dataset for testing. The following commands process this example dataset:

```
python 1dcm2raw.py ./DICOM ./raw
python 2raw2best.py ./raw ./best
# Check generated JPGs to ensure correct image selection
python 3best2anon.py ./best ./anon
python 4anon2crop.py ./anon ./crop 
python 5crop2bids.py ./crop ./bids
# Optional group-level analysis
python 6bids2norm.py ./bids
python nii2mean.py ./bids/derivatives/syncro _ct.nii.gz
```

It is advisable to inspect the results after each stage. This modular pipeline allows users to intervene or adjust steps based on the complexities of real-world clinical data.

### Processing Stages

1. **`1dcm2raw.py [input_dir] [output_dir]`**
   Converts all DICOM images to NIfTI format. Files are stored in folders named by accession number. Series are named using the series number and protocol name. Interpolation corrects for variable slice thickness and gantry tilt.

2. **`2raw2best.py [input_dir] [output_dir]`** 
   Selects the best series from each study based on slice thickness, field of view, and soft-tissue convolution kernel. Creates corresponding JPEGs for quality control.
   - Uses helper script `dir2jpg.py` to generate previews.

3. **`3best2anon.py [input_dir] [output_dir]`**  
   Renames files using anonymized IDs. Generates a `lookup.tsv` file to map accession numbers to anonymized IDs. This file should be kept secure.

4. **`4anon2crop.py [input_dir] [output_dir]`**  
   Crops and brain-extracts each image to remove facial features and de-identify data. By default, the mask is dilated 25mm beyond the brain boundary.

5. **`5crop2bids.py [input_dir] [output_dir`]**  
   Converts cropped images to BIDS format. Also generates placeholder boilerplate files:
   - `dataset_description.json`
   - `participants.tsv`
   - `participants.json`

6. **`6bids2norm.py [bids_dir]`**  
   Normalizes each image to a common space (MNI152). Saves outputs in the `derivatives/syncro` directory.
   - Calls `SYNcro.py` to register each image using ANTs.
   - Uses FreeSurfer's SynthSR to synthesize a T1-weighted image from CT.

7. **`nii2mean.py [input_dir] [filter]`**  
   Creates a group-average image from all files in the input folder matching the specified filter.

Below is an example of the average of normalized CT images (albeit the full initial SOOP-CT dataset, not the small demo).

![Averaging of nii2mean with MRIcroGL H 0.4 A -8 8 24 40 C -24 0 S X R 0](mean.jpg)

## Links

 - DICOM.zip images: [Acute Ischemic Infarct Segmentation](https://github.com/GriffinLiang/AISD)
 - DICOM-to-NIfTI conversion: [dcm2niix](https://github.com/rordenlab/dcm2niix)
 - Core Python dependencies: [numpy](https://github.com/numpy/numpy), [nibabel](https://github.com/nipy/nibabel)
 - Spatial normalization: [ANTS](https://pubmed.ncbi.nlm.nih.gov/17659998/)
 - Brain extraction: [BrainChop](https://github.com/neuroneural/brainchop-cli)
 - T1 synthesis: [SynthSR](https://surfer.nmr.mgh.harvard.edu/fswiki/SynthSR)

## Citation

 - Absher, J., ... Rorden, C. (in prep). *SOOP-CT: Acute Stroke CT with Open Tools for De-Identification and Sharing*
