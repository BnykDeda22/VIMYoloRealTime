import numpy as np
from ultralytics import YOLO


class ODModel:
    def __init__(self, path_to_weights=r"weights/apples.pt"):
        self.model = YOLO(path_to_weights).to('cuda:0')
        self.classes = self.model.names

    def predict(self, frame, imgsz=960, conf=0.26, nms=True, classes=None, device=None):
        filter_classes = classes if classes else None
        # Detect objects
        results = self.model.predict(source=frame,
                                     imgsz=imgsz,
                                     conf=conf,
                                     nms=nms,
                                     classes=filter_classes
                                     )

        # Get the first result from the array as we are only using one image
        result = results[0]
        # Get bboxes
        bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
        # Get class ids
        class_ids = np.array(result.boxes.cls.cpu(), dtype="int")
        # Get scores
        # round score to 2 decimal places
        scores = np.array(result.boxes.conf.cpu(), dtype="float").round(2)
        return bboxes, class_ids, scores
