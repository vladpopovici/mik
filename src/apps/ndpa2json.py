#
# NDPA2JSON: converts annotation from Hamamatsu's NDPA format to GeoJSON.
#
import sys
from mik.ndpa import load_NDPA
from mik.wsi import WSI
from mik import NpJSONEncoder

import configargparse as opt
from datetime import datetime
import hashlib
import geojson as gj

_time = datetime.now()
__author__ = "Vlad Popovici <popovici@bioxlab.org>"
__version__ = "0.1"
__description__ = {
    'name': 'st_match_tissue_parts',
    'unique_id' : hashlib.md5(str.encode("ndpa2json" + __version__)).hexdigest(),
    'version': __version__,
    'timestamp': _time.isoformat(),
    'input': ['None'],
    'output': ['None'],
    'params': dict()
}

def main() -> int:
    p = opt.ArgumentParser(description="Converts annotation from Hamamatsu's NDPA format to GeoJSON.")
    p.add_argument("--wsi", action="store", help="name of the whole slide image file (.NDPI)",
                   required=True)
    p.add_argument("--ndpa", action="store", help="name of the annotation file (.NDPA)",
                   required=True)
    p.add_argument("--out", action="store", help="GeoJSON file for storing the results",
                   required=True)
    p.add_argument("--reference_corner", action="store_true",
                   help="use upper-left corner as origin for the coordinate system. Default: no (use image center)")
    

    args = p.parse_args()

    __description__['params'] = vars(args)
    __description__['input'] = [str(args.wsi)]
    __description__['output'] = [str(args.out)]

    ann = load_NDPA(WSI(args.wsi), args.ndpa, 
                    reference="corner" if args.reference_corner else "center",
                    force_closed_contours=True)
    ann_list = list()
    for a in ann._annots['base']:  # NDPA does not have more layers
        b = a.asGeoJSON()
        b["properties"]["mpp"] = ann._mpp
        b["properties"]["image_shape"] = ann._image_shape
        ann_list.append(b)

    with open(args.out, 'w') as out:
        gj.dump(ann_list, out, cls=NpJSONEncoder, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())
