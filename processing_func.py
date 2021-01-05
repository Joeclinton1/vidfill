from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import os


def svgMult2Vid(popup):
    sFrame = int(popup[0].get())
    eFrame = int(popup[1].get())
    title = popup[2].get()
    convert2Png = popup[3].get()
    popup[4].destroy()
    outVidName = self.rootDir + title + ".mp4"
    if sFrame >= 1 and eFrame <= self.numFrames:
        if convert2Png != 1:
            for i in range(sFrame, eFrame + 1):
                drawing = svg2rlg(self.folderName + "/frame%d.svg" % i)
                renderPM.drawToFile(drawing, self.folderName + "/frame%d.png" % i, fmt="PNG")
        images = {}
        for img in os.listdir(self.folderName):
            if img.endswith(".png"):
                fileNum = int(re.sub("[^0-9]", "", img))
                if sFrame <= fileNum <= eFrame:
                    images[fileNum] = img

        fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
        video = cv2.VideoWriter(outVidName, fourcc, 15, (int(self.vidW), int(self.vidH)), True)
        for key, image in sorted(images.items()):
            video.write(cv2.imread(os.path.join(self.folderName, image)))

        cv2.destroyAllWindows()
        video.release()


def colourFrames(sFrame, eFrame):
    for i, fPoints in enumerate(frameCPoints[sFrame:eFrame + 1]):
        frameNum = sFrame + i
        if len(fPoints) > 0:  # WHATZZZZUPPPPPPBEEEEEEEE
            self.read(frameNum, False)
            for fPoint in fPoints:
                cntIndex = self.find_closest(fPoint[-2:])
                self.contours[cntIndex][1] = fPoint[0]
            filepath = self.folderName + "/frame%d.svg" % frameNum
            self.modify(filepath, self.contours)
    self.showImage()
    cPointsOld = cPoints
