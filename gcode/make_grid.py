#!/usr/bin/env python

#
# directly generate gcode for 3D printing segmented bezel 
#

import math

def inch(x):
  return 25.4 * x

class Gcode:
  def __init__(self):
    self.zOffset = 0    
    # platform center
    self.cX = 100
    self.cY = 100
    self.cZ = 0
    self.extrusionDistance = 0
    self.retractDistance = 1
    self.retractSpeed = 75*60
    self.filamentDiameter = 1.68
    self.extrusionWidth = 0.42
    self.layerHeight = 0.254
    self.extrusionCorrection = 0.75 # black PolyMax filament
    self.filamentCrossSection = math.pi * math.pow(self.filamentDiameter/2, 2)
    self.beadCrossSection = ( self.layerHeight * 
                              (self.extrusionWidth - self.layerHeight) +
                              math.pi * math.pow((self.layerHeight/2), 2) );
    self.extrusionFactor = ( self.extrusionCorrection * 
                             self.beadCrossSection /
                             self.filamentCrossSection );
    self.moveFeedRate = 75 * 60;
    self.extrudeRate = 40 * 60;
    return
  
  def emitLines(self, lines):
    for line in lines:
      print line

  def startCode(self):
    code = [
      'G21; set mm units',
      'G28; home all axis',
      'G90; set absolute coordinates',
      'G92 E0; reset extruder distance',
      'M140 S40;set bed pre-temperature',
      'M190 S40; wait for bed pre-temp',
      'M104 S140; set extruder IDLE temp and start heating',
      'M140 S50; set bed temperature',
      'M190 S45; wait for bed to heat up',
      'M104 S193; set extruder temp and start heating',
      'G1 Z5 F300 ;move platform down 5mm',
      'G1 X160 Y130 F3000 ; move to back right corner',
      'M190 S50; wait for bed to heat up',
      'M109 S193; wait for extruder temp to be reached',
      'G1 Z0.35 F200 ;move platform close to nozzle',
      'G1 E7; extruder anchor',
      'G92 E0; reset extrusion distance',
      'G1 F3000; Set feed rate for first move.'
      ];
    self.emitLines(code)

  def endCode(self):
    code = [
      'M140 S0 ;Turn heated bed off',
      'M104 S0 ;Turn nozzle heat off',
      'G91 ;Make coordinates relative',
      'G0 Z2 E-2 ;Move up 2mm and retract extuder 2mm at 400mm/min',
      'G90 ;Use absolute coordinates again',
      'G00 X100 Y200 F10000 ;Go to dump area',
      'M84 ;Disable steppers so they dont get hot during idling...',
      'M84 S0 ;Cancel the timeout set by the start gcode'
      ]
    self.emitLines(code)

  def moveTo(self, x, y, z):
    px = self.cX + x
    py = self.cY + y
    pz = self.cZ + z
    code = [ "G1 X%.3f Y%.3f Z%.3f F%.4f E%.4f" % (px, py, pz,
                                                   self.extrudeRate,
                                                   self.extrusionDistance) ]
    self.emitLines(code)
    self.currentX = px
    self.currentY = py
    self.currentZ = pz
    return
  
  def lineTo(self, x, y, z):
    px = self.cX + x
    py = self.cY + y
    pz = self.cZ + z
    extrusionLength = ( self.extrusionFactor *
                        math.sqrt(math.pow(px - self.currentX, 2) +
                                  math.pow(py - self.currentY, 2) +
                                  math.pow(pz - self.currentZ, 2)))
    self.extrusionDistance += extrusionLength
    code = [ "G1 X%.3f Y%.3f Z%.3f F%.4f E%.4f" % (px, py, pz,
                                                   self.extrudeRate,
                                                   self.extrusionDistance) ]
    self.emitLines(code)
    self.currentX = px
    self.currentY = py
    self.currentZ = pz
    return

  def retract(self):
    code = []
    if (self.retractDistance):
        self.extrusionDistance -= self.retractDistance;
        code.append('G1 E%f F%f' % (self.extrusionDistance,
                                    self.retractSpeed))
    self.extrusionDistance = 0.
    code.append('G92 E0')
    self.emitLines(code)
    return

  def unRetract(self):
    if (self.retractDistance):
      self.extrusionDistance += self.retractDistance
      code = ['G1 E%f F%f' % (self.extrusionDistance,
                              self.retractSpeed)]
      self.emitLines(code)
    return
  
def makeGrid(gc, rows, cols, dx, dy, height):
  minX = 0
  minY = 0
  minZ = 0
  maxX = minX + cols * dx
  maxY = minY + rows * dy

  layers = int(math.floor(height / gc.layerHeight))
  gc.startCode()
  for layer in range(0, layers):
    z = (layer + 1) * gc.layerHeight
    if (layer % 4) == 0:
      gc.retract()
      gc.moveTo(minX, minY, z)      
      gc.unRetract()
      for row in range(0, rows+1):
        y = minY + dy * row
        if (not row % 2):
          gc.lineTo(maxX, y, z);
          if (row < rows):
            gc.lineTo(maxX, y + dy, z)
        else:
          gc.lineTo(minX, y, z);
          if (row < rows):
            gc.lineTo(minX, y + dy, z)
    if (layer % 4) == 1:
      gc.retract()
      gc.moveTo(minX, maxY, z)      
      gc.unRetract()      
      for col in range(0, cols+1):
        x = minX + dx * col
        if (not col % 2):
          gc.lineTo(x, minY, z);
          if (col < cols):
            gc.lineTo(x + dx, minY, z)
        else:
          gc.lineTo(x, maxY, z);
          if (col < cols):
            gc.lineTo(x + dx, maxY, z)
    if (layer % 4) == 2:
      gc.retract()
      gc.moveTo(minX, maxY, z)      
      gc.unRetract()      
      for row in range(0, rows+1):
        y = minY + dy * (rows - row)
        if (not row % 2):
          gc.lineTo(maxX, y, z);
          if (row < rows):
            gc.lineTo(maxX, y - dy, z)
        else:
          gc.lineTo(minX, y, z);
          if (row < rows):
            gc.lineTo(minX, y - dy, z)
    if (layer % 4) == 3:
      gc.retract()
      gc.moveTo(maxX, maxY, z)      
      gc.unRetract()      
      for col in range(0, cols + 1):
        x = minX + dx * (cols - col)
        if (not col % 2):
          gc.lineTo(x, minY, z);
          if (col < cols):
            gc.lineTo(x - dx, minY, z)
        else:
          gc.lineTo(x, maxY, z);
          if (col < cols):
            gc.lineTo(x - dx, maxY, z)
  gc.endCode()


# configurable parameters
rows = 10
cols = 10
dx = inch(0.1)
dy = inch(0.1)
height = inch(0.1)

gc = Gcode()
makeGrid(gc, rows, cols, dx, dy, height)
