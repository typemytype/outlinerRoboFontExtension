import vanilla
import AppKit

from lib.tools.bezierTools import roundValue

from mojo.roboFont import OpenWindow, CurrentGlyph, CurrentFont
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor, NSColorToRgba
from mojo.subscriber import WindowController, Subscriber, registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber
from mojo.events import postEvent

from outlinePen import OutlinePen


outlinePaletteDefaultKey = "com.typemytype.outliner"


def calculate(glyph, options, preserveComponents=None):
    if preserveComponents is not None:
        options["preserveComponents"] = preserveComponents

    pen = OutlinePen(
        glyph.layer,
        offset=options["offset"],
        contrast=options["contrast"],
        contrastAngle=options["contrastAngle"],
        connection=options["connection"],
        cap=options["cap"],
        miterLimit=options["miterLimit"],
        closeOpenPaths=options["closeOpenPaths"],
        optimizeCurve=options["optimizeCurve"],
        preserveComponents=options["preserveComponents"],
        filterDoubles=options["filterDoubles"]
    )

    glyph.draw(pen)

    pen.drawSettings(
        drawOriginal=options["addOriginal"],
        drawInner=options["addInner"],
        drawOuter=options["addOuter"]
    )

    result = pen.getGlyph()
    if options["keepBounds"]:
        if glyph.bounds and result.bounds:
            minx1, miny1, maxx1, maxy1 = glyph.bounds
            minx2, miny2, maxx2, maxy2 = result.bounds

            h1 = maxy1 - miny1

            w2 = maxx2 - minx2
            h2 = maxy2 - miny2

            scale = h1 / h2
            center = minx2 + w2 * .5, miny2 + h2 * .5

            wrapped = RGlyph(result)
            wrapped.scaleBy((scale, scale), center)

    return result


class OutlinerGlyphEditor(Subscriber):

    # debug = True

    controller = None

    def build(self):
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer(outlinePaletteDefaultKey)
        self.path = container.appendPathSublayer()
        self.updateDisplay()
        self.updateOutline()

    def destroy(self):
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer(outlinePaletteDefaultKey)
        container.clearSublayers()

    def outlinerDidChange(self, info):
        self.updateOutline()

    def outlinerDisplayDidChanged(self, info):
        self.updateDisplay()

    def glyphEditorGlyphDidChangeOutline(self, info):
        self.updateOutline(info["glyph"])

    def updateDisplay(self):
        if self.controller:
            displayOptions = self.controller.getDisplayOptions()
            r, g, b, a = displayOptions["color"]
            self.path.setVisible(displayOptions["preview"])
            with self.path.propertyGroup():
                if displayOptions["shouldFill"]:
                    self.path.setFillColor((r, g, b, a))
                else:
                    self.path.setFillColor(None)

                if displayOptions["shouldStroke"]:
                    self.path.setStrokeWidth(1)
                    self.path.setStrokeColor((r, g, b, 1))
                else:
                    self.path.setStrokeWidth(0)
                    self.path.setStrokeColor(None)

    def updateOutline(self, glyph=None):
        if glyph is None:
            glyph = self.getGlyphEditor().getGlyph()

        if self.controller:
            result = calculate(
                glyph=glyph,
                options=self.controller.getOptions()
            )
            self.path.setPath(result.getRepresentation("merz.CGPath"))
        else:
            self.path.setPath(None)


class OutlinerPalette(WindowController):

    # debug = True

    def build(self):
        self.w = vanilla.FloatingWindow((300, 535), "Outline Palette")

        y = 5
        middle = 135
        textMiddle = middle - 27
        y += 10
        self.w._tickness = vanilla.TextBox((0, y - 3, textMiddle, 17), 'Thickness:', alignment="right")

        ticknessValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.offset", 10)

        self.w.tickness = vanilla.Slider(
            (middle, y, -50, 15),
            minValue=1,
            maxValue=200,
            callback=self.parametersChanged,
            value=ticknessValue
        )
        self.w.ticknessText = vanilla.EditText(
            (-40, y, -10, 17),
            ticknessValue,
            callback=self.parametersTextChanged,
            sizeStyle="small"
        )
        y += 33
        self.w._contrast = vanilla.TextBox((0, y - 3, textMiddle, 17), 'Contrast:', alignment="right")

        contrastValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.contrast", 0)

        self.w.contrast = vanilla.Slider(
            (middle, y, -50, 15),
            minValue=0,
            maxValue=200,
            callback=self.parametersChanged,
            value=contrastValue
        )
        self.w.contrastText = vanilla.EditText(
            (-40, y, -10, 17),
            contrastValue,
            callback=self.parametersTextChanged,
            sizeStyle="small"
        )
        y += 33
        self.w._contrastAngle = vanilla.TextBox((0, y - 3, textMiddle, 17), 'Contrast Angle:', alignment="right")

        contrastAngleValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.contrastAngle", 0)

        self.w.contrastAngle = vanilla.Slider(
            (middle, y - 10, 30, 30),
            minValue=0,
            maxValue=360,
            callback=self.contrastAngleCallback,
            value=contrastAngleValue
        )
        self.w.contrastAngle.getNSSlider().cell().setSliderType_(AppKit.NSCircularSlider)

        self.w.contrastAngleText = vanilla.EditText(
            (-40, y, -10, 17),
            contrastAngleValue,
            callback=self.parametersTextChanged,
            sizeStyle="small"
        )

        y += 33

        self.w._miterLimit = vanilla.TextBox((0, y - 3, textMiddle, 17), 'MiterLimit:', alignment="right")

        connectmiterLimitValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.connectmiterLimit", True)

        self.w.connectmiterLimit = vanilla.CheckBox(
            (middle-22, y - 3, 20, 17),
            "",
            callback=self.connectmiterLimit,
            value=connectmiterLimitValue
        )

        miterLimitValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.miterLimit", 10)

        self.w.miterLimit = vanilla.Slider(
            (middle, y, -50, 15),
            minValue=1,
            maxValue=200,
            callback=self.parametersChanged,
            value=miterLimitValue
        )
        self.w.miterLimitText = vanilla.EditText(
            (-40, y, -10, 17),
            miterLimitValue,
            callback=self.parametersTextChanged,
            sizeStyle="small"
        )

        self.w.miterLimit.enable(not connectmiterLimitValue)
        self.w.miterLimitText.enable(not connectmiterLimitValue)

        y += 30

        cornerAndCap = ["Square", "Round", "Butt"]

        self.w._corner = vanilla.TextBox((0, y, textMiddle, 17), 'Corner:', alignment="right")
        self.w.corner = vanilla.PopUpButton((middle - 2, y - 2, -48, 22), cornerAndCap, callback=self.parametersTextChanged)

        y += 30

        self.w._cap = vanilla.TextBox((0, y, textMiddle, 17), 'Cap:', alignment="right")
        useCapValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.closeOpenPath", False)
        self.w.useCap = vanilla.CheckBox(
            (middle - 22, y, 20, 17),
            "",
            callback=self.useCapCallback,
            value=useCapValue
        )
        self.w.cap = vanilla.PopUpButton((middle - 2, y - 2, -48, 22), cornerAndCap, callback=self.parametersTextChanged)
        self.w.cap.enable(useCapValue)

        cornerValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.corner", "Square")
        if cornerValue in cornerAndCap:
            self.w.corner.set(cornerAndCap.index(cornerValue))

        capValue = getExtensionDefault(f"{outlinePaletteDefaultKey}.cap", "Square")
        if capValue in cornerAndCap:
            self.w.cap.set(cornerAndCap.index(capValue))

        y += 33

        self.w.keepBounds = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Keep Bounds",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.keepBounds", False),
            callback=self.parametersTextChanged
        )
        y += 30
        self.w.optimizeCurve = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Optimize Curve",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.optimizeCurve", False),
            callback=self.parametersTextChanged
        )
        y += 30
        self.w.addOriginal = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Add Source",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.addOriginal", False),
            callback=self.parametersTextChanged
        )
        y += 30
        self.w.addInner = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Add Left",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.addInner", True),
            callback=self.parametersTextChanged
        )
        y += 30
        self.w.addOuter = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Add Right",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.addOuter", True),
            callback=self.parametersTextChanged
        )
        y += 35
        self.w.preview = vanilla.CheckBox(
            (middle - 3, y, middle, 22),
            "Preview",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.preview", True),
            callback=self.previewCallback
        )
        y += 30
        self.w.fill = vanilla.CheckBox(
            (middle - 3 + 10, y, middle, 22),
            "Fill",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.fill", False),
            callback=self.fillCallback, sizeStyle="small"
        )
        y += 25
        self.w.stroke = vanilla.CheckBox(
            (middle - 3 + 10, y, middle, 22),
            "Stroke",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.stroke", True),
            callback=self.strokeCallback, sizeStyle="small"
        )

        color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 1, 1, .8)

        self.w.color = vanilla.ColorWell(
            ((middle - 5) * 1.7, y - 33, -10, 60),
            color=getExtensionDefaultColor(f"{outlinePaletteDefaultKey}.color", color),
            callback=self.colorCallback
        )

        b = -80
        self.w.apply = vanilla.Button((-70, b, -10, 22), "Expand", self.expand, sizeStyle="small")
        self.w.applyNewFont = vanilla.Button((-190, b, -80, 22), "Expand Selection", self.expandSelection, sizeStyle="small")
        self.w.applySelection = vanilla.Button((-290, b, -200, 22), "Expand Font", self.expandFont, sizeStyle="small")

        b += 30
        self.w.preserveComponents = vanilla.CheckBox(
            (10, b, -10, 22),
            "Preserve Components",
            sizeStyle="small",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.preserveComponents", False),
            callback=self.parametersTextChanged
        )
        b += 25
        self.w.filterDoubles = vanilla.CheckBox(
            (10, b, -10, 22),
            "Filter Double points",
            sizeStyle="small",
            value=getExtensionDefault(f"{outlinePaletteDefaultKey}.filterDoubles", True),
            callback=self.parametersTextChanged
        )

        self.w.open()

    def started(self):
        OutlinerGlyphEditor.controller = self
        registerGlyphEditorSubscriber(OutlinerGlyphEditor)

    # def destroy(self):
    def windowWillClose(self, sender):
        unregisterGlyphEditorSubscriber(OutlinerGlyphEditor)
        OutlinerGlyphEditor.controller = None

    def getOptions(self):
        return dict(
            offset=int(self.w.tickness.get()),
            contrast=int(self.w.contrast.get()),
            contrastAngle=int(self.w.contrastAngle.get()),
            keepBounds=self.w.keepBounds.get(),
            preserveComponents=bool(self.w.preserveComponents.get()),
            filterDoubles=bool(self.w.filterDoubles.get()),
            connection=self.w.corner.getItems()[self.w.corner.get()],
            cap=self.w.cap.getItems()[self.w.cap.get()],
            closeOpenPaths=self.w.useCap.get(),
            miterLimit=int(self.w.miterLimit.get()),
            optimizeCurve=self.w.optimizeCurve.get(),
            addOriginal=self.w.addOriginal.get(),
            addInner=self.w.addInner.get(),
            addOuter=self.w.addOuter.get(),
        )

    def getDisplayOptions(self):
        return dict(
            preview=self.w.preview.get(),
            shouldFill=self.w.fill.get(),
            shouldStroke=self.w.stroke.get(),
            color=NSColorToRgba(self.w.color.get())
        )

    # control callbacks

    def connectmiterLimit(self, sender):
        setExtensionDefault(f"{outlinePaletteDefaultKey}.connectmiterLimit", sender.get())
        value = not sender.get()
        self.w.miterLimit.enable(value)
        self.w.miterLimitText.enable(value)
        self.parametersChanged()

    def useCapCallback(self, sender):
        value = sender.get()
        setExtensionDefault(f"{outlinePaletteDefaultKey}.closeOpenPath", value)
        self.w.cap.enable(value)
        self.parametersChanged()

    def contrastAngleCallback(self, sender):
        if AppKit.NSEvent.modifierFlags() & AppKit.NSShiftKeyMask:
            value = sender.get()
            value = roundValue(value, 45)
            sender.set(value)
        self.parametersChanged()

    def parametersTextChanged(self, sender):
        value = sender.get()
        try:
            value = int(float(value))
        except ValueError:
            value = 10
            sender.set(value)

        self.w.tickness.set(int(self.w.ticknessText.get()))
        self.w.contrast.set(int(self.w.contrastText.get()))
        self.w.contrastAngle.set(int(self.w.contrastAngleText.get()))
        self.parametersChanged()

    def parametersChanged(self, sender=None, glyph=None):
        options = self.getOptions()
        if self.w.connectmiterLimit.get():
            self.w.miterLimit.set(options["offset"])

        for key, value in options.items():
            setExtensionDefault(f"{outlinePaletteDefaultKey}.{key}", value)

        self.w.ticknessText.set(f"{options['offset']}")
        self.w.contrastText.set(f"{options['contrast']}")
        self.w.contrastAngleText.set(f"{options['contrastAngle']}")
        self.w.miterLimitText.set(f"{options['miterLimit']}")

        postEvent("com.typemytype.outliner.changed")

    def displayParametersChanged(self):
        postEvent("com.typemytype.outliner.displayChanged")

    def previewCallback(self, sender):
        value = sender.get()
        self.w.fill.enable(value)
        self.w.stroke.enable(value)
        self.w.color.enable(value)
        setExtensionDefault(f"{outlinePaletteDefaultKey}.preview", value)
        self.displayParametersChanged()

    def colorCallback(self, sender):
        setExtensionDefaultColor(f"{outlinePaletteDefaultKey}.color", sender.get())
        self.displayParametersChanged()

    def fillCallback(self, sender):
        setExtensionDefault(f"{outlinePaletteDefaultKey}.fill", sender.get()),
        self.displayParametersChanged()

    def strokeCallback(self, sender):
        setExtensionDefault(f"{outlinePaletteDefaultKey}.stroke", sender.get()),
        self.displayParametersChanged()

    # buttons callbacks

    def expand(self, sender):
        glyph = CurrentGlyph()
        preserveComponents = bool(self.w.preserveComponents.get())
        self.expandGlyph(glyph, preserveComponents)
        self.w.preview.set(False)
        self.previewCallback(self.w.preview)

    def expandGlyph(self, glyph, preserveComponents=True):
        glyph.prepareUndo("Outline")

        outline = calculate(glyph, self.getOptions(), preserveComponents)

        glyph.clearContours()
        outline.drawPoints(glyph.getPointPen())

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
