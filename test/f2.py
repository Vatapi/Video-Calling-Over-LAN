from flask import Flask, render_template, Response
# import os
# import random
import cv2
from socket import socket, AF_INET, SOCK_STREAM
from imutils.video import WebcamVideoStream
import pyaudio
from array import array
from threading import Thread
import numpy as np
import zlib
import struct

# HOST = input("Enter Server IP\n")
HOST = "172.16.84.167"
PORT_VIDEO = 3000
PORT_AUDIO = 4000

BufferSize = 4096
CHUNK=1024
lnF = 640*480*3
FORMAT=pyaudio.paInt16
CHANNELS=2
RATE=44100
startaudio = 1
startvideo = 1
Quit = False
app = Flask(__name__)

@app.route('/')
def home():
    #os.system("python3 script.py")
    return render_template('home.html')

@app.route('/hosted')
def hosting():
    ServerThread = Thread(target = ServerMedia , args= ()) #Add ServerMedia file as a function<3
    ServerThread.start()
    return render_template('index.html')

@app.route('/connectfeed')
def connectfeed():
    return render_template("index.html")


def gen(clientVideoSocket):
    while Quit!=True:
        lengthbuf = recvallVideo(clientVideoSocket,4)
        length, = struct.unpack('!I', lengthbuf)
        databytes = recvallVideo(clientVideoSocket,length)
        img = zlib.decompress(databytes)
        if len(databytes) == length:
            print("Recieving Media..")
            print("Image Frame Size:- {}".format(len(img)))
            # img = np.array(list(img))
            # img = np.array(img, dtype = np.uint8).reshape(480, 640, 3)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n\r\n')
        else:
            print("Data CORRUPTED")

@app.route('/video_feed')
def video_feed():
    clientVideoSocket = socket(family=AF_INET, type=SOCK_STREAM)
    clientVideoSocket.connect((HOST, PORT_VIDEO))


    clientAudioSocket = socket(family=AF_INET, type=SOCK_STREAM)
    clientAudioSocket.connect((HOST, PORT_AUDIO))

    audio=pyaudio.PyAudio()
    stream=audio.open(format=FORMAT,channels=CHANNELS, rate=RATE, input=True, output = True,frames_per_buffer=CHUNK)

    initiation = clientVideoSocket.recv(5).decode()

    if initiation == "start":
        SendFrameThread = Thread(target=SendFrame, args=(clientVideoSocket,)).start()
        #SendAudioThread = Thread(target=SendAudio, args=(clientAudioSocket,stream,)).start()
        #RecieveFrameThread = Thread(target=RecieveFrame).start()
        #RecieveAudioThread = Thread(target=RecieveAudio,args=(clientAudioSocket, stream,)).start()

    return Response(gen(clientVideoSocket),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



def SendAudio(clientAudioSocket,stream):
    while Quit!=True:
        if startaudio == 1:
            data = stream.read(CHUNK)
            clientAudioSocket.sendall(data)
        else:
            pass

def RecieveAudio(clientAudioSocket,stream):
    while Quit!=True:
        data = recvallAudio(clientAudioSocket,BufferSize)
        stream.write(data)

def recvallAudio(clientAudioSocket,size):
    databytes = b''
    while len(databytes) != size:
        to_read = size - len(databytes)
        if to_read > (4 * CHUNK):
            databytes += clientAudioSocket.recv(4 * CHUNK)
        else:
            databytes += clientAudioSocket.recv(to_read)
    return databytes


@app.route('/audio')
def listen():
    global startaudio
    if startaudio == 0:
        startaudio = 1
    else:
        startaudio = 0
    print("success")
    return "jbsdj"


def SendFrame(clientVideoSocket):
    wvs = WebcamVideoStream(0).start()
    while Quit!=True:
        if startvideo == 1:
            frame = wvs.read()
            #cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            #print(frame)
            ret, frame = cv2.imencode('.jpg', frame)
            # frame = np.array(frame, dtype = np.uint8).reshape(1, lnF)
            # jpg_as_text = bytearray(frame)
            jpg_as_text = frame.tobytes()
            databytes = zlib.compress(jpg_as_text, 9)
            length = struct.pack('!I', len(databytes))
            bytesToBeSend = b''
            clientVideoSocket.sendall(length)
            while len(databytes) > 0:
                if (5000 * CHUNK) <= len(databytes):
                    bytesToBeSend = databytes[:(5000 * CHUNK)]
                    databytes = databytes[(5000 * CHUNK):]
                    clientVideoSocket.sendall(bytesToBeSend)
                else:
                    bytesToBeSend = databytes
                    clientVideoSocket.sendall(bytesToBeSend)
                    databytes = b''
            print("##### Data Sent!! #####")
        else:
            pass

def recvallVideo(clientVideoSocket,size):
    databytes = b''
    while len(databytes) != size:
        to_read = size - len(databytes)
        if to_read > (1000 * CHUNK):
            databytes += clientVideoSocket.recv(1000 * CHUNK)
        else:
            databytes += clientVideoSocket.recv(to_read)
    return databytes

@app.route('/video')
def video():
    global startvideo
    if startvideo == 1:
        startvideo = 0
    else:
        startvideo = 1
    print ("Sucess Video")
    return "jskjdhsjk"


@app.route('/quit')
def Quit():
    global Quit
    Quit = True
    print ("Quit Sucess")
    return redirect(url_for('/'))


def ServerMedia():
    # HOST = input("Enter Host IP\n")
    HOST = "172.16.84.167"
    PORT_VIDEO = 3000
    PORT_AUDIO = 4000
    lnF = 640*480*3
    CHUNK = 1024
    BufferSize = 4096
    addressesAudio = {}
    addresses = {}
    threads = {}

    def ConnectionsVideo():
        while True:
            try:
                clientVideo, addr = serverVideo.accept()
                print("{} is connected!!".format(addr))
                addresses[clientVideo] = addr
                if len(addresses) > 1:
                    for sockets in addresses:
                        if sockets not in threads:
                            threads[sockets] = True
                            sockets.send(("start").encode())
                            Thread(target=ClientConnectionVideo, args=(sockets, )).start()
                else:
                    continue
            except:
                continue

    def ConnectionsSound():
        while True:
            try:
                clientAudio, addr = serverAudio.accept()
                print("{} is connected!!".format(addr))
                addressesAudio[clientAudio] = addr
                Thread(target=ClientConnectionSound, args=(clientAudio, )).start()
            except:
                continue

    def ClientConnectionVideo(clientVideo):
        while True:
            try:
                lengthbuf = recvall(clientVideo, 4)
                length, = struct.unpack('!I', lengthbuf)
                recvall(clientVideo, length)
            except:
                continue

    def ClientConnectionSound(clientAudio):
        while True:
            try:
                data = clientAudio.recv(BufferSize)
                broadcastSound(clientAudio, data)
            except:
                continue

    def recvall(clientVideo, BufferSize):
            databytes = b''
            i = 0
            while i != BufferSize:
                to_read = BufferSize - i
                if to_read > (1000 * CHUNK):
                    databytes = clientVideo.recv(1000 * CHUNK)
                    i += len(databytes)
                    broadcastVideo(clientVideo, databytes)
                else:
                    if BufferSize == 4:
                        databytes += clientVideo.recv(to_read)
                    else:
                        databytes = clientVideo.recv(to_read)
                    i += len(databytes)
                    if BufferSize != 4:
                        broadcastVideo(clientVideo, databytes)
            print("YES!!!!!!!!!" if i == BufferSize else "NO!!!!!!!!!!!!")
            if BufferSize == 4:
                broadcastVideo(clientVideo, databytes)
                return databytes

    def broadcastVideo(clientSocket, data_to_be_sent):
        for clientVideo in addresses:
            if clientVideo != clientSocket:
                clientVideo.sendall(data_to_be_sent)

    def broadcastSound(clientSocket, data_to_be_sent):
        for clientAudio in addressesAudio:
            if clientAudio != clientSocket:
                clientAudio.sendall(data_to_be_sent)

    serverVideo = socket(family=AF_INET, type=SOCK_STREAM)
    try:
        serverVideo.bind((HOST, PORT_VIDEO))
    except OSError:
        print("Server Busy")

    serverAudio = socket(family=AF_INET, type=SOCK_STREAM)
    try:
        serverAudio.bind((HOST, PORT_AUDIO))
    except OSError:
        print("Server Busy")

    serverAudio.listen(2)
    print("Waiting for connection..")
    AcceptThreadAudio = Thread(target=ConnectionsSound)
    AcceptThreadAudio.start()


    serverVideo.listen(2)
    print("Waiting for connection..")
    AcceptThreadVideo = Thread(target=ConnectionsVideo)
    AcceptThreadVideo.start()
    AcceptThreadVideo.join()
    serverVideo.close()

if __name__ == "__main__":
    app.run(debug=True)
