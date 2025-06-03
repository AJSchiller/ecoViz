import bpy, bmesh, math
import numpy as np
from math import pi, sin

SK = bpy.data.texts['Sky.py'].as_module()
BU = bpy.data.texts['BlenderUtils.py'].as_module()

inf=1e6; on=1; off=0

MainDir = bpy.path.abspath("//")

O = bpy.data.objects

def ar(i): return np.array(i)
def Rand(i=1): return np.random.random(i)

PanoHD = off
Movie = off

bpy.context.scene.frame_set(980)

def Place(Obj, Name="",Location=(0,0,0), Rotation=(0,0,0), Scale=1.0, Instanced=False):
    if Instanced==True:
        Obj=BU.CopyObject(Obj)
        if Obj.name!="":
            Obj.name=Name
    Obj.location=Location
    Obj.rotation_euler=Rotation
    if Scale!=1.0:
        if len(Scale)>1:
            Obj.scale=Scale
        else:    
            Obj.scale=(Scale,Scale,Scale)
        print('### Scale adjusted')
    return Obj

def SetScene(CameraNr):
    
    EndTime=bpy.context.scene.frame_end
    Waterlevel = O['Seaplane'].location[2]
    
    Cam = bpy.context.scene.camera
    CamLoc = ar(Cam.location)
    CamRot = ar(Cam.rotation_euler)
 
#    bpy.context.scene.frame_start = 1
#    bpy.context.scene.frame_end = 250
       
    if Movie==on:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
    else:       
        bpy.context.scene.frame_start = bpy.context.scene.frame_current
        bpy.context.scene.frame_end = bpy.context.scene.frame_current
        
#    if CameraNr == 1:
#          
#    if CameraNr == 2:
#    
#    if CameraNr == 3:
#            
#    if CameraNr == 4:

#    if CameraNr == 5:         
                 
def SetPanos():
    for cam in bpy.data.cameras: 
        if cam.name[0:4]=="Pano":
            bpy.data.cameras.remove(cam)
        
#    Location1 = (-750, 1150, 12)       
#    Location2 = (-471, 746, 4) 
#    Location3 = ( 655, 434, 4)  

    # Making a new camera
    CurrentLocation = bpy.context.scene.camera.location
    bpy.ops.object.camera_add(location=CurrentLocation, rotation=(90/180*pi,0,0/180*pi))
    PanoCam=bpy.context.object 
    PanoCam.name="PanoCam"
    PanoCam.data.name="PanoCam"
    PanoCam.data.clip_end = 50000

    PanoCam.data.lens = 5

    PanoCam.data.type = 'PANO'
    PanoCam.data.cycles.panorama_type = 'EQUIRECTANGULAR'
    bpy.context.scene.render.image_settings.file_format = 'JPEG'

    bpy.context.scene.camera = PanoCam

    bpy.context.scene.frame_end = 1
    bpy.context.scene.frame_end = 1

    HighRes = on

    if HighRes==on:
        bpy.context.scene.render.resolution_x = 8192*(1+PanoHD)
        bpy.context.scene.render.resolution_y = 4096*(1+PanoHD)
        bpy.context.scene.cycles.samples = 256
    else:
        bpy.context.scene.render.resolution_x = 2160/2
        bpy.context.scene.render.resolution_y = 1080/2
        
    return PanoCam    

def MakePanos(Camera):
    
    Loc1 = (-750, 1150, 4)       
    Loc2 = (-471, 746, 4)
    Loc3 = ( 655, 434, 4) 
    
    Pos =  (Loc1,Loc2,Loc3)
    Time = (  1 ,  1 ,  1 )
    
    bpy.context.scene.camera = Camera
    
    for i in range(len(Pos)):
        Camera.location=Pos[i]
        bpy.context.scene.frame_set(Time[i])
        fname=MainDir+"Panos%02d.jpg" % i
        bpy.context.scene.render.filepath=fname
        print("Rendering file: "+fname)
        bpy.ops.render.render(write_still=True)

def Set3D():
    bpy.context.scene.render.use_multiview = True
    bpy.context.scene.render.views_format = 'STEREO_3D'

    bpy.context.scene.render.image_settings.views_format = 'STEREO_3D'

    #bpy.context.scene.display_mode = 'SIDEBYSIDE'

    bpy.context.object.data.stereo.convergence_mode = 'OFFAXIS'
    bpy.context.object.data.stereo.convergence_distance = 10

        
if __name__ == "__main__": 

    Camera=SetPanos() 
    #MakePanos(Camera)   
    #Set3D()    
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
        
    print('==> Finished switching to panoramic view');