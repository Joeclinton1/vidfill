from tkinter import *
from tkinter import messagebox
from tkinter import Tk
from tkinter.colorchooser import *
import os, glob, cv2
import numpy as np
from lxml import etree as ET
import re
import math
from ctypes import windll
np.set_printoptions(threshold=sys.maxsize)
colourOnRelease = False
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
#import squareTrace



def img2ContoursSingle(filepath, threshvalue):
    img = cv2.imread(filepath)
    img = cv2.fastNlMeansDenoising(img, None, 8, 21, 7)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img, threshvalue, 255, cv2.THRESH_BINARY_INV)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)
    thresh = cv2.rectangle(thresh, (2, 2), (int(vidW) - 2, int(vidH) - 1), 255, 2)
    im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    return contours

def img2ContoursMult(filepath,options):
    steps = options[0]
    offsetL = options[1]
    offsetH = options[2]
    img = cv2.imread(filepath)
    img = cv2.fastNlMeansDenoising(img, None, 8, 21, 7)
    contours = []
    step = (255 - offsetL-offsetH) / steps
    for i in range(steps):
        offH = offsetL+offsetH if i==steps-1 else offsetL
        offL = offsetL if i!=0 else 0
        im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(i*step+offL)
        im[(im > (i+1)*step+offH) | (im < i*step+offL)] = 0
        im[(im >= i*step+offL) & (im <= (i+1)*step+offH)] = 255
        thresh = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
        thresh = cv2.rectangle(thresh, (1, 1), (int(vidW) - 1, int(vidH) - 1),0,2)
        im2, subContours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        contours.extend(subContours)
        """im2 = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(im2, contours, -1, (0, 255, 0), 3)
        cv2.imshow("image", im2)
        cv2.waitKey(0)"""

    return sorted(contours, key=cv2.contourArea,reverse=True)

def cntWrite(isMult,filepath, newContours):
    root = ET.Element("svg", width=str(vidW), height=str(vidH), xmlns="http://www.w3.org/2000/svg", stroke="black")
    if isMult:
        path = "M3 3,  3 717,1277  717,1277    3,4 3"
        ET.SubElement(root, "path", style="fill:#ffffff", d=path)
    for i, cnt in enumerate(newContours):
        #epsilon = 0.02*cv2.arcLength(cnt,True)
        approx = cv2.approxPolyDP(cnt, 0.6, False)
        listCnt = np.vstack(approx).squeeze()
        if len(approx) < 4 or (cv2.contourArea(approx) > vidW * vidH * 0.9 and isMult):
            continue
        else:
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, listCnt)))
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
    tree = ET.ElementTree(root)
    tree.write(filepath)


def cntModify(filepath, contours):
    root = ET.Element("svg", width=str(vidW), height=str(vidH), xmlns="http://www.w3.org/2000/svg", stroke="black")
    for cnt in contours:
        path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt[0])))
        ET.SubElement(root, "path", style="fill:" + cnt[1], d=path)
    tree = ET.ElementTree(root)
    tree.write(filepath)


def svgMult2Vid(popup):
    sFrame = int(popup[0].get())
    eFrame = int(popup[1].get())
    title = popup[2].get()
    convert2Png = popup[3].get()
    popup[4].destroy()
    outVidName = rootDir + title + ".mp4"
    if sFrame >= 1 and eFrame <= numFrames:
        if convert2Png != 1:
            for i in range(sFrame, eFrame + 1):
                drawing = svg2rlg(folderName + "/frame%d.svg" % i)
                renderPM.drawToFile(drawing, folderName + "/frame%d.png" % i, fmt="PNG")
        images = {}
        for img in os.listdir(folderName):
            if img.endswith(".png"):
                fileNum = int(re.sub("[^0-9]", "", img))
                if sFrame <= fileNum <= eFrame:
                    images[fileNum] = img

        fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
        video = cv2.VideoWriter(outVidName, fourcc, 15, (int(vidW), int(vidH)), True)
        for key, image in sorted(images.items()):
            video.write(cv2.imread(os.path.join(folderName, image)))

        cv2.destroyAllWindows()
        video.release()


def convertVideo(popup=None):
    global cPoints
    global folderName
    scanType = popup[3].get()
    scanOption = popup[4]
    print(scanOption)
    print(scanType)

    if scanType == "single":
        scanOption = int(scanOption.get())
        if scanOption > 255 or scanOption < 0:
            return
    else:
        scanOption = list(map(lambda x: int(x.get()), scanOption))
        if (scanOption[0] > 15 or scanOption[0] < 2) and (scanOption[1] < 0 or scanOption[1] > 100):
            return

    if not popup or popup[0].get() == '':
        global folderNum
        folderNum += 1
        folderName = rootDir + "frames_" + str(folderNum).zfill(2)

        os.mkdir(folderName)
        sFrame = 0
        eFrame = numFrames
        cPoints = []
        cPointsWrite(folderNameNew)

    else:
        sFrame = int(popup[0].get())
        eFrame = int(popup[1].get())
        popup[2].destroy()


    for count in range(sFrame, eFrame+1):
        vidCap.set(cv2.CAP_PROP_POS_MSEC, count * 67)
        success, frame = vidCap.read()
        filepathBMP = folderName + "/frame%d.bmp" % count
        filepathXML = folderName + "/frame%d.svg" % count
        if not popup:
            cv2.imwrite(filepathBMP, frame)
        if scanType=="single":
            contours = img2ContoursSingle(filepathBMP,scanOption)
            cntWrite(False, filepathXML, contours)
        else:
            contours = img2ContoursMult(filepathBMP,scanOption)
            cntWrite(True, filepathXML, contours)



def readContours(frame, drawContours):
    global contours
    contours = []
    tree = ET.parse(folderName + "/frame%d.svg" % frame)
    for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
        array = path.get("d")[1:].split(",")
        fill = path.get("style")[6:]
        colour = tuple(int(fill[i:i + 2], 16) for i in (0, 2, 4))

        for i, s in enumerate(array):
            array[i] = list(map(int, s.split()))

        contourNP = np.array(array)
        print(contourNP)
        tkPolygon = [item * scale for sublist in array for item in sublist]
        contours.append([contourNP, "#" + fill])
        if (drawContours):
            polygon = canvas.create_polygon(tkPolygon, fill="#" + fill, outline='#ff0000')
            canvas.tag_bind(polygon, "<ButtonRelease-1>", canvasRelease)


def nextImage():
    global frame
    if frame < numFrames:
        frame += 1
        entry.delete(0, END)
        entry.insert(0, frame)
        showImage()


def prevImage():
    global frame
    if frame > 1:
        frame -= 1
        entry.delete(0, END)
        entry.insert(0, frame)
        showImage()


def goToFrame(event):
    frameNum = int(entry.get())
    if 0 < frameNum < numFrames:
        global frame
        frame = frameNum
        showImage()
    else:
        entry.delete(0, END)
        entry.insert(0, frame)
    root.focus_set()


def showImage():
    canvas.delete("all")
    readContours(frame, True)
    canvas.bind("<Button-1>", canvasClick)
    canvas.bind("<B1-Motion>", mouseHoldMove)
    for index, cPoint in enumerate(cPoints):
        points = cPoint[2]
        colour = cPoint[1]
        type = [1, 1]
        prevPoint = 0
        for i, point in enumerate(points):
            ptFrame = cPoint[-1][i]
            sFrame = cPoint[-1][0]
            movType = cPoint[0][1]
            cType = cPoint[0][0]
            eFrame = cPoint[-1][-1]
            scaledPt = [scale * x for x in point]
            if sFrame <= frame <= eFrame or (movType == 1 and cType != 1 and sFrame <= frame):
                # ternary conditionals to set value of type
                if movType == 3 or movType == 1:
                    type[0] = 1 if i == 0 else 3 if i == len(points) - 1 else 2
                    type[1] = 1 if ptFrame == frame else 2
                else:
                    type[0] = 1 if frame == sFrame else 3 if frame == eFrame else 2
                    type[1] = 1 if frame == sFrame else 2
                if i > 0:
                    canvas.create_line(prevPoint, scaledPt)
                if type != [2, 2] or movType == 2:
                    createShape(colour, scaledPt, [index, i], tuple(type))
            prevPoint = scaledPt


def mouseDown(event):
    global lastx
    global lasty
    lastx = event.x
    lasty = event.y


def mouseHoldMove(event, Type=None, index=None):
    global lastx
    global lasty
    global mouseMoved
    global cPoints
    global rectangle
    if index == None and (
            currentTool == "rectangle" or currentTool == "cRect" or currentTool == "mouth"):  # this allows me to create a temp rectangle which resizes with the mouse
        canvas.delete(rectangle)
        rectangle = canvas.create_rectangle(lastx, lasty, event.x, event.y)
        mouseMoved = True
    elif index != None and currentTool != "fill":  # Moves shape when dragged.
        if Type[1] == 1:
            canvas.move(CURRENT, event.x - lastx, event.y - lasty)
            lastx = event.x
            lasty = event.y
        mouseMoved = True


def mouseUp(event, index, identifier, isCurrent):
    global mouseMoved
    ptIndex = index[1]
    index = index[0]
    print(isCurrent)
    print(mouseMoved)
    point2 = (canvas.canvasx(event.x), canvas.canvasy(event.y))
    scaledPt2 = (point2[0] / scale, point2[1] / scale)
    cPoint = cPoints[index]
    sFrame = cPoint[-1][0]

    if not mouseMoved and currentTool != 0:
        modColour(scaledPt2, index, identifier)
    if mouseMoved and isCurrent == False and cPoint[0][
        1] == 1:
        print("add keyframe")  # add a keyframe point to that point only if it is not current and is a new point
        scaledPt1 = cPoint[2][0]

        # modify cPoint to include points for every frame on the line of motion
        frameSpan = frame - sFrame
        interval = np.floor_divide(np.subtract(scaledPt2, scaledPt1), frameSpan)
        cPoint[-1] = []
        cPoint[2] = []
        print(interval)
        for i in range(sFrame, frame + 1):
            cPoint[2].append([scaledPt1[0], scaledPt1[1]])
            cPoint[-1].append(i)
            scaledPt1 = np.add(scaledPt1, interval)
        cPoint[0][1] = 3
        canvas.tag_unbind(identifier, "<ButtonRelease-1>")
        if colourOnRelease:
            colourFrames(sFrame,frame)
        showImage()
        mouseMoved = False
    elif mouseMoved and isCurrent:  # The point has been moved and it's position needs to be modified in the list.
        type = cPoint[0][0]
        if type == 3 or type == 1:
            cPoint[2][ptIndex] = scaledPt2
        elif type == 4 or type == 2:
            rectW = cPoint[2][0][2] - cPoint[2][0][0]
            rectH = cPoint[2][0][3] - cPoint[2][0][1]
            cPoint[2][ptIndex] = (scaledPt2[0], scaledPt2[1], event.x + rectW, event.y + rectH)
        showImage()
        mouseMoved = False


def findVisualCenter(cnt):
    M = cv2.moments(cnt)
    pt = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    dists = np.sum((cnt - pt) ** 2, axis=1)
    n = np.argmin(dists)
    pt2 = cnt[n]
    # rotate contour list so that the start point is first in the list
    rCnt = np.roll(cnt, -1 * n, axis=0)

    dist = 0
    isCloser = False
    for i, cntPt in enumerate(rCnt):
        newDist = np.linalg.norm(cntPt - pt2)
        if isCloser:
            if newDist > dist:
                pt3 = (rCnt[i - 1] + cntPt) / 2
                vCenter = (pt2 + pt3) / 2
                vCt_t = (vCenter[0], vCenter[1])
                if cv2.pointPolygonTest(cnt, vCt_t, measureDist=False) == 1:
                    return vCt_t
                else:
                    isCloser = False
        else:
            if newDist < dist:
                isCloser = True
        dist = newDist
    return False


def escapeContour(pt, cnt, cnt2):
    print(pt)
    dists = np.sum((cnt - pt) ** 2, axis=1)
    n = np.argmin(dists)
    pt2 = cnt[n]

    dists = np.sum((cnt2 - pt2) ** 2, axis=1)
    n = np.argmin(dists)
    pt3 = cnt2[n]

    pt4 = (pt2 + pt3) / 2
    return (pt4[0], pt4[1])


def autoKeyFrame(index, eFrame=None):
    cPoint = cPoints[index]
    cPoint[0][1] = 3
    sFrame = cPoint[-1][0]
    pt = cPoint[2][0]
    readContours(sFrame, False)
    oldCnt = contours[closestCnt(pt)][0]

    f = sFrame + 1
    while True:
        aOld = cv2.contourArea(oldCnt)
        M_old = cv2.moments(oldCnt)
        cOld = (int(M_old["m10"] / M_old["m00"]), int(M_old["m01"] / M_old["m00"]))

        readContours(f, False)
        bestProb = 20
        bestProb2 = 10
        bestCnt = 2
        cntIndex = 0
        for i, cnt in enumerate(contours):
            aRatio = abs(cv2.contourArea(cnt[0]) / aOld - 1)
            M = cv2.moments(cnt[0])
            c = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            dist = math.sqrt((c[0] - cOld[0]) ** 2 + (c[1] - cOld[1]) ** 2)
            sim = cv2.matchShapes(oldCnt, cnt[0], 1, 0.0)

            prob = sim/3 + aRatio / 1.7 + dist / 90
            print(sim/3,aRatio/1.7,dist/90, prob)
            if prob < bestProb2 and prob > bestProb:
                bestProb2 = prob

            if prob < bestProb:
                bestProb = prob
                bestCnt = cnt[0]
                cntIndex = i
        print("bestProb:",bestProb," BestProb2:",bestProb2)
        if eFrame is None and (bestProb > 3.4 or bestProb2<bestProb*1.3):
            return f
        print(" ")

        cnt = bestCnt
        M = cv2.moments(cnt)
        pt = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        if cv2.pointPolygonTest(cnt, pt, measureDist=False) != 1:
            pt = findVisualCenter(cnt)

        if pt == False:
            pt = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        else:
            cntIndex2 = closestCnt(pt)
            innerCnt = contours[cntIndex2][0]
            if cntIndex != cntIndex2:
                pt = escapeContour(pt, innerCnt, cnt)

        cPoint[2].append(pt)
        cPoint[-1].append(f)

        if eFrame is not None and f == eFrame:
            break

        oldCnt = cnt
        f += 1


def contextMenu(event, index, type):
    popup = Menu(root, tearoff=0)
    popup.add_command(label="Delete point", command=lambda index=index, isStart=type: delPoint(index, isStart))
    if type == (3, 1) and len(cPoints[index][2]) > 1:
        popup.add_command(label="Remove last keyframe", command=lambda index=index: delLastPoint(index))
    if type == (1, 2):
        popup.add_command(label="Set static end point", command=lambda index=index: addEndPoint(index))
        popup.add_command(label="Auto Keyframe",
                          command=lambda index=index, endFrame=frame: autoKeyFrame(index, endFrame))
    if type == (2,1):
        popup.add_command(label="Set to endpoint", command=lambda index=index: changeEndPoint(index))
    popup.post(event.x_root, event.y_root)


def delLastPoint(index):
    cPoints[index][2] = cPoints[index][2][:-1]
    cPoints[index][-1] = cPoints[index][-1][:-1]
    showImage()


def delPoint(index, type):
    if type[0] == 1:
        del cPoints[index]
    else:
        cPoints[index][2] = [cPoints[index][2][0]]
        cPoints[index][0][1] = 1
        cPoints[index][-1] = [cPoints[index][-1][0]]
    showImage()


def createShape(activeColour, coord, index, type):
    colourDict = {(1, 1): "#00ff00", (1, 2): "#dbffe3", (2, 1): "#ffff00", (2, 2): "#ffffb5", (3, 1): "#ff0000",
                  (3, 2): "#ffd0ce"}
    colour = colourDict[type]
    if cPoints[index[0]][0][0] == 1:
        colour = '#38eeff'
    r = 5
    x = coord[0]
    y = coord[1]

    if len(coord) == 4:
        x2 = coord[2]
        y2 = coord[3]
        shape = canvas.create_rectangle(x, y, x2, y2, outline=colour, width=3, activefill=activeColour,
                                        activestipple='gray25')
    else:
        shape = canvas.create_oval(x - r, y - r, x + r, y + r, fill=colour, width=1, activefill=activeColour)

    canvas.tag_bind(shape, "<1>", mouseDown)
    canvas.tag_bind(shape, "<B1-Motion>", lambda event, Type=type, index=index[0]: mouseHoldMove(event, Type, index))
    iscurrent = True if type[1] == 1 else False
    canvas.tag_bind(shape, "<ButtonRelease-1>",
                    lambda event, index=index, identifier=shape, isCurrent=iscurrent: mouseUp(event, index, identifier,
                                                                                              isCurrent))
    canvas.tag_bind(shape, "<Button-3>", lambda event, index=index[0], type=type: contextMenu(event, index, type))


def closestCnt(point):
    tempContours = []
    closest = (10000,)
    for i, c in enumerate(contours):
        if cv2.pointPolygonTest(c[0], point, measureDist=False) > 0:
            tempContours.append((c, i))

    for c in tempContours:
        dist = cv2.pointPolygonTest(c[0][0], point, measureDist=True)
        if dist < closest[0]:
            closest = (dist, c[1])
    return closest[1]


def modColour(point, index, identifier):
    global contours
    cntIndex = closestCnt(point)
    oldColour = cPoints[index][1]
    colour = askcolor(oldColour, parent = dialogRoot)[1]
    root.focus_set()
    if colour != None:
        if currentTool == "cPoint" or currentTool == "cPointStatic":
            contours[cntIndex][1] = colour
            filepath = folderName + "/frame%d.svg" % frame
            cntModify(filepath, contours)
        cPoints[index][1] = colour
        showImage()


def canvasRelease(event):
    if currentTool != 0:
        global mouseMoved
        global contours
        point = (canvas.canvasx(event.x), canvas.canvasy(event.y))
        scaledPt = (point[0] / scale, point[1] / scale)
        cntIndex = closestCnt(scaledPt)
        oldColour = contours[cntIndex][1]
        colour = askcolor(oldColour, parent = dialogRoot)[1]
        root.focus_set()
        if colour:
            if not mouseMoved:  # adding new colour point

                if currentTool == "cPoint" or currentTool == "cPointStatic":
                    contours[cntIndex][1] = colour
                    if (currentTool == "cPointStatic"):
                        cPoints.append([[1, 1], colour, [scaledPt], [frame]])
                    else:
                        cPoints.append([[3, 1], colour, [scaledPt], [frame]])
                    filepath = folderName + "/frame%d.svg" % frame
                    cntModify(filepath, contours)
                    showImage()
                    createShape(colour, point, [len(cPoints) - 1, 0], (1, 1))
                elif currentTool == "cPointAuto":
                    cPoints.append([[3, 1], colour, [scaledPt], [frame]])
                    endFrame = autoKeyFrame(len(cPoints)-1)
                    colourFrames(frame,endFrame-1)

                elif currentTool == "fill":
                    f = frame
                    for i in range(50):
                        contours[cntIndex][1] = colour
                        filepath = folderName + "/frame%d.svg" % f
                        cntModify(filepath, contours)

                        f += 1
                        print(f)
                        oldCnt = contours[cntIndex][0]
                        readContours(f, False)
                        simThresh = 0.25
                        bestSim = simThresh
                        for i, cnt in enumerate(contours):

                            sim = cv2.matchShapes(oldCnt, cnt[0], 3, 0.0)
                            print(sim)
                            if sim < bestSim:
                                bestSim = sim
                                cntIndex = i
                        if bestSim == simThresh:  # No contour was found and so there was no change in sim
                            break
                    showImage()

            else:
                sLastX = int(lastx / scale)
                sLastY = int(lasty / scale)
                if currentTool == "rectangle":
                    # appending a rectangle to the svg
                    canvas.itemconfig(rectangle, fill=colour, outline='#ff0000')
                    rectCoords = np.divide(np.array(
                        [[sLastX, sLastY], [int(scaledPt[0]), sLastY], [int(scaledPt[0]), int(scaledPt[1])],
                         [sLastX, int(scaledPt[1])], [sLastX, sLastY]]),
                        scale)
                    contours.append([rectCoords, colour])
                    filepath = folderName + "/frame%d.svg" % frame
                    cntModify(filepath, contours)
                if currentTool == "cRect":
                    # appending a cRect to the cPoints list
                    cPoints.append(
                        [[4, 1], colour, [[sLastX, sLastY, int(scaledPt[0]), int(scaledPt[1])]],
                         [frame]])
                    canvas.delete(rectangle)
                    createShape(colour, (lastx, lasty, point[0], point[1]), [len(cPoints) - 1, 0], (1, 1))
                if currentTool == "mouth":
                    # appending a cRect to the cPoints list
                    cPoints.append(
                        [[5, 1], colour, [[sLastX, sLastY, int(scaledPt[0]), int(scaledPt[1])]],
                         [frame]])
                    canvas.delete(rectangle)
                    createShape(colour, (lastx, lasty, point[0], point[1]), [len(cPoints) - 1, 0], (1, 1))
                mouseMoved = False
        elif currentTool == "rectangle" or currentTool == "cRect" or currentTool == "mouth":
            canvas.delete(rectangle)
            mouseMoved = False


def canvasClick(event):
    global rectangle
    if currentTool == "rectangle" or currentTool == "cRect" or currentTool == "mouth":
        rectangle = canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1)
        mouseDown(event)


def addEndPoint(index):
    global cPoints
    cPoints[index][-1].append(frame)
    cPoints[index][0][1] = 2
    showImage()

def changeEndPoint(index):
    global cPoints
    pIndex = cPoints[index][-1].index(frame)+1
    cPoints[index][2]=cPoints[index][2][:pIndex]
    cPoints[index][-1] = cPoints[index][-1][:pIndex]


def addEndPointMult():
    global cPoints
    for i, cPoint in enumerate(cPoints):
        if cPoint[-1][0] < frame and cPoint[0][1] == 1 and cPoint[0][0] != 1:
            cPoint[-1].append(frame)
            cPoint[0][1] = 2
    showImage()


def cPointsWrite(folder):
    root = ET.Element("Colour-points")
    for cPoint in cPoints:
        frames = ' '.join(map(str, cPoint[-1]))
        types = ' '.join(map(str, cPoint[0]))
        subRoot = ET.SubElement(root, "cPoint", types=types, colour=cPoint[1], frames=frames)
        for p in cPoint[2]:
            if p:
                pt = ' '.join(map(lambda p: str(int(p)), p))
                ET.SubElement(subRoot, "point").text = pt

    tree = ET.ElementTree(root)
    tree.write(folder + "/colour_points.xml")


def str2list(str):
    return [int(x) for x in str.split()]


def cPointsRead():
    global cPoints
    global cPointsOld
    cPoints = []
    tree = ET.parse(folderName + "/colour_points.xml")
    for cPoint in tree.iterfind("//cPoint"):
        types = str2list(cPoint.get("types"))
        colour = cPoint.get("colour")
        points = []
        for point in cPoint:
            points.append(str2list(point.text))
        frames = str2list(cPoint.get("frames"))
        cPoints.append([types, colour, points, frames])

    cPointsOld = cPoints


def CF_PU_reciever(popup):
    cPointsWrite(folderName)
    print(popup)
    sFrame = int(popup[0].get())
    eFrame = int(popup[1].get())
    popup[2].destroy()
    colourFrames(sFrame,eFrame)


def colourFrames(sFrame,eFrame):
    global cPoints
    global cPointsOld

    cPointsCopy = cPoints
    frameCPoints = [[] for _ in range(numFrames)]
    mouthColours = ["#000000","#ffffff","#b72c1f"]
    for cPoint in cPointsCopy:
        frames = cPoint[-1]
        if sFrame <= frames[0] <= eFrame or sFrame <= frames[-1] <= eFrame or (sFrame >= frames[0] and eFrame<= frames[-1]):
            subType = cPoint[0][1]
            type = cPoint[0][0]
            point1 = cPoint[2][0]

            if type == 3:
                if subType == 3:
                    points = cPoint[2]
                    for i, frame in enumerate(frames):
                        value = (cPoint[1], points[i][0], points[i][1])
                        frameCPoints[frame].append(value)
                elif subType == 2:
                    for i in range(frames[0], frames[1] + 1):
                        value = (cPoint[1], point1[0], point1[1])
                        frameCPoints[i].append(value)
            if type == 1:
                value = (cPoint[1], point1[0], point1[1])
                frameCPoints[frames[0]].append(value)

            if type == 4 and subType == 2:
                for i in range(frames[0], frames[1] + 1):
                    readContours(i, False)
                    for cntIndex, cnt in enumerate(contours):
                        x, y, w, h = cv2.boundingRect(cnt[0])
                        if point1[0] < x and point1[1] < y and point1[2] > x + w and point1[3] > y + h:
                            contours[cntIndex][1] = cPoint[1]

                    filepath = folderName + "/frame%d.svg" % i
                    cntModify(filepath, contours)
            if type == 5 and subType == 2:
                largestArea = 0
                for i in range(frames[0], frames[1] + 1):
                    readContours(i, False)
                    mouthParts = []
                    for cntIndex, cnt in enumerate(contours):
                        x, y, w, h = cv2.boundingRect(cnt[0])
                        area = cv2.contourArea(cnt[0])
                        if point1[0] < x and point1[1] < y and point1[2] > x + w and point1[3] > y + h:
                            mouthParts.append([cntIndex,area])
                    if len(mouthParts) == 0:
                        continue
                    mouthParts.sort(key=lambda x:x[1],reverse=True)
                    if mouthParts[0][1] > largestArea:
                        largestArea = mouthParts[0][1]

                    length = len(mouthParts) if len(mouthParts) <=3 else 3
                    for mouthIndex in range(length):
                        cntIndex = mouthParts[mouthIndex][0]
                        colour = mouthColours[mouthIndex]
                        area = mouthParts[mouthIndex][1]
                        #print(i,area,largestArea,mouthIndex)
                        if mouthIndex == 0 and area<largestArea/3.5:
                            colour = mouthColours[1]

                        if mouthIndex == 1 and length == 2:
                            if mouthParts[0][1]>area*13 or mouthParts[0][1]<largestArea/2.5:
                                colour = mouthColours[2]


                        contours[cntIndex][1] = colour

                    filepath = folderName + "/frame%d.svg" % i
                    cntModify(filepath, contours)
    for i, fPoints in enumerate(frameCPoints[sFrame:eFrame + 1]):
        frameNum = sFrame + i
        if len(fPoints) > 0:  # WHATZZZZUPPPPPPBEEEEEEEE
            readContours(frameNum, False)
            for fPoint in fPoints:
                cntIndex = closestCnt(fPoint[-2:])
                contours[cntIndex][1] = fPoint[0]
            filepath = folderName + "/frame%d.svg" % frameNum
            cntModify(filepath, contours)
    showImage()
    cPointsOld = cPoints


def clearFramesCmd(s, e, rst):
    sFrame = int(s.get())
    eFrame = int(e.get())
    rst.destroy()
    result = messagebox.askyesno("Reset All", "Are you sure?\nThere is no way to undo this", icon='warning')
    if result:
        global cPoints
        cPoints = list(
            filter(lambda x: not sFrame <= x[-1][0] <= eFrame, cPoints))  # removes cPoints outside of frame range
        cPointsWrite(folderName)
        for i in range(sFrame, eFrame + 1):
            filepath = folderName + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)
        showImage()


def clearCPoints():
    # create reset popup

    rst = Toplevel(master=root, padx=50, pady=10)
    rst.title = "Choose frames"

    Message(rst, text="choose the start and end frame to delete from", width=300).pack()
    start = Entry(rst, width=50)
    start.pack()
    end = Entry(rst, width=50)
    end.pack()
    Button(rst, text="Clear Frames", command=lambda s=start, e=end, rst=rst: clearFramesCmd(s, e, rst)).pack()


def traceVideoPU():
    popup = Toplevel(master=root, padx=50, pady=10)
    popup.title = "Choose frames"

    Message(popup, text="Choose the start and end frame to trace from.\n(Leave form blank to convert entire video)",
            width=300).pack()
    start = Entry(popup, width=50)
    start.pack()
    start.insert(0,str(frame))
    end = Entry(popup, width=50)
    end.pack()

    scanType = StringVar()
    scanType.set("single")
    elements = [start, end, popup, scanType]

    Radiobutton(popup, text="Single Scan", variable=scanType, value="single", command=lambda option = "single", pu = popup, e = elements: changeTracePU(option,pu,e)).pack(anchor=W)
    Radiobutton(popup, text="Multiple scans", variable=scanType, value="mult",command=lambda option = "mult", pu = popup, e = elements: changeTracePU(option,pu,e)).pack(anchor=W)

def changeTracePU(type, popup, elements):
    global traceOption, traceOptions
    try:
        traceOptions.pack_forget()
    except:
        pass
    traceOptions = Frame(popup)
    traceOptions.pack()
    if type == "single":
        Message(traceOptions, text="Min Threshold value",width=300).pack()
        traceOption = Entry(traceOptions, width=10)
        traceOption.pack()
        traceOption.insert(0, "150")
        elements.append(traceOption)

    elif type == "mult":
        Message(traceOptions, text="Number of scans", width=300).pack()
        traceOption = Entry(traceOptions, width=5)
        traceOption.pack()
        traceOption.insert(0, "7")

        Message(traceOptions, text="Offset of initial scan", width=300).pack()
        traceOption2 = Entry(traceOptions, width=8)
        traceOption2.pack()
        traceOption2.insert(0, "12")

        Message(traceOptions, text="Offset of final scan", width=300).pack()
        traceOption3 = Entry(traceOptions, width=8)
        traceOption3.pack()
        traceOption3.insert(0, "15")
        elements.append([traceOption,traceOption2,traceOption3])


    Button(traceOptions, text="Trace Video", command=lambda popup=elements: convertVideo(popup)).pack()


def svg2VidPU():
    popup = Toplevel(master=root, padx=50, pady=10)
    popup.title = "Choose frames"

    Message(popup, text="Choose the start and end frame to convert from.\n(Leave form blank to convert entire video)",
            width=300).pack()
    start = Entry(popup, width=25)
    start.pack()
    end = Entry(popup, width=25)
    end.pack()
    Message(popup, text="Video title:", width=200).pack()
    title = Entry(popup, width=25)
    title.pack()
    var = IntVar()
    Checkbutton(popup, text="Skip converting svg to png", variable=var).pack()
    elements = [start, end, title, var, popup]
    Button(popup, text="Convert Video", command=lambda popup=elements: svgMult2Vid(popup)).pack()


def colourFramesPU():
    popup = Toplevel(master=root, padx=50, pady=10)
    popup.title = "Choose frames"

    Message(popup, text="Choose the start and end frame to colour from.", width=300).pack()
    start = Entry(popup, width=50)
    start.pack()
    end = Entry(popup, width=50)
    end.pack()
    elements = [start, end, popup]
    Button(popup, text="Colour Frames", command=lambda popup=elements: CF_PU_reciever(popup)).pack()


def changeTool(icon):
    global currentTool
    currentTool = icon
    print(icon)


def onClosing():
    cPointsWrite(folderName)
    root.destroy()

class HoverButton(Button):

    def __init__(self, master, **kw):
        Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.clicked = False
        self.bind("<Button-1>", self.on_click)
        # self.bind("<Enter>", self.on_enter)
        # self.bind("<Leave>", self.on_leave)

    def on_click(self, e):
        self.clicked = True
        for button in toolbarButts:
            button.configure(bg='#F0F0F0')
        self['background'] = self['activebackground']

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        if not self.clicked:
            print(self.clicked)
            self['background'] = self.defaultBackground


# setup variables
currentTool = 0
dc = windll.user32.GetDC(0)
rootDir = "C:/Users/Joe/Documents/Asdf11/"
vidfillDir = "C:/Users/Joe/Documents/VidFill/"
folderNum = int(max(glob.glob(rootDir + "frames_??"))[-2:])
folderName = rootDir + "frames_" + str(folderNum).zfill(2)
folderNameNew = rootDir + "frames_" + str(folderNum + 1).zfill(2)
kernel = np.ones((3, 3), np.uint8)
kernel2 = np.ones((11, 11), np.uint8)
kernel3 = np.ones((1, 1), np.uint8)

root = Tk()
s_width = root.winfo_screenwidth()
s_height = root.winfo_screenheight()
s_pad = 200
contours = []
cPoints = []
cPointsOld = []
frame = 1
lastx = 0
lasty = 0
mouseMoved = False

vidFilepath = rootDir + "asdfmovie11.mp4"
vidCap = cv2.VideoCapture(vidFilepath)
vidW = vidCap.get(cv2.CAP_PROP_FRAME_WIDTH)
vidH = vidCap.get(cv2.CAP_PROP_FRAME_HEIGHT)
frameRatio = vidCap.get(cv2.CAP_PROP_FPS) / (1 / 0.067)
numFrames = int(vidCap.get(cv2.CAP_PROP_FRAME_COUNT) / frameRatio)
scale = (s_height - s_pad) / vidH

# create menu
menubar = Menu(root)
menubar.add_command(label="Save", command=lambda folder=folderName: cPointsWrite(folderName))
menubar.add_command(label="Colour frames", command=colourFramesPU)
menubar.add_command(label="Clear frames", command=clearCPoints)
menubar.add_command(label="Trace video", command=traceVideoPU)
menubar.add_command(label="Convert to video", command=svg2VidPU)
menubar.add_command(label="Set static EndPoints to visible", command=addEndPointMult)
menubar.add_command(label="Print cPoints", command=lambda: print(cPoints))

# create toolbar
toolbar = Frame(root)
icons = ["cPointAuto", "cPoint", "cPointStatic", "cRect", "fill", "mouth", "rectangle"]
toolbarButts = []

for icon in icons:
    iconImg = PhotoImage(master=toolbar, file= vidfillDir + icon + ".png")
    button = HoverButton(toolbar, image=iconImg, activebackground='#42cef4', command=lambda icon=icon: changeTool(icon))
    toolbarButts.append(button)
    button.image = iconImg
    button.pack(pady=5, padx=2)
toolbar.pack(side=LEFT)
# create canvas

canvas = Canvas(root, width=s_width - s_pad / 1.5, height=s_height - s_pad)
canvas.pack(anchor='s', pady=20)
root.bind("<r>", lambda event: root.focus_set())

# show start image
cPointsRead()
showImage()

# create buttons
timeline = Frame(root, takefocus = 0)
lArrowImg = PhotoImage(file=vidfillDir + "lArrow.png")
rArrowImg = PhotoImage(file=vidfillDir + "rArrow.png")
Button(timeline, image=lArrowImg, command=prevImage).pack(side=LEFT)
entry = Entry(timeline, justify='center', takefocus = 0)
entry.bind("<Return>", goToFrame)
entry.pack(side=LEFT, padx=10)
Button(timeline, image=rArrowImg, command=nextImage).pack(side=LEFT)
timeline.pack(pady=5)
root.bind('<Left>', lambda event: prevImage())
root.bind('<Right>', lambda event: nextImage())

dialogRoot = Toplevel()
dialogRoot .geometry("%dx%d%+d%+d" % (50, 50, s_width/2-300, s_height/2-200))
dialogRoot .withdraw()

# start mainloop
root.config(menu=menubar)
root.protocol("WM_DELETE_WINDOW", onClosing)
root.mainloop()
