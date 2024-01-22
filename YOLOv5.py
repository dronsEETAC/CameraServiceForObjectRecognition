import torch
import cv2 as cv
import pandas

class YOLOv5:
    def __init__(self):
        self.object = None
        self.model = None
    
    def load_model(self, object):
        self.object = object
        model_path = f"weights/{object}.pt"
        # I think that the following loads the local model without needing Internet connection
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)

    def detect_picam2(self, picam2):
        frame = picam2.capture_array()

        # Inference
        pred = self.model(frame)
        # xmin,ymin,xmax,ymax
        df = pred.pandas().xyxy[0]
        # Filter by confidence
        df = df[df["confidence"] > 0.5]

        for i in range(df.shape[0]):
            bbox = df.iloc[i][["xmin", "ymin", "xmax", "ymax"]].values.astype(int)

            # Give land order if object is detected
            if df.iloc[i]['name'] == self.object and df.iloc[i]['confidence'] > 0.6:
                print(f"{df.iloc[i]['name']} detected. Sending land order...")
                # publish land order (autopilotService)
                return True
                # autopilot_client.publish("AutopilotClient/autopilotService/land")


            # print bboxes: frame -> (xmin, ymin), (xmax, ymax)
            #cv.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
            # print text
            #cv.putText(frame,
            #            f"{df.iloc[i]['name']}: {round(df.iloc[i]['confidence'], 4)}",
            #            (bbox[0], bbox[1] - 15),
            #            cv.FONT_HERSHEY_PLAIN,
            #            1,
            #            (255, 255, 255),
            #            2)

        #cv.imshow("Camera", frame) # for testing purposes, comment line after testing
        return False
    
    def detect_webcam(self, cap):
        ret, frame = cap.read()

        # Inference
        pred = self.model(frame)
        # xmin,ymin,xmax,ymax
        df = pred.pandas().xyxy[0]
        # Filter by confidence
        df = df[df["confidence"] > 0.5]

        for i in range(df.shape[0]):
            bbox = df.iloc[i][["xmin", "ymin", "xmax", "ymax"]].values.astype(int)

            # Give land order if object is detected
            if df.iloc[i]['name'] == self.object and df.iloc[i]['confidence'] > 0.6:
                print(f"{df.iloc[i]['name']} detected. Sending land order...")
                # publish land order (autopilotService)
                return True

            # print bboxes: frame -> (xmin, ymin), (xmax, ymax)
            #cv.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
            # print text
            #cv.putText(frame,
            #            f"{df.iloc[i]['name']}: {round(df.iloc[i]['confidence'], 4)}",
            #            (bbox[0], bbox[1] - 15),
            #            cv.FONT_HERSHEY_PLAIN,
            #            1,
            #            (255, 255, 255),
            #            2)

        #cv.imshow("Camera", frame) # for testing purposes, comment line after testing
        return False
