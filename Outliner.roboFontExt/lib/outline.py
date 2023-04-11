import ezui
from fontTools.misc.arrayTools import calcBounds

from mojo.roboFont import OpenWindow, CurrentGlyph, CurrentFont
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.events import postEvent

from outlinePen import OutlinePen


outlinePaletteDefaultKey = "com.typemytype.outliner.v3"

lineJoinOptions = ["Square", "Round", "Butt"]
endCapOptions = ["Square", "Round", "Butt", "Open"]


def calculate(glyph, options):
    cap = endCapOptions[options["endCapPopUpButton"]].lower()
    if cap == "open":
        cap = "square"
    closeOpenPaths = options["endCapPopUpButton"] == 3

    pen = OutlinePen(
        glyph.layer,
        offset=options["strokeWidthField"],
        contrast=options["strokeContrastField"],
        contrastAngle=options["strokeContrastAngleField"],
        connection=lineJoinOptions[options["lineJoinPopUpButton"]].lower(),
        cap=cap,
        miterLimit=options["miterLimitField"],
        closeOpenPaths=closeOpenPaths,
        optimizeCurve=options["optimizeCurvesCheckbox"],
        preserveComponents=options["preserveComponentsCheckbox"],
        filterDoubles=options["optimizeDoublePointsCheckbox"]
    )

    if options["applyToRadioButtons"] == 3:
        # only apply on selected contours/components
        for contour in glyph:
            if contour.selected:
                contour.draw(pen)
        for components in glyph.components:
            if component.selected:
                component.draw(pen)
    else:
        glyph.draw(pen)

    pen.drawSettings(
        drawOriginal=options["outputStrokeSourceCheckbox"],
        drawInner=options["outputStrokeLeftCheckbox"],
        drawOuter=options["outputStrokeRightCheckbox"]
    )

    result = pen.getGlyph()
    if options["preserveBoundsCheckbox"]:
        if glyph.bounds and result.bounds:
            if options["applyToRadioButtons"] == 3:
                # only apply on selected contours/components
                bounds = []
                for contour in glyph:
                    if contour.selected and contour.bounds:
                        selectedMinx, selectedMiny, selectedMaxx, selectedMaxy = contour.bounds
                        bounds.append((selectedMinx, selectedMiny))
                        bounds.append((selectedMaxx, selectedMaxy))
                for components in glyph.components:
                    if component.selected and component.bounds:
                        selectedMinx, selectedMiny, selectedMaxx, selectedMaxy = component.bounds
                        bounds.append((selectedMinx, selectedMiny))
                        bounds.append((selectedMaxx, selectedMaxy))
                minx1, miny1, maxx1, maxy1 = calcBounds(bounds)
            else:
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

    def glyphEditorDidSetGlyph(self, info):
        self.updateOutline(info["glyph"])

    def glyphEditorGlyphDidChangeOutline(self, info):
        self.updateOutline(info["glyph"])

    def glyphDidChangeSelection(self, info):
        self.updateOutline(info["glyph"])

    def updateDisplay(self):
        if self.controller:
            displayOptions = self.controller.getDisplayOptions()
            r, g, b, a = displayOptions["color"]
            self.path.setVisible(displayOptions["shouldFill"] or displayOptions["shouldStroke"])
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


class OutlinerWindowController(ezui.WindowController):

    def build(self):
        content = """
        = TwoColumnForm

        : Stroke Width:
        --X-- [__]                        @strokeWidthField

        : Stroke Contrast:
        --X-- [__]                        @strokeContrastField

        : Stroke Contrast Angle:
        --X-- [__]                        @strokeContrastAngleField

        : Miter Limit:
        --X-- [__]                        @miterLimitField

        : Line Join:
        ( ...)                            @lineJoinPopUpButton

        : End Cap:
        ( ...)                            @endCapPopUpButton

        : Output Strokes:
        [ ] Source                        @outputStrokeSourceCheckbox
        [X] Left                          @outputStrokeLeftCheckbox
        [X] Right                         @outputStrokeRightCheckbox

        : Preserve:
        [X] Components                    @preserveComponentsCheckbox
        [ ] Bounds                        @preserveBoundsCheckbox

        : Optimize:
        [ ] Curves                        @optimizeCurvesCheckbox
        [X] Double Points                 @optimizeDoublePointsCheckbox

        : Apply To:
        ( ) All Glyphs                    @applyToRadioButtons
        ( ) Selected Glyphs
        (X) Current Glyph
        ( ) Current Glyph Selection

        : Outline in Layer:
        [_  _]                            @outputLayerField

        =---=

        (( Preview ...))                  @previewPullDownButton
        * ColorWell                       @previewColorWell
        ( Outline )                       @outlineButton
        """
        maxStrokeWidth = 500
        descriptionData = dict(
            content=dict(
                itemColumnWidth=175
            ),
            strokeWidthField=dict(
                valueType="integer",
                value=20,
                minValue=1,
                maxValue=maxStrokeWidth
            ),
            strokeContrastField=dict(
                valueType="integer",
                value=0,
                minValue=0,
                maxValue=maxStrokeWidth
            ),
            strokeContrastAngleField=dict(
                valueType="float",
                value=0,
                minValue=0,
                maxValue=360
            ),
            miterLimitField=dict(
                valueType="integer",
                value=0,
                minValue=0,
                maxValue=maxStrokeWidth
            ),
            lineJoinPopUpButton=dict(
                items=lineJoinOptions,
                selected=0
            ),
            endCapPopUpButton=dict(
                items=endCapOptions,
                selected=0
            ),
            outputStrokeSourceCheckbox=dict(),
            outputStrokeLeftCheckbox=dict(),
            outputStrokeRightCheckbox=dict(),
            preserveComponentsCheckbox=dict(),
            preserveBoundsCheckbox=dict(),
            optimizeCurvesCheckbox=dict(),
            optimizeDoublePointsCheckbox=dict(),
            applyToRadioButtons=dict(),
            outputLayerComboBox=dict(),
            previewPullDownButton=dict(
                itemDescriptions=[
                    dict(
                        identifier="fillMenuItem",
                        text="Fill",
                        state=getExtensionDefault(f"{outlinePaletteDefaultKey}.previewFill", True)
                    ),
                    dict(
                        identifier="strokeMenuItem",
                        text="Stroke",
                        state=getExtensionDefault(f"{outlinePaletteDefaultKey}.previewStroke", False)
                    ),
                ],
                gravity="leading"
            ),
            previewColorWell=dict(
                width=50,
                gravity="leading",
                color=getExtensionDefault(f"{outlinePaletteDefaultKey}.previewColor", (0, 1, 1, .8))
            ),
            outlineButton=dict(),
        )
        self.w = ezui.EZPanel(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            title="Outliner"
        )

        defaults = getExtensionDefault(outlinePaletteDefaultKey, dict())
        self.w.setItemValues(defaults)

    def started(self):
        self.w.open()
        OutlinerGlyphEditor.controller = self
        registerGlyphEditorSubscriber(OutlinerGlyphEditor)

    def destroy(self):
        unregisterGlyphEditorSubscriber(OutlinerGlyphEditor)
        OutlinerGlyphEditor.controller = None

    def getOptions(self):
        return self.w.getItemValues()

    def getDisplayOptions(self):
        previewPullDownButton = self.w.getItem("previewPullDownButton")
        return dict(
            shouldFill=previewPullDownButton.getMenuItemState("fillMenuItem"),
            shouldStroke=previewPullDownButton.getMenuItemState("strokeMenuItem"),
            color=self.w.getItemValue("previewColorWell")
        )

    def fillMenuItemCallback(self, sender):
        value = not sender.state()
        previewPullDownButton = self.w.getItem("previewPullDownButton")
        previewPullDownButton.setMenuItemState("fillMenuItem", value)
        setExtensionDefault(f"{outlinePaletteDefaultKey}.previewFill", value)
        postEvent("com.typemytype.outliner.displayChanged")

    def strokeMenuItemCallback(self, sender):
        value = not sender.state()
        previewPullDownButton = self.w.getItem("previewPullDownButton")
        previewPullDownButton.setMenuItemState("strokeMenuItem", value)
        setExtensionDefault(f"{outlinePaletteDefaultKey}.previewStroke", value)
        postEvent("com.typemytype.outliner.displayChanged")

    def previewColorWellCallback(self, sender):
        setExtensionDefault(f"{outlinePaletteDefaultKey}.previewColor", sender.get())
        postEvent("com.typemytype.outliner.displayChanged")

    def contentCallback(self, sender):
        setExtensionDefault(outlinePaletteDefaultKey, sender.getItemValues())
        postEvent("com.typemytype.outliner.changed")

    def outlineButtonCallback(self, sender):
        options = self.getOptions()
        applyToValue = options["applyToRadioButtons"]
        font = CurrentFont()
        glyphs = []
        if applyToValue == 0:
            # All Glyphs
            glyphs = font
        elif applyToValue == 1:
            # Selected Glyphs
            glyphs = [font[glyphName] for glyphName in font.selection]
        elif applyToValue in [2, 3]:
            # Current Glyph
            glyphs = [CurrentGlyph()]

        for glyph in glyphs:
            outline = calculate(glyph, options)

            if options["outputLayerField"]:
                layerName = options["outputLayerField"].strip()
                if layerName:
                    glyph = glyph.getLayer(layerName)

            glyph.prepareUndo("Outline")

            if options["applyToRadioButtons"] == 3:
                for contour in list(glyph):
                    if contour.selected:
                        glyph.removeContour(contour)
                for component in list(glyph.components):
                    if component.selected:
                        glyph.removeComponent(component)
            else:
                glyph.clearContours()
                glyph.clearComponents()

            outline.drawPoints(glyph.getPointPen())

            glyph.round()
            glyph.performUndo()


OpenWindow(OutlinerWindowController)