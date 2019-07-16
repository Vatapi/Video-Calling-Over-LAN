import cv2
cap = cv2.VideoCapture(0)
print (cap.get(cv2.CAP_PROP_BUFFERSIZE))

a = cap.set(cv2.CAP_PROP_BUFFERSIZE , 3)
print (a)
