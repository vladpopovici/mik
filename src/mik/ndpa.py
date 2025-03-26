#
# NDPA: Hamamatsu's annotations are stored in XML format.
#

from typing import Union
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
import os
import argparse as opt
import xml.etree.ElementTree as ET
from .wsi import WSI
from wsitk_annot import Annotation, Polygon

def load_NDPA(ndpi: WSI, ndpa: Union[str, Path], 
              reference: str = 'center',
              force_closed_contours: bool=False) -> Annotation:
    """
    Read annotation from NDPA file and convert it to level-0 image pixel coordinates.

    Args:
        ndpi: a whole slide image (WSI) object
        ndpa: path to NDPA file
        reference: ('center' or 'corner') whether the coordinates are to be kept 
            relative to the 'center' of the image (default for Hamamatsu coordinates) 
            or should be translated to be relative to the upper-left corner of the image
        force_closed_contours: close the polylines

    Returns:
        an Annotation object
    """
    ndpa = Path(ndpa)
    xml_file = ET.parse(ndpa)
    xml_root = xml_file.getroot()

    try:
        x_off = int(ndpi._original_meta['hamamatsu.XOffsetFromSlideCentre'])
        y_off = int(ndpi._original_meta['hamamatsu.YOffsetFromSlideCentre'])
    except KeyError:
        raise RuntimeError('probably not a Hamamatsu NDPA file')

    reference = reference.lower()
    if reference not in ['center', 'corner']:
        raise RuntimeError('Unknown reference point')
    
    x_mpp = float(ndpi.info['mpp_x'])
    y_mpp = float(ndpi.info['mpp_y'])
    dimX0, dimY0 = ndpi.extent(0)
    half_dimX0, half_dimY0 = int(dimX0 / 2), int(dimY0 / 2)

    x_zero = int(np.floor(x_off / 1000.0 / x_mpp - half_dimX0))
    y_zero = int(np.floor(y_off / 1000.0 / y_mpp - half_dimY0))

    wsi_annot = Annotation(
        name=ndpa.name,
        image_shape={'width': int(dimX0), 'height': int(dimY0)},
        mpp = 0.5 * (x_mpp + y_mpp)
    )
    for ann in list(xml_root):
        name = ann.find('title').text
        p = ann.find('annotation')
        if p is None:
            continue
        if p.find('closed').text != "1":
            continue                   # not a closed contour
        p = p.find('pointlist')
        if p is None:
            continue

        xy_coords = []
        for pts in list(p):
            # coords in NDPI system, relative to the center of the slide
            x = int(pts.find('x').text)
            y = int(pts.find('y').text)

            # convert the coordinates:
            x -= x_off                 # relative to the center of the image
            y -= y_off

            x /= 1000.0 * x_mpp        # in pixels, relative to the center
            y /= 1000.0 * y_mpp

            x = int(np.floor(x + half_dimX0)) # in pixels, relative to UL corner
            y = int(np.floor(y + half_dimY0))

            xy_coords.append([x, y])

        if len(xy_coords) < 5:
            # too short
            continue

        # check the last point to match the first one
        if (xy_coords[0][0] != xy_coords[-1][0]) or (xy_coords[0][1] != xy_coords[-1][1]):
            if force_closed_contours:
                xy_coords.append(xy_coords[0])

        pl = Polygon(xy_coords, name=name)
        if reference == "center":
            pl.translate(x_zero, y_zero)

        wsi_annot.add_annotation_object(pl, layer='base')

    return wsi_annot


