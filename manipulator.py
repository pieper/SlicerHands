import numpy,vtk,slicer

class Manipulator(object):
  '''A superclass for managing various slicer actions
  that are triggered by changes to node attributes
  (in the driving use case, they will be transform nodes
  with attributes corresponding to user actions)
  For now, you can set observations incrementally, 
  but cannot release them except by calling cleanup, which
  removes all.
  '''

  def __init__(self):
    self.observerTags = {}
    self.nodeOldStates = {}
    self.nodeStates = {}

  def __del__(self):
    self.cleanup()

  def cleanup(self):
    """Remove any pending observations"""
    for obj in self.observerTags:
      obj.RemoveObserver(self.observerTags[obj])
    self.observerTags = {}
    self.nodeOldStates = {}
    self.nodeStates = {}

  def onNodeModified(self,caller,event):
    """Update the nodeStates in response to 
    modified events:
    - keep track of the old and current value
    - call the callback when the state changes
    - this can be subclassed if need to track events
    """
    for attribute in self.nodeStates[caller]:
      newValue = caller.GetAttribute(attribute)
      if newValue != self.nodeStates[caller][attribute]:
        oldValue = self.nodeStates[caller][attribute]
        self.nodeOldStates[caller][attribute] = self.nodeStates[caller][attribute]
        self.nodeStates[caller][attribute] = newValue
        self.onAttributeChanged(caller,attribute,newValue,oldValue)

  def observeAttributes(self,observations):
    for node,attributes in observations:
      self.nodeOldStates[node] = {}
      self.nodeStates[node] = {}
      for attribute in attributes:
        self.nodeStates[node][attribute] = node.GetAttribute(attribute)
      if not node in self.observerTags:
        self.observerTags[node] = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onNodeModified)

  def onAttributeChanged(self,node,attribute,newValue,oldValue):
    """Called when an attribute changes - to be overridden by subclass"""
    print(node,attribute,newValue,oldValue)
    pass


class SliceJumper(Manipulator):
  """Jump slices to the location of the hand tansform
  when there is a pinch gesture"""

  def __init__(self,transform):
    super(SliceJumper,self).__init__()
    self.transform = transform
    self.jumping = False
    self.lastJumpLocation = numpy.array( (0,0,0) )
    self.currentJumpLocation = numpy.array( (0,0,0) )
    self.startOfJumpPosition = numpy.array( (0,0,0) )
    self.observeAttributes( ((transform, ('SlicerHands.gesture',)),) )
    event = slicer.vtkMRMLTransformNode.TransformModifiedEvent
    self.observerTags[transform] = transform.AddObserver(event, self.onTransform)

  def position(self,transformNode):
    m = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToWorld(m)
    return numpy.array( (m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)) )

  def onTransform(self,caller,event):
    if self.jumping:
      lm = slicer.app.layoutManager()
      redWidget = lm.sliceWidget('Red')
      redNode = redWidget.mrmlSliceNode()
      currentPosition = self.position(caller)
      move = currentPosition - self.startOfJumpPosition
      self.currentJumpLocation = self.lastJumpLocation + move
      redNode.JumpSlice(*self.currentJumpLocation)
      redNode.JumpAllSlices(*self.currentJumpLocation)

  def onAttributeChanged(self,node,attribute,newValue,oldValue):
    if node == self.transform:
      if attribute == 'SlicerHands.gesture':
        newJumpState = newValue == 'pinch'
        if newJumpState and not self.jumping:
          # start of a jump action
          self.startOfJumpPosition = self.position(node)
        if not newJumpState and self.jumping:
          # end of a jump action
          self.lastJumpLocation = self.currentJumpLocation
        self.jumping = newJumpState
