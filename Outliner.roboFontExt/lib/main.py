import outlinePen

from mojo.subscriber import registerSubscriberEvent


registerSubscriberEvent(
    subscriberEventName="com.typemytype.outliner.changed",
    methodName="outlinerDidChange",
    lowLevelEventNames=["com.typemytype.outliner.changed"],
    dispatcher="roboFont",
    documentation="Send when the outliner pallette did change parameters.",
    delay=0,
    # debug=True
)

registerSubscriberEvent(
    subscriberEventName="com.typemytype.outliner.displayChanged",
    methodName="outlinerDisplayDidChanged",
    lowLevelEventNames=["com.typemytype.outliner.displayChanged"],
    dispatcher="roboFont",
    documentation="Send when the outliner pallette did change display options.",
    # debug=True
)