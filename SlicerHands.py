import os
import unittest
from __main__ import vtk, qt, ctk, slicer

import manipulator

#
# SlicerHands
#

class SlicerHands:
  def __init__(self, parent):
    parent.title = "SlicerHands" # TODO make this more human readable by adding spaces
    parent.categories = ["Work in Progress"]
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This exposes a touchless interface to slicer.
    """
    parent.acknowledgementText = """
    This file was originally developed by Steve Pieper, Isomics, Inc. and was partially funded by NIH grants P41 RR013218 and U54 EB005149.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['SlicerHands'] = self.runTest

  def runTest(self):
    tester = SlicerHandsTest()
    tester.runTest()

#
# qSlicerHandsWidget
#

class SlicerHandsWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

    self.logic = SlicerHandsLogic()

  def setup(self):
    # Instantiate and connect widgets ...

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "SlicerHands Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    self.layout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    # Parameters button
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the parameters collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    # start hand driver button
    startDriver = qt.QPushButton("Start Hand Driver")
    startDriver.toolTip = "Run the threegear hand driver"
    parametersFormLayout.addWidget(startDriver)
    startDriver.connect('clicked()', self.startDriver)

    # connect to the driver
    self.connectToHandsButton = qt.QPushButton("Connect to Hand Driver")
    self.connectToHandsButton.toolTip = "Connect to the threegear hand driver"
    parametersFormLayout.addWidget(self.connectToHandsButton)
    self.connectToHandsButton.connect('clicked()', self.connectToHands)

    # connect to the driver
    self.disconnectFromHandsButton = qt.QPushButton("Disconnect from Hand Driver")
    self.disconnectFromHandsButton.toolTip = "Disconnect from the threegear hand driver"
    self.disconnectFromHandsButton.enabled = False
    parametersFormLayout.addWidget(self.disconnectFromHandsButton)
    self.disconnectFromHandsButton.connect('clicked()', self.disconnectFromHands)

    # update camera transform (temp)
    self.updateCameraButton = qt.QPushButton("UpdateCameraTransform")
    parametersFormLayout.addWidget(self.updateCameraButton)
    self.updateCameraButton.connect('clicked()', self.updateCamera)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Set local var as instance attribute
    self.startDriver = startDriver

  def startDriver(self):
    import subprocess
    print('TODO: launch batch file from python - use shortcut on desktop for now')
    self.driver = subprocess.Popen(['handdriver.bat', 'pieper'], cwd=r'd:\threegear\GesturalUserInterface')
    self.driverout, self.drivererr = self.driver.communicate()

  def connectToHands(self):
    self.logic.connectToHands()
    self.disconnectFromHandsButton.enabled = True
    self.connectToHandsButton.enabled = False

  def disconnectFromHands(self):
    self.logic.disconnectFromHands()
    self.disconnectFromHandsButton.enabled = False
    self.connectToHandsButton.enabled = True

  def updateCamera(self):
    cameraToRAS,distance = self.logic.cameraTransform()
    tableToCamera = self.logic.tableCursor()
    tableToCamera.GetMatrixTransformToParent().SetElement(2, 3, -distance)
    tableToCamera.SetAndObserveTransformNodeID(cameraToRAS.GetID())
    leftToTable,leftHandLine = self.logic.handCursor('Left')
    rightToTable,rightHandLine = self.logic.handCursor('Right')
    for node in (leftToTable,leftHandLine,rightToTable,rightHandLine):
      node.SetAndObserveTransformNodeID(tableToCamera.GetID())

  def onReload(self,moduleName="SlicerHands"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)
    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()

  def onReloadAndTest(self,moduleName="SlicerHands"):
    self.onReload()
    evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
    tester = eval(evalString)
    tester.runTest()

#
# SlicerHandsLogic
#

class SlicerHandsLogic:
  """
  Logic for managing connection to the hand driver
  and mapping events into changes in the mrml scene
  """
  def __init__(self):
    self.host='localhost'
    self.port=1988
    self.socket = None

  def __del__(self):
    self.disconnectFromHands()

  def connectToHands(self):
    """
    Initiate the connection
    """
    self.socket = qt.QTcpSocket()
    self.socket.connectToHost(self.host, self.port)
    self.socket.connect('readyRead()', self.handleRead)

  def disconnectFromHands(self):
    """
    terminate the connection
    """
    self.socket.abort()
    self.socket.close()

  def handleRead(self):
    while self.socket.canReadLine():
      m = str(self.socket.readLine()).split()
      if m[0] == 'POINT' and float(m[-1]) > .0:
        #print('Pointing %s at %s %s %s (conf: %s)' % (m[1], m[5], m[6], m[7], m[-1]))
        pass
      #events = ('PRESSED', 'RELEASED', 'DRAGGED', 'MOVED')
      events = ('PRESSED', 'RELEASED', 'DRAGGED')
      inGestureEvents = ('PRESSED', 'RELEASED', 'DRAGGED')
      outOfGestureEvents = ('RELEASED',)
      message = ""
      if m[0] in events:
        message += '%s %s' % (m[0], m[-1],)
        transform,line = self.handCursor(m[-1].title())
        if m[0] in inGestureEvents:
          transform.SetAttribute('SlicerHands.gesture', 'pinch')
        if m[0] in outOfGestureEvents:
          transform.SetAttribute('SlicerHands.gesture', None)

      if message != "":
        slicer.util.showStatusMessage(message)
      if m[0] == 'POSE':
        pl = map(float,m[1:4])
        pr = map(float,m[9:12])
        leftTransform,leftHandLine = self.handCursor('Left')
        rightTransform,rightHandLine = self.handCursor('Right')
        for t,p in ( (leftTransform,pl), (rightTransform,pr) ):
          t.GetMatrixTransformToParent().SetElement(0, 3, p[0])
          t.GetMatrixTransformToParent().SetElement(1, 3, p[1])
          t.GetMatrixTransformToParent().SetElement(2, 3, p[2])
        for handLine,p in ( (leftHandLine,pl), (rightHandLine,pr) ):
          points = handLine.GetPolyData().GetPoints()
          points.SetPoint(0,p[0], 0.0,p[2])
          points.SetPoint(1,p[0],p[1],p[2])
          handLine.GetPolyData().Modified()


  def cameraTransform(self):
    """Create the transform and the observer for the camera
    """
    transformName = 'Camera-To-RAS'
    transformNode = slicer.util.getNode(transformName)
    if not transformNode:
      # Create transform node
      transformNode = slicer.vtkMRMLLinearTransformNode()
      transformNode.SetName(transformName)
      slicer.mrmlScene.AddNode(transformNode)

    # update transform with current camera parameters - only default view for now
    lm = slicer.app.layoutManager()
    threeDWidget = lm.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    viewNode = threeDView.mrmlViewNode()
    cameraNodes = slicer.util.getNodes('vtkMRMLCameraNode*')
    for cameraNode in cameraNodes.values():
      if cameraNode.GetActiveTag() == viewNode.GetID():
        break
    camera = cameraNode.GetCamera()

    import numpy
    position = numpy.array(camera.GetPosition())
    focalPoint = numpy.array(camera.GetFocalPoint())
    viewUp = numpy.array(camera.GetViewUp())
    viewPlaneNormal = numpy.array(camera.GetViewPlaneNormal())
    viewAngle = camera.GetViewAngle()
    viewRight = numpy.cross(viewUp,viewPlaneNormal)
    viewDistance = numpy.linalg.norm(focalPoint - position)

    cameraToRAS = vtk.vtkMatrix4x4()
    for row in xrange(3):
      cameraToRAS.SetElement(row, 0, viewRight[row])
      cameraToRAS.SetElement(row, 1, viewUp[row])
      cameraToRAS.SetElement(row, 2, viewPlaneNormal[row])
      cameraToRAS.SetElement(row, 3, position[row])

    transformNode.GetMatrixTransformToParent().DeepCopy(cameraToRAS)
    return transformNode,viewDistance

  def handCursor(self,whichHand='Left'):
    """Create the mrml structure to represent a hand cursor if needed
    otherwise return the current transform
    whichHand : 'Left' for left color, anything else for right
                also defines suffix for Transform and Cursor
    """
    transformName = '%s-To-Table' % whichHand
    transformNode = slicer.util.getNode(transformName)
    if not transformNode:
      # make the mrml 
      sphere = vtk.vtkSphereSource()
      sphere.Update()
      # Create model node
      cursor = slicer.vtkMRMLModelNode()
      cursor.SetScene(slicer.mrmlScene)
      cursor.SetName("Cursor-%s" % whichHand)
      cursor.SetAndObservePolyData(sphere.GetOutput())
      # Create display node
      cursorModelDisplay = slicer.vtkMRMLModelDisplayNode()
      if whichHand == 'Left':
        color = (1,.84313725490196079,0) # gold (wedding ring hand)
      else:
        color = (0.69411764705882351, 0.47843137254901963, 0.396078431372549) # slicer skin tone
      cursorModelDisplay.SetColor(color)
      cursorModelDisplay.SetScene(slicer.mrmlScene)
      slicer.mrmlScene.AddNode(cursorModelDisplay)
      cursor.SetAndObserveDisplayNodeID(cursorModelDisplay.GetID())
      # Add to slicer.mrmlScene
      cursorModelDisplay.SetInputPolyData(sphere.GetOutput())
      slicer.mrmlScene.AddNode(cursor)
      # Create transform node
      transformNode = slicer.vtkMRMLLinearTransformNode()
      transformNode.SetName(transformName)
      for i in xrange(3):
        transformNode.GetMatrixTransformToParent().SetElement(i, i, 10)
      slicer.mrmlScene.AddNode(transformNode)
      cursor.SetAndObserveTransformNodeID(transformNode.GetID())
    handLineNode = self.handLine(whichHand)
    return transformNode,handLineNode

  def handLine(self,whichHand='Left'):
    """Create a line to show the path from the hand to the table
    """
    handLineName = 'DropLine-%s' % whichHand
    handLineNode = slicer.util.getNode(handLineName)
    if not handLineNode:
      points = vtk.vtkPoints()
      polyData = vtk.vtkPolyData()
      polyData.SetPoints(points)

      lines = vtk.vtkCellArray()
      polyData.SetLines(lines)
      linesIDArray = lines.GetData()
      linesIDArray.Reset()
      linesIDArray.InsertNextTuple1(0)

      polygons = vtk.vtkCellArray()
      polyData.SetPolys( polygons )
      idArray = polygons.GetData()
      idArray.Reset()
      idArray.InsertNextTuple1(0)

      for point in ( (0,0,0), (1,1,1) ):
        pointIndex = points.InsertNextPoint(*point)
        linesIDArray.InsertNextTuple1(pointIndex)
        linesIDArray.SetTuple1( 0, linesIDArray.GetNumberOfTuples() - 1 )
        lines.SetNumberOfCells(1)
        
      # Create handLineNode model node
      handLineNode = slicer.vtkMRMLModelNode()
      handLineNode.SetScene(slicer.mrmlScene)
      handLineNode.SetName("DropLine-%s" % whichHand)
      handLineNode.SetAndObservePolyData(polyData)

      # Create display node
      modelDisplay = slicer.vtkMRMLModelDisplayNode()
      modelDisplay.SetColor(1,1,0) # yellow
      modelDisplay.SetScene(slicer.mrmlScene)
      slicer.mrmlScene.AddNode(modelDisplay)
      handLineNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())

      # Add to slicer.mrmlScene
      modelDisplay.SetInputPolyData(handLineNode.GetPolyData())
      slicer.mrmlScene.AddNode(handLineNode)
    return handLineNode


  def tableCursor(self,dimensions=(900,30,600)):
    """Create the mrml structure to represent the table if needed
    otherwise return the current transform
    dimensions : left-right, up-down, in-out size of table
    """
    transformName = 'Table-To-Camera'
    transformNode = slicer.util.getNode(transformName)
    if not transformNode:
      # make the mrml 
      box = vtk.vtkCubeSource()
      box.SetXLength(dimensions[0])
      box.SetYLength(dimensions[1])
      box.SetZLength(dimensions[2])
      box.SetCenter(0,-dimensions[1]/2.,0)

      box.Update()
      # Create model node
      cursor = slicer.vtkMRMLModelNode()
      cursor.SetScene(slicer.mrmlScene)
      cursor.SetName("Cursor-Table")
      cursor.SetAndObservePolyData(box.GetOutput())
      # Create display node
      cursorModelDisplay = slicer.vtkMRMLModelDisplayNode()
      cursorModelDisplay.SetColor((0.86274509803921573,)*3) # 'gainsboro'
      cursorModelDisplay.SetOpacity(0.5)
      cursorModelDisplay.SetScene(slicer.mrmlScene)
      slicer.mrmlScene.AddNode(cursorModelDisplay)
      cursor.SetAndObserveDisplayNodeID(cursorModelDisplay.GetID())
      # Add to slicer.mrmlScene
      cursorModelDisplay.SetInputPolyData(box.GetOutput())
      slicer.mrmlScene.AddNode(cursor)
      # Create transform node
      transformNode = slicer.vtkMRMLLinearTransformNode()
      transformNode.SetName(transformName)
      slicer.mrmlScene.AddNode(transformNode)
      tableToCamera = vtk.vtkMatrix4x4()
      tableToCamera.SetElement(1, 3, -100)
      transformNode.GetMatrixTransformToParent().DeepCopy(tableToCamera)
      cursor.SetAndObserveTransformNodeID(transformNode.GetID())
    return transformNode


class SlicerHandsTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SlicerHands1()

  def test_SlicerHands1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SlicerHandsLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
