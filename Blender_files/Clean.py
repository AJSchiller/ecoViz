import bpy, bmesh, sys, math

BU = bpy.data.texts['BlenderUtils.py'].as_module()
BU.DeleteAll(exclude=[])
BU.CleanAll()
