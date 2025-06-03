import bpy, bmesh, math
from math import pi
#import importlib
#import numpy as np
#from contextlib import redirect_stdout
#import io, os
from typing import NamedTuple

BU = bpy.data.texts['BlenderUtils.py'].as_module()

on=1;off=0

MainDir = bpy.path.abspath("//")

################################################################################
# Defining HDRIs
################################################################################

TexDir = MainDir + "textures/"

class HDRIrec(NamedTuple):
    File: str
    V_offset: float
    Angle_offset: float
    SunHAngle: float
    SunVAngle: float
    LightInt:float

HDRI=[]
HDRI.append(HDRIrec('cgaxis_hdri_skies_01_59', 0.0, 90,  00, 50, 3.0)) # Bright Day  
HDRI.append(HDRIrec('cgaxis_hdri_skies_01_62', 0.0, 90, -90, 80, 0.5)) # Evening
HDRI.append(HDRIrec('kloppenheim_06_8k', -0.005, 110, -60, 85, 1)) # Purple clouds

################################################################################
# Some function definitions
################################################################################
        
def linkNodes(world,from_node, from_slot_name, to_node, to_slot_name):
    input = to_node.inputs[to_slot_name]
    output = from_node.outputs[from_slot_name]
    world.node_tree.links.new(input, output)  
    
def ClearWorldNodes():
    nodes = bpy.data.worlds['World'].node_tree.nodes
    for node in nodes:
        if (node.name!='World Output') and (node.name!='Background'): # skip the material output node as we'll need it later
            nodes.remove(node)                  
        
################################################################################
# Setting the sky
################################################################################

def SetSky(RealSky=on, SkyNr=0, Z_Move=0, Angle=0, Intensity=0.5):

    world = bpy.context.scene.world
    world.use_nodes = True
    ClearWorldNodes()
    Mat=bpy.context.scene.world.node_tree.nodes["World Output"]
    BkGr=bpy.context.scene.world.node_tree.nodes["Background"]

    Mat.location=(0,0)
    BkGr.location=(-200,0)

    if RealSky==on:
        
        LightIntensity=HDRI[SkyNr].LightInt
        path=TexDir+HDRI[SkyNr].File+'/'+HDRI[SkyNr].File+'.hdr'
        
        EnvTex=world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        EnvTex.location=(-500,0)        
        EnvImage = bpy.data.images.load(filepath = path)
        EnvImage.name="Image node"
        EnvTex.image=EnvImage 
        linkNodes(world,EnvTex, 'Color', BkGr, 'Color')
        
        EnvMap=world.node_tree.nodes.new("ShaderNodeMapping")
        EnvMap.location=(-700,0)
        EnvMap.inputs[1].default_value[2]=Z_Move
        world.node_tree.nodes["Mapping"].inputs[1].default_value[2] = 0.02
        
        EnvMap.inputs[2].default_value[2]=(HDRI[SkyNr].Angle_offset-Angle)/180*pi
        linkNodes(world, EnvMap, 'Vector', EnvTex, 'Vector')
        
        EnvTextCor=world.node_tree.nodes.new("ShaderNodeTexCoord")
        EnvTextCor.location=(-900,0)
        linkNodes(world, EnvTextCor, 'Generated', EnvMap, 'Vector')
        #world.node_tree.nodes["Mapping"].inputs[1].default_value[2] = -HDRI[SkyNr].V_offset

    else:
        EnvTex=world.node_tree.nodes.new("ShaderNodeTexSky")
        EnvTex.turbidity = 1
        EnvTex.ground_albedo = 0.1
        linkNodes(world,EnvTex, 'Color', BkGr, 'Color')
        world.node_tree.nodes["Background"].inputs[1].default_value=4

    BkGr.inputs[1].default_value = Intensity

    # --- Setting the Sun ---------------------------------------------------------
    
    BU.RemoveObject('Sun')
        
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 0))
    Sun=BU.Active()
    Sun.name="Sun"
    Sun.location=(-0,-60,50)
    Sun.rotation_euler=(HDRI[SkyNr].SunVAngle/180*pi,0,(HDRI[SkyNr].SunHAngle+Angle)/180*pi)
    Sun.data.use_nodes=True
    Sun.data.node_tree.nodes['Emission'].inputs[0].default_value = (0.95, 0.95, 1.0, 1)
    Sun.data.node_tree.nodes["Emission"].inputs[1].default_value = 3

if __name__ == "__main__": 
    
    BU.CleanAll()

    SetSky(RealSky=on, SkyNr=2, Z_Move=0.02, Angle = 0, Intensity=0.5)
    
    White_Mat=bpy.data.materials.new(name="White_Mat")    
    
    bpy.ops.mesh.primitive_plane_add(size=8000, location=(0, 0, 0))
    Plane=BU.Active()
    Plane.data.materials.append(White_Mat)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=5, location=(0, 0, 0))
    Pole=BU.Active()
    Pole.data.materials.append(White_Mat)
    
    bpy.ops.object.text_add(location=(-5, 100, 5), rotation=(90/180*pi, 0, 0), radius=10)
    NorthText=BU.Active()
    NorthText.name="NorthText"
    NorthText.data.body = "North"

    bpy.ops.object.text_add(location=(5, -100, 5), rotation=(90/180*pi, 0,pi), radius=10)
    SouthText=BU.Active()
    SouthText.name="SouthText"
    SouthText.data.body = "South"

    bpy.ops.object.text_add(location=(100, 0, 5), rotation=(90/180*pi, 0,-0.5*pi), radius=10)
    EastText=BU.Active()
    EastText.name="EastText"
    EastText.data.body = "East"
    
    bpy.ops.object.text_add(location=(-100, 0, 5), rotation=(90/180*pi, 0,0.5*pi), radius=10)
    WestText=BU.Active()
    WestText.name="WestText"
    WestText.data.body = "West"
