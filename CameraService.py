import ssl

import cv2 as cv

import paho.mqtt.client as mqtt
import base64
import threading
import time

import json

from ColorDetector import ColorDetector

from picamera2 import Picamera2

from YOLOv5 import YOLOv5


def send_video_stream(origin, client):
    global sending_video_stream
    global cap
    global quality
    global period
    global cam_mode
    global picam2
    topic_to_publish = f"cameraService/{origin}/videoFrame"

    while sending_video_stream:
        if cam_mode == "webcam":
            # Read Frame
            ret, frame = cap.read()
            if ret:
                ################################################################################
                encode_param = [int(cv.IMWRITE_JPEG_QUALITY), quality]
                _, image_buffer = cv.imencode(".jpg", frame, encode_param)
                jpg_as_text = base64.b64encode(image_buffer)
                client.publish(topic_to_publish, jpg_as_text)
                time.sleep(period)
                ################################################################################
        elif cam_mode == "picamera2":
            # Read Frame
            frame = picam2.capture_array()

            ################################################################################
            encode_param = [int(cv.IMWRITE_JPEG_QUALITY), quality]
            _, image_buffer = cv.imencode(".jpg", frame, encode_param)
            jpg_as_text = base64.b64encode(image_buffer)
            client.publish(topic_to_publish, jpg_as_text)
            time.sleep(period)
            ################################################################################


def send_video_for_calibration(origin, client):
    global sending_video_for_calibration
    global cap
    global colorDetector
    global cam_mode
    global picam2
    topic_to_publish = f"cameraService/{origin}/videoFrame"

    while sending_video_for_calibration:
        if cam_mode == "webcam":
            # Read Frame
            ret, frame = cap.read()
            if ret:
                frame = colorDetector.MarkFrameForCalibration(frame)
                _, image_buffer = cv.imencode(".jpg", frame)
                jpg_as_text = base64.b64encode(image_buffer)
                client.publish(topic_to_publish, jpg_as_text)
                time.sleep(0.2)
        elif cam_mode == "picamera2":
            # Read Frame
            frame = picam2.capture_array()

            frame = colorDetector.MarkFrameForCalibration(frame)
            _, image_buffer = cv.imencode(".jpg", frame)
            jpg_as_text = base64.b64encode(image_buffer)
            client.publish(topic_to_publish, jpg_as_text)
            time.sleep(0.2)


def send_video_with_colors(origin, client):
    global finding_colors
    global cap
    global colorDetector
    global cam_mode
    global picam2
    topic_to_publish = f"cameraService/{origin}/videoFrameWithColor"

    while finding_colors:
        if cam_mode == "webcam":
            # Read Frame
            ret, frame = cap.read()
            if ret:
                frame, color = colorDetector.DetectColor(frame)
                _, image_buffer = cv.imencode(".jpg", frame)
                frame_as_text = base64.b64encode(image_buffer)
                base64_string = frame_as_text.decode("utf-8")
                frame_with_colorJson = {"frame": base64_string, "color": color}
                frame_with_color = json.dumps(frame_with_colorJson)
                client.publish(topic_to_publish, frame_with_color)
                time.sleep(0.2)
        elif cam_mode == "picamera2":
            # Read Frame
            frame = picam2.capture_array()

            frame, color = colorDetector.DetectColor(frame)
            _, image_buffer = cv.imencode(".jpg", frame)
            frame_as_text = base64.b64encode(image_buffer)
            base64_string = frame_as_text.decode("utf-8")
            frame_with_colorJson = {"frame": base64_string, "color": color}
            frame_with_color = json.dumps(frame_with_colorJson)
            client.publish(topic_to_publish, frame_with_color)
            time.sleep(0.2)


def detection(origin, client):
    global cap
    global quality
    global period
    global cam_mode
    global cap
    global picam2
    global detecting
    global yolov5
    topic_to_publish = f"cameraService/{origin}/detectionVideoFrame"
    topic_to_publish2 = f"cameraService/{origin}/objectDetected"
    
    # configure image quality
    if cam_mode == "webcam":
        width = 640*quality/100
        height = 480*quality/100
        cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
    elif cam_mode == "picamera2":
        if quality > 95:
            quality = 95
        picam2.options["quality"] = quality
        
     # start loop for detection
    detected = False
    while detecting:
        if cam_mode == "webcam":
            frame, detected = yolov5.detect_webcam(cap)
        elif cam_mode == "picamera2":
            frame, detected = yolov5.detect_picam2(picam2)
        
        _, image_buffer = cv.imencode(".jpg", frame)
        jpg_as_text = base64.b64encode(image_buffer)
        client.publish(topic_to_publish, jpg_as_text)
        time.sleep(period)
        
        if detected == True:
            client.publish(topic_to_publish2)
            


def process_message(message, client):

    global sending_video_stream
    global sending_video_for_calibration
    global finding_colors
    global cap
    global colorDetector
    global quality
    global period
    global cam_mode
    global picam2
    global detecting
    global yolov5

    splited = message.topic.split("/")
    origin = splited[0]
    command = splited[2]
    print("recibo ", command, "de ", origin)

    if command == "takePicture":
        print("Take picture")
        ret = False
        if cam_mode == "webcam":
            for n in range(1, 20):
                # this loop is required to discard first frames
                ret, frame = cap.read()
        elif cam_mode == "picamera2":
            for n in range(1, 20):
                # this loop is required to discard first frames
                frame = picam2.capture_array()
        _, image_buffer = cv.imencode(".jpg", frame)
        # Converting into encoded bytes
        jpg_as_text = base64.b64encode(image_buffer)
        client.publish("cameraService/" + origin + "/picture", jpg_as_text)

    if command == "startVideoStream":
        ################################################################################
        payload = message.payload.decode("utf-8")
        if payload == "":
            quality = 50
            period = 0.2
        else:
            payload_splited = payload.split("/")
            quality = int(payload_splited[0])
            period = float(payload_splited[1])
        ################################################################################
        print("start video stream")
        sending_video_stream = True
        w = threading.Thread(
            target=send_video_stream,
            args=(origin, client),
        )
        w.start()

    if command == "stopVideoStream":
        print("stop video stream")
        sending_video_stream = False

    if command == "markFrameForCalibration":
        print("markFrameForCalibration")
        sending_video_for_calibration = True
        w = threading.Thread(
            target=send_video_for_calibration,
            args=(origin, client),
        )
        w.start()
    if command == "stopCalibration":
        print("stop calibration")
        sending_video_for_calibration = False
    if command == "getDefaultColorValues":
        yellow, green, blueS, blueL, pink, purple = colorDetector.DameValores()
        colorsJson = {
            "yellow": yellow,
            "green": green,
            "blueS": blueS,
            "blueL": blueL,
            "pink": pink,
            "purple": purple,
        }
        colors = json.dumps(colorsJson)
        print("envio: ", colorsJson)
        client.publish("cameraService/" + origin + "/colorValues", colors)
    if command == "getColorValues":
        colorDetector.TomaValores()
        print("ya he tomado los valores")
        yellow, green, blueS, blueL, pink, purple = colorDetector.DameValores()
        colorsJson = {
            "yellow": yellow,
            "green": green,
            "blueS": blueS,
            "blueL": blueL,
            "pink": pink,
            "purple": purple,
        }
        print("voy a enviar: ", colorsJson)
        colors = json.dumps(colorsJson)
        print("envio: ", colorsJson)
        client.publish("cameraService/" + origin + "/colorValues", colors)

    if command == "takeValues":
        colorDetector.TomaValores()

    if command == "startFindingColor":
        finding_colors = True
        w = threading.Thread(
            target=send_video_with_colors,
            args=(origin, client),
        )
        w.start()
    if command == "stopFindingColor":
        finding_colors = False

    if command == "startDetection":
        payload = message.payload.decode("utf-8")
        payload_splited = payload.split("/")
        object_ = str(payload_splited[0])
        quality = int(payload_splited[1])
        period = float(payload_splited[2])
        yolov5.load_model(object_)

        print("start detection")
        detecting = True
        w = threading.Thread(
            target=detection,
            args=(origin, client),
        )
        w.start()

    if command == "stopDetection":
        print("stop detection")
        detecting = False


def on_internal_message(client, userdata, message):
    print("recibo internal ", message.topic)
    global internal_client
    process_message(message, internal_client)


def on_external_message(client, userdata, message):
    print("recibo external ", message.topic)

    global external_client
    process_message(message, external_client)


def on_connect(external_client, userdata, flags, rc):
    if rc == 0:
        print("Connection OK")
    else:
        print("Bad connection")


def CameraService(connection_mode, operation_mode, camera_mode, external_broker, username, password):
    global op_mode
    global external_client
    global internal_client
    global state
    global cap
    global colorDetector
    global picam2
    global cam_mode
    global yolov5

    sending_video_stream = False

    if camera_mode == "webcam":
        cap = cv.VideoCapture(0)  # video capture source camera (Here webcam of lap>
    elif camera_mode == "picamera2":
        # start the RPi on board camera (picamera2)
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        picam2.start()
    cam_mode = camera_mode

    colorDetector = ColorDetector()

    yolov5 = YOLOv5()

    print("Camera ready")

    print("Connection mode: ", connection_mode)
    print("Operation mode: ", operation_mode)
    op_mode = operation_mode

    internal_client = mqtt.Client("Autopilot_internal")
    internal_client.on_message = on_internal_message
    internal_client.connect("localhost", 1884)

    state = "disconnected"

    print("Connection mode: ", connection_mode)
    print("Operation mode: ", operation_mode)
    op_mode = operation_mode

    internal_client = mqtt.Client("Camera_internal")
    internal_client.on_message = on_internal_message
    internal_client.connect("localhost", 1884)

    external_client = mqtt.Client("Camera_external", transport="websockets")
    external_client.on_message = on_external_message
    external_client.on_connect = on_connect

    if connection_mode == "global":
        if external_broker == "hivemq":
            external_client.connect("broker.hivemq.com", 8000)
            print("Connected to broker.hivemq.com:8000")

        elif external_broker == "hivemq_cert":
            external_client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )
            external_client.connect("broker.hivemq.com", 8884)
            print("Connected to broker.hivemq.com:8884")

        elif external_broker == "classpip_cred":
            external_client.username_pw_set(username, password)
            external_client.connect("classpip.upc.edu", 8000)
            print("Connected to classpip.upc.edu:8000")

        elif external_broker == "classpip_cert":
            external_client.username_pw_set(username, password)
            external_client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )
            external_client.connect("classpip.upc.edu", 8883)
            print("Connected to classpip.upc.edu:8883")
        elif external_broker == "localhost":
            external_client.connect("localhost", 8000)
            print("Connected to localhost:8000")
        elif external_broker == "localhost_cert":
            print("Not implemented yet")

    elif connection_mode == "local":
        if operation_mode == "simulation":
            external_client.connect("localhost", 8000)
            print("Connected to localhost:8000")
        else:
            external_client.connect("10.10.10.1", 8000)
            print("Connected to 10.10.10.1:8000")

    print("Waiting....")
    external_client.subscribe("+/cameraService/#", 2)
    internal_client.subscribe("+/cameraService/#")
    internal_client.loop_start()
    external_client.loop_forever()


if __name__ == "__main__":
    import sys

    connection_mode = sys.argv[1]  # global or local
    operation_mode = sys.argv[2]  # simulation or production
    camera_mode = sys.argv[3]  # webcam or picamera2
    username = None
    password = None
    if connection_mode == "global":
        external_broker = sys.argv[4]
        if external_broker == "classpip_cred" or external_broker == "classpip_cert":
            username = sys.argv[5]
            password = sys.argv[6]
    else:
        external_broker = None

    CameraService(connection_mode, operation_mode, camera_mode, external_broker, username, password)
