import base64
import json

from io import BytesIO
from qtpy import QtCore
# from qtpy.QtCore import Qt
# from qtpy import QtGui
# from qtpy import QtWidgets

import csv
import os.path
import sys


PY2 = sys.version_info[0] == 2


class LabelFileError(Exception):
    pass


class LabelFile(object):

    suffix = '.json'
    # suffix = '.csv'

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        if filename is not None:
            self.load(filename)
        self.filename = filename

    def load(self, filename):
        keys = [
            'imageData',
            'imagePath',
            'lineColor',
            'fillColor',
            'shapes',  # polygonal annotations
            'flags',   # image level flags # for deep zoom image
        ]
        try:
            with open(filename, 'rb' if PY2 else 'r') as f:
                data = json.load(f)

            if data['imageData'] is not None:
                imageData = base64.b64decode(data['imageData'])
            else:
                # relative path from label file to relative path from cwd
                imagePath = os.path.join(os.path.dirname(filename), data['imagePath'])
                with open(imagePath, 'rb') as f:
                    imageData = f.read()

            flags = data.get('flags')
            imagePath = data['imagePath']
            lineColor = data['lineColor']
            fillColor = data['fillColor']
            shapes = (
                (s['label'], s['points'], s['line_color'], s['fill_color'])
                for s in data['shapes']
            )
        except Exception as e:
            raise LabelFileError(e)

        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        self.imageData = imageData
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.filename = filename
        self.otherData = otherData

    def save(self, filename, shapes, imagePath, imageData=None,
             lineColor=None, fillColor=None, otherData=None,
             flags=None):
        if imageData is not None:
            if str(type(imageData)) == "<class 'bytes'>":
                imageData = base64.b64encode(imageData).decode('utf-8')

            elif str(type(imageData)) == "<class 'PIL.Image.Image'>":
                buffered = BytesIO()
                imageData.save(buffered, format="JPEG")
                imageData = base64.b64encode(buffered.getvalue()).decode('utf-8')

        if otherData is None:
            otherData = {}
        if flags is None:
            flags = [] #imageData.level
        data = dict(
            flags=flags,
            shapes=shapes,
            lineColor=lineColor,
            fillColor=fillColor,
            imagePath=imagePath,
            imageData=imageData,
        )
        for key, value in otherData.items():
            data[key] = value
        try:
            with open(filename, 'wb' if PY2 else 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                self.saveCSVFile(filename, data)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    def saveCSVFile(self, filename, data):
        filename = filename[:-5] +'.csv'

        with open(filename, 'wb' if PY2 else 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow('label' + ',' + 'points')
            for d, dat in enumerate(data['shapes']):
                pts = [dat['label'] + ',']
                for (x, y) in dat['points']:
                    pts.append(str(x) + ',')
                    pts.append(str(y) + ',')

                # writer.writerow(str(p) for p in pts)
                writer.writerow(pts)


    @staticmethod
    def isLabelFile(filename):
        return os.path.splitext(filename)[1].lower() == LabelFile.suffix

