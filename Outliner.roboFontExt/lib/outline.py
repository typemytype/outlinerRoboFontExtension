from vanilla import *
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController

from fontTools.pens.cocoaPen import CocoaPen

from lib.tools.bezierTools import curveConverter, roundValue

from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from mojo.roboFont import OpenWindow, version, CurrentGlyph, CurrentFont
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor

from .outlinePen import OutlinePen

outlinePaletteDefaultKey = "com.typemytype.outliner"


class OutlinerPalette(BaseWindowController):

    def __init__(self):
        self.w = FloatingWindow((300, 535), "Outline Palette")

        y = 5
        middle = 135
        textMiddle = middle - 27
        y += 10
        self.w._tickness = TextBox((0, y - 3, textMiddle, 17), 'Thickness:', alignment="right")

        ticknessValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "thickness"), 10)

        self.w.tickness = Slider((middle, y, -50, 15),
                                 minValue=1,
                                 maxValue=200,
                                 callback=self.parametersChanged,
                                 value=ticknessValue)
        self.w.ticknessText = EditText((-40, y, -10, 17), ticknessValue,
                                       callback=self.parametersTextChanged,
                                       sizeStyle="small")
        y += 33
        self.w._contrast = TextBox((0, y - 3, textMiddle, 17), 'Contrast:', alignment="right")

        contrastValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "contrast"), 0)

        self.w.contrast = Slider((middle, y, -50, 15),
                                 minValue=0,
                                 maxValue=200,
                                 callback=self.parametersChanged,
                                 value=contrastValue)
        self.w.contrastText = EditText((-40, y, -10, 17), contrastValue,
                                       callback=self.parametersTextChanged,
                                       sizeStyle="small")
        y += 33
        self.w._contrastAngle = TextBox((0, y - 3, textMiddle, 17), 'Contrast Angle:', alignment="right")

        contrastAngleValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "contrastAngle"), 0)

        self.w.contrastAngle = Slider((middle, y - 10, 30, 30),
                                 minValue=0,
                                 maxValue=360,
                                 callback=self.contrastAngleCallback,
                                 value=contrastValue)
        self.w.contrastAngle.getNSSlider().cell().setSliderType_(NSCircularSlider)
        self.w.contrastAngleText = EditText((-40, y, -10, 17), contrastAngleValue,
                                       callback=self.parametersTextChanged,
                                       sizeStyle="small")

        y += 33

        self.w._miterLimit = TextBox((0, y - 3, textMiddle, 17), 'MiterLimit:', alignment="right")

        connectmiterLimitValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "connectmiterLimit"), True)

        self.w.connectmiterLimit = CheckBox((middle-22, y - 3, 20, 17), "",
                                             callback=self.connectmiterLimit,
                                             value=connectmiterLimitValue)

        miterLimitValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "miterLimit"), 10)

        self.w.miterLimit = Slider((middle, y, -50, 15),
                                    minValue=1,
                                    maxValue=200,
                                    callback=self.parametersChanged,
                                    value=miterLimitValue)
        self.w.miterLimitText = EditText((-40, y, -10, 17), miterLimitValue,
                                          callback=self.parametersTextChanged,
                                          sizeStyle="small")

        self.w.miterLimit.enable(not connectmiterLimitValue)
        self.w.miterLimitText.enable(not connectmiterLimitValue)

        y += 30

        cornerAndCap = ["Square", "Round", "Butt"]

        self.w._corner = TextBox((0, y, textMiddle, 17), 'Corner:', alignment="right")
        self.w.corner = PopUpButton((middle - 2, y - 2, -48, 22), cornerAndCap, callback=self.parametersTextChanged)

        y += 30

        self.w._cap = TextBox((0, y, textMiddle, 17), 'Cap:', alignment="right")
        useCapValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "closeOpenPath"), False)
        self.w.useCap = CheckBox((middle - 22, y, 20, 17), "",
                                             callback=self.useCapCallback,
                                             value=useCapValue)
        self.w.cap = PopUpButton((middle - 2, y - 2, -48, 22), cornerAndCap, callback=self.parametersTextChanged)
        self.w.cap.enable(useCapValue)

        cornerValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "corner"), "Square")
        if cornerValue in cornerAndCap:
            self.w.corner.set(cornerAndCap.index(cornerValue))

        capValue = getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "cap"), "Square")
        if capValue in cornerAndCap:
            self.w.cap.set(cornerAndCap.index(capValue))

        y += 33

        self.w.keepBounds = CheckBox((middle - 3, y, middle, 22), "Keep Bounds",
                                   value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "keepBounds"), False),
                                   callback=self.parametersTextChanged)
        y += 30
        self.w.optimizeCurve = CheckBox((middle - 3, y, middle, 22), "Optimize Curve",
                                   value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "optimizeCurve"), False),
                                   callback=self.parametersTextChanged)
        y += 30
        self.w.addOriginal = CheckBox((middle - 3, y, middle, 22), "Add Source",
                                   value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addOriginal"), False),
                                   callback=self.parametersTextChanged)
        y += 30
        self.w.addInner = CheckBox((middle - 3, y, middle, 22), "Add Left",
                                   value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addLeft"), True),
                                   callback=self.parametersTextChanged)
        y += 30
        self.w.addOuter = CheckBox((middle - 3, y, middle, 22), "Add Right",
                                   value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addRight"), True),
                                   callback=self.parametersTextChanged)

        y += 35

        self.w.preview = CheckBox((middle - 3, y, middle, 22), "Preview",
                               value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "preview"), True),
                               callback=self.previewCallback)
        y += 30
        self.w.fill = CheckBox((middle - 3 + 10, y, middle, 22), "Fill",
                               value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "fill"), False),
                               callback=self.fillCallback, sizeStyle="small")
        y += 25
        self.w.stroke = CheckBox((middle - 3 + 10, y, middle, 22), "Stroke",
                               value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "stroke"), True),
                               callback=self.strokeCallback, sizeStyle="small")

        color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 1, 1, .8)

        self.w.color = ColorWell(((middle - 5) * 1.7, y - 33, -10, 60),
                                 color=getExtensionDefaultColor("%s.%s" % (outlinePaletteDefaultKey, "color"), color),
                                 callback=self.colorCallback)

        self.previewCallback(self.w.preview)

        b = -80
        self.w.apply = Button((-70, b, -10, 22), "Expand", self.expand, sizeStyle="small")
        self.w.applyNewFont = Button((-190, b, -80, 22), "Expand Selection", self.expandSelection, sizeStyle="small")
        self.w.applySelection = Button((-290, b, -200, 22), "Expand Font", self.expandFont, sizeStyle="small")

        b += 30
        self.w.preserveComponents = CheckBox((10, b, -10, 22), "Preserve Components", sizeStyle="small",
                                value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "preserveComponents"), False),
                                callback=self.parametersTextChanged)
        b += 25
        self.w.filterDoubles = CheckBox((10, b, -10, 22), "Filter Double points", sizeStyle="small",
                                value=getExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "filterDoubles"), True),
                                callback=self.parametersTextChanged)
        self.setUpBaseWindowBehavior()

        addObserver(self, "drawOutline", "drawBackground")
        self.parametersTextChanged
        self.w.open()

    def windowCloseCallback(self, sender):
        removeObserver(self, "drawBackground")
        self.updateView()
        super(OutlinerPalette, self).windowCloseCallback(sender)

    def drawOutline(self, info):
        if not self.w.preview.get():
            return
        outline = self.calculate(glyph=info["glyph"].naked())
        pen = CocoaPen(None)
        outline.draw(pen)

        self.w.color.get().set()
        if self.w.fill.get():
            pen.path.fill()

        if self.w.stroke.get():
            pen.path.setLineWidth_(info["scale"])
            pen.path.stroke()

    def calculate(self, glyph, preserveComponents=False):
        tickness = self.w.tickness.get()
        contrast = self.w.contrast.get()
        contrastAngle = self.w.contrastAngle.get()
        keepBounds = self.w.keepBounds.get()
        optimizeCurve = self.w.optimizeCurve.get()
        filterDoubles = self.w.filterDoubles.get()
        if self.w.connectmiterLimit.get():
            miterLimit = None
        else:
            miterLimit = self.w.miterLimit.get()

        corner = self.w.corner.getItems()[self.w.corner.get()]
        cap = self.w.cap.getItems()[self.w.cap.get()]

        closeOpenPaths = self.w.useCap.get()

        drawOriginal = self.w.addOriginal.get()
        drawInner = self.w.addInner.get()
        drawOuter = self.w.addOuter.get()

        pen = OutlinePen(glyph.getParent(),
                            tickness,
                            contrast,
                            contrastAngle,
                            connection=corner,
                            cap=cap,
                            miterLimit=miterLimit,
                            closeOpenPaths=closeOpenPaths,
                            optimizeCurve=optimizeCurve,
                            preserveComponents=preserveComponents,
                            filterDoubles=filterDoubles)

        glyph.draw(pen)

        pen.drawSettings(drawOriginal=drawOriginal,
                         drawInner=drawInner,
                         drawOuter=drawOuter)

        result = pen.getGlyph()
        if keepBounds:
            if glyph.bounds and result.bounds:
                minx1, miny1, maxx1, maxy1 = glyph.bounds
                minx2, miny2, maxx2, maxy2 = result.bounds

                h1 = maxy1 - miny1

                w2 = maxx2 - minx2
                h2 = maxy2 - miny2

                s = h1 / h2

                center = minx2 + w2 * .5, miny2 + h2 * .5

                dummy = RGlyph(result)

                # RF3
                if version >= "3.0":
                    dummy.scaleBy((s, s), center)
                # RF1
                else:
                    dummy.scale((s, s), center)

        return result

    def connectmiterLimit(self, sender):
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "connectmiterLimit"), sender.get())
        value = not sender.get()
        self.w.miterLimit.enable(value)
        self.w.miterLimitText.enable(value)
        self.parametersChanged(sender)

    def useCapCallback(self, sender):
        value = sender.get()
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "closeOpenPath"), value)
        self.w.cap.enable(value)
        self.parametersChanged(sender)

    def contrastAngleCallback(self, sender):
        if NSEvent.modifierFlags() & NSShiftKeyMask:
            value = sender.get()
            value = roundValue(value, 45)
            sender.set(value)
        self.parametersChanged(sender)

    def parametersTextChanged(self, sender):
        value = sender.get()
        try:
            value = int(float(value))
        except ValueError:
            value = 10
            sender.set(value)

        tickness = int(self.w.ticknessText.get())
        self.w.tickness.set(tickness)
        contrast = int(self.w.contrastText.get())
        self.w.contrast.set(contrast)
        contrastAngle = int(self.w.contrastAngleText.get())
        self.w.contrastAngle.set(contrastAngle)
        self.parametersChanged(sender)

    def parametersChanged(self, sender=None, glyph=None):
        tickness = int(self.w.tickness.get())
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "thickness"), tickness)
        contrast = int(self.w.contrast.get())
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "contrast"), contrast)
        contrastAngle = int(self.w.contrastAngle.get())
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "contrastAngle"), contrastAngle)
        keepBounds = self.w.keepBounds.get()
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "keepBounds"), keepBounds)
        preserveComponents = bool(self.w.preserveComponents.get())
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "preserveComponents"), preserveComponents)
        filterDoubles = bool(self.w.filterDoubles.get())
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "filterDoubles"), filterDoubles)

        miterLimit = int(self.w.miterLimit.get())
        if self.w.connectmiterLimit.get():
            miterLimit = tickness
            self.w.miterLimit.set(miterLimit)
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "miterLimit"), miterLimit)

        corner = self.w.corner.getItems()[self.w.corner.get()]
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "corner"), corner )

        cap = self.w.cap.getItems()[self.w.cap.get()]
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "cap"), cap )

        drawOriginal = self.w.addOriginal.get()
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addOriginal"), drawOriginal)

        drawInner = self.w.addInner.get()
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addLeft"), drawInner)

        drawOuter = self.w.addOuter.get()
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "addRight"), drawOuter)

        self.w.ticknessText.set("%i" % tickness)
        self.w.contrastText.set("%i" % contrast)
        self.w.contrastAngleText.set("%i" % contrastAngle)
        self.w.miterLimitText.set("%i" % miterLimit)
        self.updateView()

    def previewCallback(self, sender):
        value = sender.get()
        self.w.fill.enable(value)
        self.w.stroke.enable(value)
        self.w.color.enable(value)
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "preview"), value)
        self.updateView()

    def colorCallback(self, sender):
        setExtensionDefaultColor("%s.%s" % (outlinePaletteDefaultKey, "color"), sender.get())
        self.updateView()

    def fillCallback(self, sender):
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "fill"), sender.get()),
        self.updateView()

    def strokeCallback(self, sender):
        setExtensionDefault("%s.%s" % (outlinePaletteDefaultKey, "stroke"), sender.get()),
        self.updateView()

    def updateView(self, sender=None):
        UpdateCurrentGlyphView()

    def expand(self, sender):
        glyph = CurrentGlyph()
        preserveComponents = bool(self.w.preserveComponents.get())
        self.expandGlyph(glyph, preserveComponents)
        self.w.preview.set(False)
        self.previewCallback(self.w.preview)

    def expandGlyph(self, glyph, preserveComponents=True):
        defconGlyph = glyph.naked()

        glyph.prepareUndo("Outline")

        isQuad = curveConverter.isQuadratic(defconGlyph)

        if isQuad:
            curveConverter.quadratic2bezier(defconGlyph)

        outline = self.calculate(defconGlyph, preserveComponents)

        glyph.clearContours()
        outline.drawPoints(glyph.getPointPen())

        if isQuad:
            curveConverter.bezier2quadratic(defconGlyph)

        glyph.round()
        glyph.performUndo()

    def expandSelection(self, sender):
        font = CurrentFont()
        preserveComponents = bool(self.w.preserveComponents.get())
        selection = font.selection
        for glyphName in selection:
            glyph = font[glyphName]
            self.expandGlyph(glyph, preserveComponents)

    def expandFont(self, sender):
        font = CurrentFont()
        preserveComponents = bool(self.w.preserveComponents.get())
        for glyph in font:
            self.expandGlyph(glyph, preserveComponents)


OpenWindow(OutlinerPalette)
