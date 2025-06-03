import bpy, bmesh
from mathutils import Vector
from math import radians, pi, cos, sin
from mathutils import Euler, Matrix
import numpy as np
import time,os
from os.path import join, isfile

BU = bpy.data.texts['BlenderUtils.py'].as_module()

MainDir = bpy.path.abspath("//")
O=bpy.data.objects
C=bpy.data.collections
M=bpy.data.materials

on=True;off=False

SeaSize              = 5000
OceanBakeLength      = 500   
OceanTextureSizeA    = 5
OceanTextureSizeB    = 6
WaveDamping          = 0.2
WaterDiceNr          = 4

WaveFolder           = 'Wavefield'

################################################################################
# Linking to the ocean wave data
################################################################################
    
def Link_Waves(Ocean_Mat):
    # --- Linking the first wave Cache ---------------------------------------------   
    imageObjects = []
    imagePath = MainDir + WaveFolder+ '/Cache_A'
    imgFiles  = []

    for fn in sorted(os.listdir( imagePath )):
        fj=join( imagePath, fn ) 
        if isfile(fj) and fj.lower().endswith('.exr'): imgFiles.append(fj)

    # Load entire list of images
    for imgFile in imgFiles:
        Img=bpy.data.images.load( imgFile )
        Img.name='Cache_A_'+Img.name
        imageObjects.append( Img )  
       
    ImgNode=Ocean_Mat.node_tree.nodes['Image Texture A']   
    bpy.data.images["Cache_A_disp_0001.exr"].source = 'SEQUENCE'
    ImgNode.image=bpy.data.images['Cache_A_disp_0001.exr']  
    ImgNode.image_user.frame_start = 1
    ImgNode.image_user.frame_duration = OceanBakeLength
    ImgNode.image_user.frame_offset = 0
    ImgNode.image_user.use_auto_refresh = True

    Ocean_Mat.node_tree.nodes["Wave 1 map"].inputs[1].default_value = (-OceanTextureSizeA/2,-OceanTextureSizeA/2,0)
    Ocean_Mat.node_tree.nodes["Wave 1 map"].inputs[2].default_value = (0,0,90/180*pi)
    Ocean_Mat.node_tree.nodes["Wave 1 map"].inputs[3].default_value = (OceanTextureSizeA,OceanTextureSizeA,OceanTextureSizeA)

    # --- Linking the second wave Cache --------------------------------------------     
    imageObjects = []
    imagePath = MainDir + WaveFolder+'/Cache_B'
    imgFiles  = []

    for fn in sorted(os.listdir( imagePath )):
        fj=join( imagePath, fn ) 
        if isfile(fj) and fj.lower().endswith('.exr'): imgFiles.append(fj)

    # Load entire list of images
    for imgFile in imgFiles:
        # Add to image object list to use later
        Img=bpy.data.images.load( imgFile )
        Img.name='Cache_B_'+Img.name
        imageObjects.append( Img ) 

    ImgNode2=Ocean_Mat.node_tree.nodes['Image Texture B']   
    bpy.data.images["Cache_B_disp_0001.exr"].source = 'SEQUENCE'
    ImgNode2.image=bpy.data.images['Cache_B_disp_0001.exr']  
    ImgNode2.image_user.frame_start = 1
    ImgNode2.image_user.frame_duration =  OceanBakeLength
    ImgNode2.image_user.frame_offset = 0
    ImgNode2.image_user.use_auto_refresh = True

    Ocean_Mat.node_tree.nodes["Wave 2 map"].inputs[1].default_value = (-OceanTextureSizeB/2,-OceanTextureSizeB/2,0)
    Ocean_Mat.node_tree.nodes["Wave 2 map"].inputs[2].default_value = (0,0,90/180*pi)
    Ocean_Mat.node_tree.nodes["Wave 2 map"].inputs[3].default_value = (OceanTextureSizeB,OceanTextureSizeB,OceanTextureSizeB)

def SetSeaWaveParams(Mat):
    
    #Mat.node_tree.nodes["Mapping.004"].inputs[1].default_value[0] = 500
    #bpy.ops.image.open(filepath=MainDir+"Waterdepth_T.png", files=[{"name":"Waterdepth_T.png", "name":"Waterdepth_T.png"}], show_multiview=False)
    DepthImage = bpy.data.images.load(MainDir+"Waterdepth_T.png")
    DepthImage.colorspace_settings.name = 'Non-Color'
    Mat.node_tree.nodes["DampenImage"].image=bpy.data.images["Waterdepth_T.png"]

    # --- General settings --------------------------------------------------------
    Mat.node_tree.nodes["Texture Coordinate"].object = O["TexturePlacement"]
    Mat.node_tree.nodes["Wave damper"].inputs[1].default_value = WaveDamping

    # Setting the angle of wave number 1
    Mat.node_tree.nodes["Wave 1 map"].inputs[2].default_value[2] = 0.0 # 0.6
    
    # Water transparency
    Mat.node_tree.nodes["Water shader"].inputs[18].default_value = 0.85

#LinkWaves(Sea_Mat)
#SetSeaWaveParams(Sea_Mat)

################################################################################
# Putting in the water plane
################################################################################

def PutSeaPlane(Level=0, Location=(0,0,0.1)):

    bpy.ops.mesh.primitive_plane_add(size=SeaSize, location=(0, 0, 0))
        
    Seaplane=BU.Active()
    Seaplane.name="Seaplane"       
            
    WaterSub1 = Seaplane.modifiers.new(type='SUBSURF', name="WaterSub1")
    WaterSub1.render_levels = 5
    WaterSub1.levels = 2

    WaterSub2 = Seaplane.modifiers.new(type='SUBSURF', name="WaterSub2")
    Seaplane.cycles.use_adaptive_subdivision = True  
    Seaplane.cycles.dicing_rate = WaterDiceNr
    
    Seaplane.data.materials.append(M['Sea_Mat'])

    # Putting a bottom underneath it, to create darker water
    SeaBottomplane=BU.CopyObject(Seaplane,Linked=False) 
    SeaBottomplane.location=Location
    SeaBottomplane.location[2]=-2

    SeaBottomplane.name="SeaBottomplane"
    Seabottom_Mat=bpy.data.materials.new(name='Seabottom_Mat')
    Seabottom_Mat.use_nodes=True    
    Seabottom_Mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.02, 0.02, 0.02, 1)
    SeaBottomplane.data.materials[0]=Seabottom_Mat 

    return Seaplane, SeaBottomplane   

