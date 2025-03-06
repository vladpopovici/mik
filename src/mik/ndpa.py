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

def load_NDPA(ndpi: WSI, ndpa: Union[str, Path], force_closed_contours: bool=False) -> Annotation:
    ndpa = Path(ndpa)
    xml_file = ET.parse(ndpa)
    xml_root = xml_file.getroot()

    try:
        x_off = int(ndpi._original_meta['hamamatsu.XOffsetFromSlideCentre'])
        y_off = int(ndpi._original_meta['hamamatsu.YOffsetFromSlideCentre'])
    except KeyError:
        raise RuntimeError('probably not a Hamamatsu NDPI file')

    x_mpp = float(ndpi.info['mpp_x'])
    y_mpp = float(ndpi.info['mpp_y'])
    dimX0, dimY0 = ndpi.extent(0)

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

            x = int(np.floor(x + dimX0 / 2.0)) # in pixels, relative to UL corner
            y = int(np.floor(y + dimY0 / 2.0))

            xy_coords.append([x, y])

        if len(xy_coords) < 5:
            # too short
            continue

        # check the last point to match the first one
        if (xy_coords[0][0] != xy_coords[-1][0]) or (xy_coords[0][1] != xy_coords[-1][1]):
            if force_closed_contours:
                xy_coords.append(xy_coords[0])

        wsi_annot.add_annotation_object(Polygon(xy_coords, name=name), layer='base')

    return wsi_annot


