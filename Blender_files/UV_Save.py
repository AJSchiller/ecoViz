import bpy, bmesh, sys, math
from math import pi
import numpy as np
import io, os, time

BU = bpy.data.texts['BlenderUtils.py'].as_module()
MT = bpy.data.texts['Materials.py'].as_module()

inf=1e6; on=1; off=0

MainDir = bpy.path.abspath("//")

################################################################################
# Saving and loading the UVs
################################################################################

def SaveUVs(obj, UVFolder): 
    FileName = obj.name
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.face_map.verify()  # currently blender needs both layers.
    # Save UVs
    UVs=[]
    for f in bm.faces:
        for l in f.loops:
            UVs.append((l[uv_layer].uv[0], l[uv_layer].uv[1]))
    bm.to_mesh(me)
    UVm=np.array(UVs)
    np.save(UVFolder+FileName,UVm)
    print('=> USs Saved!')
 
def LoadUVs(obj, UVFolder): 
    FileName = obj.name
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.face_map.verify()  # currently blender needs both layers.
    # Save UVs
    i=0;
    UVm=np.load(UVFolder+FileName+'.npy')
    for f in bm.faces:
        for l in f.loops:
            l[uv_layer].uv[0] = UVm[i][0]
            l[uv_layer].uv[1] = UVm[i][1]
            i=i+1
    bm.to_mesh(me)
    print('=> UVs for', obj.name, 'restored!') 

################################################################################
# Saving and loading the UVs
################################################################################

if __name__ == "__main__":
    
    SAVE=on
    
    obj=BU.Active()
    
    if SAVE==on:
        UVFolder = MainDir + '/UVMaps/'
        SaveUVs(obj,UVFolder)
    else:
        UVFolder = MainDir + '/UVMaps/'
        LoadUVs(obj,UVFolder)