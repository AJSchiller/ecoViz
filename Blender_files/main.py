import bpy, bmesh, sys, math, mathutils, random
from math import pi, sin, cos, tan, atan, asin, acos, sqrt, log
from mathutils import Matrix, Vector, Euler
import numpy as np
import io, os, time, platform
from os.path import join, isfile
from os import listdir
from contextlib import redirect_stdout

stdout = io.StringIO()

BU = bpy.data.texts['BlenderUtils.py'].as_module()
MT = bpy.data.texts['Materials.py'].as_module()
SK = bpy.data.texts['Sky.py'].as_module()
UV = bpy.data.texts['UV_Save.py'].as_module()
PA = bpy.data.texts['Panoramic.py'].as_module()
SE = bpy.data.texts['Sea.py'].as_module()

#if platform.system()=='Linux':
#    print(bpy.data.texts['main.py'].as_string())

inf=1e6; on=True; off=False

MainDir = bpy.path.abspath("//")
O = bpy.data.objects
C = bpy.data.collections
def ar(i): return np.array(i)
def Rand(i=1): return np.random.random(i)

################################################################################
# Loading Settings 
################################################################################

CameraNr             = 1

Series = 'RedBeach'

LandscapeSize        = 2048

Landscape_X          = 0
Landscape_Y          = 0
SoilDiceNr           = 4

Waterlevel           = 0.0
EndTime              = 250

PutParticles         = on
PutProps             = on
PutPeople            = off
PutMusselbed         = off
LinkWaves            = off
ViewParticles        = on

SetCamera            = off
SaveCams             = off
Animate              = off

HD                   = off    # Whether to render on 4K definition
F                    = 1      # Grass multiplyer for high-up shots
        
# --- Reading command line options ---------------------------------------------

argv = sys.argv

try:
    index = argv.index("Cam") + 1
except ValueError:
    index = 0
    print("No command line arguments")

if index>0:
    CameraNr = int(argv[index])
    print('Activating Camera', CameraNr)
                                                
################################################################################
# Main program
################################################################################

os.system('clear')
print("\n==> Starting on system %s.. \n" % platform.system())  

Timer = BU.TimerClass(Profiler=off)

bpy.context.scene.render.engine='CYCLES'

bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)      

# --- Cleaning previous iterations ---------------------------------------------

BU.DeleteAll(exclude=[])
BU.CleanAll()

# --- Setting a sky ------------------------------------------------------------

# SkyNr = 0 (Overdag) 1 (Avond) 2 (Na de Storm)
#SK.SetSky(RealSky=on, SkyNr=0, Z_Move=0.0, Angle = 90, Intensity=1)
if CameraNr>10:
    SK.SetSky(RealSky=on, SkyNr=2, Z_Move=0.02, Angle = 0, Intensity=0.5)    
else:
    SK.SetSky(RealSky=on, SkyNr=2, Z_Move=0.02, Angle = 0, Intensity=0.5)

################################################################################
# Rendering parameters
################################################################################

# Setting rendering parameters                              # Default values

bpy.context.scene.cycles.samples = 64                       # 128            
bpy.context.scene.cycles.preview_samples = 32               # 32
bpy.context.scene.cycles.use_animated_seed = True

bpy.context.scene.cycles.min_light_bounces = 1              # 0
bpy.context.scene.cycles.min_transparent_bounces = 1        # 0 
bpy.context.scene.cycles.light_sampling_threshold = 0.01    # 0.01

bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'
#bpy.context.scene.cycles.feature_set = 'SUPPORTED'

bpy.context.scene.cycles.max_bounces = 3                    # 25
bpy.context.scene.cycles.diffuse_bounces = 2                # 4
bpy.context.scene.cycles.glossy_bounces = 2                 # 4
bpy.context.scene.cycles.transparent_max_bounces = 32       # 8
bpy.context.scene.cycles.transmission_bounces = 8           # 12
bpy.context.scene.cycles.volume_bounces = 0                 # 0      
    
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 1
bpy.context.scene.frame_step = 1

print( (1+HD)*1920 )

bpy.context.scene.render.resolution_x = 1920*(1+HD)
bpy.context.scene.render.resolution_y = 1080*(1+HD)

bpy.context.scene.render.filepath = MainDir
bpy.context.scene.render.image_settings.file_format = 'JPEG' # PNG/JPEG 

#####################################################################################
# Loading the landscape data
#####################################################################################

# --- Loading the landscape profile from disk ----------------------------

Data = np.load(MainDir+"Maps/"+Series+"/FlatMap.npz",allow_pickle=True); 
Coords              = Data['Coords']
Loops               = Data['Loops']
Landscape_Elevation = Data['Elevation']
Landscape_Domain    = Data['Elevation']
Libraries           = Data['Libraries']
VegetationDatabase  = Data['VegetationDatabase']
Props               = Data['Props']
Cameras             = Data['Cameras']

LandscapeSize       = Data['LandscapeSize']
Landscape_Min       = Data['Landscape_Min']
Landscape_Max       = Data['Landscape_Max']
Grid_Size           = Data['Grid_Size']
    
Grid_Width  = Landscape_Domain.shape[0]
Grid_Height = Landscape_Domain.shape[1]

print('=> Data shape: (%d x %d)' % (Landscape_Domain.shape))
print('=> Finished loading data')

#####################################################################################
# Loading the materials
#####################################################################################

if Series in ['Zuilespolder']:
    Tidalflat_Mat=BU.ImportMaterial(filename='Freshwatermarsh_Materials.blend', Material='Multiflat_Mat')
    Tidalflat_Mat.name = "Tidalflat_Mat" 
    
    Maps = [
    {'Tex':'SaltmarshLocation', 'Map':'Flat_MarshHabitat.png'}, 
    {'Tex':'Freshwatermarsh Location', 'Map':'Flat_TidalflatHabitat.png'},
    {'Tex':'DykeRevetmentLocation', 'Map':'Flat_DykeRevetment.png'},
    {'Tex':'DykeLocation', 'Map':'Flat_DykeHabitat.png'}]
            
else:
    Tidalflat_Mat=BU.ImportMaterial(filename='Estuary_Realigned_Materials.blend', Material='Multiflat_Mat')
    Tidalflat_Mat.name = "Tidalflat_Mat" 
    
    Maps = [
    {'Tex':'SaltmarshLocation', 'Map':'Flat_MarshHabitat.png'}, 
    {'Tex':'MegarippleLocation', 'Map':'Flat_MegarippleHabitat.png'},
    {'Tex':'DykeRevetmentLocation', 'Map':'Flat_DykeRevetment.png'},
    {'Tex':'DykeLocation', 'Map':'Flat_DykeHabitat.png'}]

# relinking the Habitat Maps
for Map in Maps:
    Image = bpy.data.images.load(filepath = MainDir+'Maps/'+Series+'/'+Map['Map'], check_existing=True)
    Image.colorspace_settings.name = 'Non-Color'
    bpy.data.node_groups[Map['Tex']].nodes["Image Texture"].image=Image
    
Sea_Mat=BU.ImportMaterial(filename='Wavefield/Wavefield.blend', Material='Ocean_Mat')
Sea_Mat.name="Sea_Mat"   

SE.Link_Waves(Sea_Mat)
SE.SetSeaWaveParams(Sea_Mat)

Timer.Report('loading materials') 
                              
################################################################################
# A function rotating the objects for emission in a particle system
################################################################################

def ParticleRotation(Group):
    Objects=Group.objects
    for obj in Objects:
        loc=obj.location
        BU.ApplyRotationScale(obj,loc=(0,0,0),rot=(-0.5*pi,0,0))    
        obj.rotation_euler=(0.5*pi,0,0)
        obj.location=loc      

################################################################################
# Putting in the tidal flat
################################################################################

def SetMesh(Name, Coords, Loops):

    vertices=Coords.flatten()
    vertex_index = Loops.flatten()

    num_vertices = Coords.shape[0]
    num_loops = vertex_index.shape[0]//4
    num_vertex_indices = vertex_index.shape[0]

    loop_start = np.linspace(0,num_loops-1,num_loops, np.int32)*4
    loop_total = np.ones(num_loops, dtype=np.int32)*4

    mesh = bpy.data.meshes.new(name=Name)

    # Setting up a mesh using the data
    mesh.vertices.add(num_vertices)
    mesh.vertices.foreach_set("co", vertices)

    mesh.loops.add(num_vertex_indices)
    mesh.loops.foreach_set("vertex_index", vertex_index)

    mesh.polygons.add(num_loops)
    mesh.polygons.foreach_set("loop_start", loop_start)
    mesh.polygons.foreach_set("loop_total", loop_total)

    # Updating the mesh
    mesh.update()
    mesh.validate()
    mesh.name=Name
    
    return mesh

def PutBottom(Name,Elevation,LandscapeSize, Z=-0.5):
    
    (Grid_Width,Grid_Height) = Elevation.shape

    BaseMeshData=np.zeros((Grid_Width*Grid_Height,3))
    BaseMeshData[:,0:2]=Coords
    BaseMeshData[:,2]=Landscape_Elevation.flatten()

    StartMesh = SetMesh('StartMesh', BaseMeshData, Loops)
    Landscape = bpy.data.objects.new(Name, StartMesh)
    bpy.context.scene.collection.objects.link(Landscape)
    
    Landscape.location[2]=Z
    
    Timer.Report('building meshes')

    # --- Landscape material ----------------------------------------------

    MT.ScaleUV(Landscape, Scale=10, Rotate=False)

    TidalFlatMat=bpy.data.materials["Tidalflat_Mat"]
    Landscape.data.materials.append(TidalFlatMat)
    #TidalFlatMat.node_tree.nodes["Mapping"].inputs[3].default_value[2] = 4
    #TidalFlatMat.node_tree.nodes["HeightMultiplyer"].inputs[1].default_value = 0.3
    #bpy.data.node_groups["BaseTidalflat"].nodes["HeightMultiplyer"].inputs[1].default_value = 0.3
    
    TidalFlatMat.cycles.displacement_method='BOTH'
    
    BU.Smooth(Landscape)  
    
    Timer.Report('adding landscape material')
    
    # --- Adding a subdivision --------------------------------------------

    Adaptive=on
    
    if Adaptive==on:
        #bpy.ops.object.modifier_add(type='SUBSURF')
        Landscape.modifiers.new("Subdivision", 'SUBSURF')    
        Landscape.cycles.use_adaptive_subdivision = True
        Landscape.cycles.dicing_rate = SoilDiceNr
        Landscape.modifiers["Subdivision"].levels = 1
    else:
        #bpy.ops.object.modifier_add(type='SUBSURF')
        Landscape.modifiers.new("Subdivision", 'SUBSURF') 
        Landscape.cycles.use_adaptive_subdivision = False
        Landscape.modifiers["Subdivision"].render_levels = 4*512/Grid_Width
        Landscape.modifiers["Subdivision"].levels = 1
        
    Timer.Report('building Landscape')      
    
    return Landscape  
    
def PutBottomNew(Name,Elevation,LandscapeSize, Z=-0.5):

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=512-1, y_subdivisions=512-1, 
        size=LandscapeSize, location = (0,0,Z))
    Landscape = BU.Active('Landscape')
    
    Timer.Report('building meshes')

    # --- Landscape material ----------------------------------------------

    #MT.ScaleUV(Landscape, Scale=10, Rotate=False)
    BU.EditMode()
    bpy.ops.uv.cube_project(scale_to_bounds=True)
    BU.ObjectMode()

    TidalFlatMat=bpy.data.materials["Tidalflat_Mat"]
    Landscape.data.materials.append(TidalFlatMat)
    
    TidalFlatMat.cycles.displacement_method='BOTH'
    
    BU.Smooth(Landscape)  
    
    Timer.Report('adding landscape material')
    
    # --- Adding a subdivision --------------------------------------------

    Adaptive=on
    
    if Adaptive==on:
        #bpy.ops.object.modifier_add(type='SUBSURF')
        Landscape.modifiers.new("Subdivision", 'SUBSURF')    
        Landscape.cycles.use_adaptive_subdivision = True
        Landscape.cycles.dicing_rate = SoilDiceNr
        Landscape.modifiers["Subdivision"].levels = 1
    else:
        #bpy.ops.object.modifier_add(type='SUBSURF')
        Landscape.modifiers.new("Subdivision", 'SUBSURF') 
        Landscape.cycles.use_adaptive_subdivision = False
        Landscape.modifiers["Subdivision"].render_levels = 4*512/Grid_Width
        Landscape.modifiers["Subdivision"].levels = 1
        
    Timer.Report('building Landscape')  
    
#    tex=bpy.data.textures.new('Landscape', type = 'IMAGE')
#    img = bpy.data.images.load(MainDir+'Maps/'+Series+'/'+'Flat_LandscapeMap.png')
#    img.colorspace_settings.name = 'Linear'
#    tex.image = img
    
#    Landscape.modifiers.new("Landscape Displace", 'DISPLACE')  
#    bpy.context.object.modifiers["Landscape Displace"].direction = 'RGB_TO_XYZ'
#    bpy.context.object.modifiers["Landscape Displace"].texture = tex
#    bpy.context.object.modifiers["Landscape Displace"].strength = 100*Landscape_Max - Landscape_Min
#    bpy.context.object.modifiers["Landscape Displace"].mid_level = -Landscape_Min/(Landscape_Max - Landscape_Min)
#    
#    print(Landscape_Max,Landscape_Min)
 
    return Landscape  

# --- Bump displacement ----------------------------------------------
    
def PutBumps(Landscape, ImageFile, Name, BumpUVMap, Strength=1, Mid=0.5):

    BU.SelectObject(Landscape)
    
    print(MainDir)
    MapImage = bpy.data.images.load(filepath = MainDir+"Maps/"+Series+"/"+ImageFile)
    MapImage.colorspace_settings.name = 'Linear'

    tex=bpy.data.textures.new(Name+'_Tex', type = 'IMAGE')
    tex.image = MapImage
    
    Mod = Landscape.modifiers.new('Displace'+'_'+ImageFile, 'DISPLACE') 
    Mod.texture = tex
    Mod.strength = Strength
    Mod.mid_level = Mid
    Mod.texture_coords = 'UV'
    Mod.uv_layer = BumpUVMap.name

    Timer.Report('Bumps')

def SetLandscapeUV(Landscape):
    
    BumpUVMap=Landscape.data.uv_layers.new(name="Bump_UVMap")
    Landscape.data.uv_layers.active=BumpUVMap
    BU.EditMode()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.1)
    BU.ObjectMode()
    
    return BumpUVMap

# --- Set Vertex Paint ----------------------------------------------

def SetVertexPaint(Landscape,Density,Label):
    
    DensityFlat=Density.flatten()
    
    LandscapeVerts = Landscape.data.vertices
    if Landscape.vertex_groups.get(Label) is None:
        Landscape.vertex_groups.new(name=Label)
    Objects = Landscape.vertex_groups[Label]

    for i in LandscapeVerts:
        Objects.add([i.index], DensityFlat[i.index], "REPLACE")
            
    return Landscape.vertex_groups[Label]

# --- Distance Weighing ----------------------------------------------

def DistWeight(Half=100, End=0.05):
    
    CamCoords=bpy.context.scene.camera.location

    x = np.linspace(-(LandscapeSize)/2, (LandscapeSize)/2, Grid_Width)
    y = np.linspace(-(LandscapeSize)/2, (LandscapeSize)/2, Grid_Height)
    xv, yv = np.meshgrid(x, y)
    Dist=np.sqrt((xv-CamCoords[0])**2+(yv+CamCoords[1])**2+CamCoords[2]**2)

    Weight=(1-End)*Half/(Dist+Half)+End
        
    return np.rot90(Weight.T,1).flatten()
 
##########################################################################
# Setting up the particle systems
#   Here the particle systems are set up that distribute the vegetation
#   over the area, based on a "Vertex" value set by the loaded data 
##########################################################################

def PutObjects(Par):  

    dX2 = LandscapeSize*LandscapeSize/Grid_Width/Grid_Height
    # Reorientkokkeling the data 
    #Data = np.rot90(Par['Vertex'].transpose(), k=2).flatten()
    Data = Par['Vertex']
    
    if Par['DampVertex']:
        SetVertexPaint(Landscape, Data*DistField, Par['Name']+"-Vertex")    
        Number = int(Par['Density']*np.sum(Data*DistField)*dX2/Par['Kids'])
    else:
        SetVertexPaint(Landscape, Data, Par['Name']+"-Vertex")
        Number = int(Par['Density']*np.sum(Data)*dX2/Par['Kids'])
            
    # Building the landscape with the particle system
    PS=Landscape.modifiers.new(Par['Name'], 'PARTICLE_SYSTEM')
    Particles=Landscape.particle_systems[Par['Name']]      
         
    Particles.settings.type = 'HAIR'
    Particles.settings.use_advanced_hair = True
        
    Particles.settings.count = Number   
    Particles.settings.use_modifier_stack = True

    Particles.settings.render_type = 'COLLECTION'
    Particles.settings.instance_collection = C[Par['Collection']]    

    Particles.settings.userjit = 1
    Particles.settings.use_rotations = True
    Particles.settings.rotation_mode = 'NOR_TAN'
    Particles.settings.particle_size = 0.25
    Particles.settings.size_random = 0.3
    
    Particles.settings.rotation_factor_random = 0.015
    Particles.settings.phase_factor = 0
    Particles.settings.phase_factor_random = 0.5

    Particles.name = "Particles-"+Par['Name']       
    Particles.settings.name = "Particlesettings-"+Par['Name'] 
    Particles.settings.distribution = 'RAND'
    Particles.settings.use_even_distribution = False
    Particles.settings.jitter_factor = 0    

    Particles.vertex_group_density = Par['Name']+"-Vertex"  

    if Par['TexFile'] is not "":

        tex=bpy.data.textures.new(Par['TexFile'], type = 'IMAGE')
        img = bpy.data.images.load(MainDir+'Maps/'+Series+'/'+Par['TexFile'])
        tex.image = img

        Particles.settings.active_texture=tex
        Particles.settings.texture_slots[0].use_map_time = False
        Particles.settings.texture_slots[0].use_map_density = True
        Particles.settings.texture_slots[0].use_map_size = True
        Particles.settings.texture_slots[0].density_factor = 2
        Particles.settings.texture_slots[0].texture_coords = 'UV'

    # Setting up children    
    if Par['Kids']>0:
        Particles.settings.child_type = 'INTERPOLATED'
        Particles.settings.child_nbr = 1
        Particles.settings.rendered_child_count = Par['Kids']
        Particles.settings.child_length = 5    
        Particles.settings.child_radius = 2.5
        Particles.settings.roughness_2 = 1    
     
    Timer.Report('%d %s Particles' % (Number,Par['Name']) )   
        
    return Particles           
      
##########################################################################
# Setting up the camera
##########################################################################

def SetCamera(Cam, ClipEnd=10000):
    bpy.ops.object.camera_add(location=Cam['Loc'], rotation=Cam['Rot'] )
    Camera=BU.Active(Cam['Name'])
    Camera.data.name=Cam['Name']
    if 'Lens' in Cam:
        Camera.data.lens = Cam['Lens']
    else:
        Camera.data.lens = 30
    Camera.data.clip_end = ClipEnd
    return Camera

def CameraSetup(ActiveCam = 2, Save=off):
    
    for Cam in Cameras:
        SetCamera(Cam)
    
    # --- Finishing camera setup -----------------------------------------
               
    bpy.context.scene.camera = O["Camera %02d" % ActiveCam]    
    
    # --- Moving the camera to the 'Cameras' folder 
    Set = [o for o in O if o.name[0:6]=='Camera']
    BU.Move_to_Collection(Set,'Cameras')  
    
    Timer.Report('activating camera %02d' % ActiveCam)
    
    # --- Writing the camera positions into a file, used to make a map ----
    if SaveCams==on:
        file = open(MainDir + "Cam_Positions.txt", "w")
        CamSet=[o for o in O if o.name.startswith('Camera')]
        print(CamSet)
        for o in CamSet:
            L=o.location
            file.write("%s, %1.0f, %1.0f\n" % (o.name, L[0], L[1]))
        file.close() #This close() is important
        Stop()
        
    return bpy.context.scene.camera   
    
##########################################################################
# Setting up the landscape
#   This is where the actual work starts
##########################################################################

CameraSetup(ActiveCam = CameraNr, Save=off)

# --- Setting up a distance field based on camera position ---------------
CamHeight = bpy.context.scene.camera.location[2]
DistField = DistWeight(Half=CamHeight*5, End=0)  

#filepath = "Maps/"+Series+"/"+Series+"_Library.blend"

Seaplane, SeaBottomplane = SE.PutSeaPlane(Level=Waterlevel, Location=(-150,-85,Waterlevel))

Timer.Report('building the Seaplane and Bottom plane')

Landscape = PutBottomNew('Landscape', Landscape_Elevation, LandscapeSize=LandscapeSize, Z=0)

#DistVertex = SetVertexPaint(Landscape, DistField, "DistVertex")    
    
#BumpUVMap = SetLandscapeUV(Landscape)

UVMap = bpy.data.meshes['Grid'].uv_layers["UVMap"]

PutBumps(Landscape, ImageFile="Flat_LandscapeMap.png", Name="Landscape", 
         BumpUVMap=UVMap, 
         Strength= Landscape_Max - Landscape_Min,
         Mid = -Landscape_Min/(Landscape_Max - Landscape_Min) )

#if PutMusselbed==on:
#    PutBumps(Landscape, ImageFile="Flat_Mussels.png", Name="Mussels", 
#         BumpUVMap=UVMap, Strength=0.25, Mid=0)   

## write selected objects and their data to a blend file
#data_blocks = set([O['Seaplane'],O['SeaBottomplane'],O['Landscape']]) # O['Tidalflat']
#bpy.data.libraries.write(MainDir+filepath, data_blocks)

Timer.Report('building Landscape objects')
    
#if BuildLandscape==on:
#   
#    Seaplane, SeaBottomplane = SE.PutSeaPlane(Level=Waterlevel, Location=(-150,-85,Waterlevel))
#    Timer.Report('building the Seaplane and Bottom plane')

#    Landscape = PutBottomNew('Landscape', Landscape_Elevation, LandscapeSize=LandscapeSize, Z=0)

#    #DistVertex = SetVertexPaint(Landscape, DistField, "DistVertex")    
#        
#    #BumpUVMap = SetLandscapeUV(Landscape)
#    
#    UVMap = bpy.data.meshes['Grid'].uv_layers["UVMap"]
#    
#    PutBumps(Landscape, ImageFile="Flat_LandscapeMap.png", Name="Landscape", 
#             BumpUVMap=UVMap, 
#             Strength= Landscape_Max - Landscape_Min,
#             Mid = -Landscape_Min/(Landscape_Max - Landscape_Min) )
#    stop
#    if PutMusselbed==on:
#        PutBumps(Landscape, ImageFile="Flat_Mussels.png", Name="Mussels", 
#             BumpUVMap=UVMap, Strength=0.25, Mid=0)   
#    
#    # write selected objects and their data to a blend file
#    data_blocks = set([O['Seaplane'],O['SeaBottomplane'],O['Landscape']]) # O['Tidalflat']
#    bpy.data.libraries.write(MainDir+filepath, data_blocks)
#    
#    Timer.Report('building Landscape objects')

#else:
#    Seaplane = BU.ImportObjects(filepath, 'Seaplane', Zpos=Waterlevel )
#    SeaBottomplane = BU.ImportObjects(filepath, 'SeaBottomplane', Zpos=Waterlevel-2)
#    Landscape = BU.ImportObjects(filepath, 'Landscape', Zpos=0)    
#    
#    Timer.Report('loaded Landscape objects from library')  
   
# --- Ensuring some of the landscape and seaplace properties are set correctly

Landscape.data.materials[0]=Tidalflat_Mat
Tidalflat_Mat.cycles.displacement_method='BOTH'

Seaplane.data.materials[0]=Sea_Mat
Seaplane.location[2]=Waterlevel
Seaplane.active_material.diffuse_color = (0.006, 0.75, 0.75, 1)

#UV.LoadUVs(Landscape,UVFolder=MainDir + '/UVMaps/')


# --- Making the wave ripples move ----------------------------------------

Freq=4
Loc=ar(O['WaveTextureObject'].location)
    
for i in range(EndTime):
    f=i/250
    O['WaveTextureObject'].location = Loc+ar((0,f*10+0.2*sin(Freq*f*2*pi),0))
    O['WaveTextureObject'].keyframe_insert('location',frame=i+1)

# --- Relinking the Salt marsh topography image map -----------------------        

#MapImage = bpy.data.images.load(filepath = MainDir+"Maps/"+Series+"/"+"Flat_Saltmarsh.png")
#tex=bpy.data.textures.new('Saltmarsh_Map', type = 'IMAGE')
#tex.image = MapImage   
#Landscape.modifiers['Displace_Flat_Saltmarsh.png'].texture = tex

#if PutMusselbed==on:
#    MapImage = bpy.data.images.load(filepath = MainDir+"Maps/"+Series+"/"+"Flat_Mussels.png")
#    tex=bpy.data.textures.new('MusselMap', type = 'IMAGE')
#    tex.image = MapImage   
#    Landscape.modifiers['Displace_Flat_Mussels.png'].texture = tex
        
BU.Move_to_Collection([Landscape,Seaplane,SeaBottomplane,O['Sun'],O['WaveTextureObject']], 'Landscape')

##############################################################################
# Setting up the vegetation, using the particle system
############################################################################## 

if PutParticles==on:                             
      
    # --- Loading the particle libraries ---------------------------------

    for i,Library in enumerate(Libraries):
        Group = BU.ImportCollection( 
            filename=Library['filename'], 
            Collection=Library['Collection'])
        BU.Move_to_Collection([Group],'Particles')
     
    # --- Placing the particles ------------------------------------------

    for Par in VegetationDatabase:
        PutObjects(Par)
    
##############################################################################
# Loading props 
##############################################################################
    
if PutProps==on:
    Set=[]  
    for P in Props:
         
        # --- If the given prop refers to an Object: 
        if P['type']=='Object':
            Prop = BU.ImportObjects(P['file'], P['name'], Zpos=0)    
            BU.Place(Prop, Location = P['loc'], Rotation = P['rot'],
                Collection='Props', Instanced=P['inst'])
        # --- If the given prop refers to a Collection:        
        if P['type']=='Collection':
            Prop = BU.ImportCollection(P['file'], P['name'], Instanced=P['inst'], Linked=True)    
            # If the collection is instanced, then it is placed on location
            if P['inst']==True:  
                BU.Place(Prop, Location = P['loc'], Rotation = P['rot'],Instanced=False, Collection='Props') 
            # Else also, but differently
            else:
                if 'Place' in P:
                    for L in P['Place']:
                        if not L['name'] in Set:
                            BU.Place(O[L['name']], Location = L['loc'], Rotation = L['rot'], Instanced = False) 
                            Set.append(L['name'])
                        else:
                            BU.Place(O[L['name']], L['NewName'], Location = L['loc'], Rotation = L['rot'], Instanced = True) 
                                
        Timer.Report(P['name'])    
           
##########################################################################
# Series specific settings
##########################################################################

if Series == 'RedBeach':
    print('==> Implementing Redbeach settings')
    bpy.data.particles["Particlesettings-Marsh_Spartina"].particle_size = 1
    bpy.data.particles["Particlesettings-Marsh_Phragmites"].phase_factor_random = 0.1  

##########################################################################
# Final setup
##########################################################################

# Removing all suns that were loaded accidentely via the append command
Suns = [o for o in O if o.name.startswith('Sun')]
for Sun in Suns:
    if Sun.users_collection[0].name != 'Landscape':
        O.remove(Sun)

#BU.SelectObject(bpy.context.scene.camera)
BU.SelectObject(Landscape)

# Making sure all particle systems are not visible
for m in Landscape.modifiers:
    m.show_viewport = False

# Apart from the landscape displacement
Landscape.modifiers["Displace_Flat_LandscapeMap.png"].show_viewport = True

bpy.context.object.modifiers["Subdivision"].show_viewport = True
bpy.context.object.modifiers["Subdivision"].show_in_editmode = True

# EndTime for movie sequences set here, to avoid problems during errors 
bpy.context.scene.frame_end = EndTime 
bpy.context.scene.frame_set(1)
 
PA.SetScene(CameraNr=CameraNr)    

if SetCamera==on:
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            bpy.ops.outliner.expanded_toggle()
    
if platform.system()=='Linux': 
    BU.Run_On_GPU(Timer.start_time)   
 
O.remove(O['TexturePlacement'])
#for t in bpy.data.texts: if t.name.startswith('Polii'): bpy.data.texts.remove(t)

for t in bpy.data.texts: 
    if t.name.startswith('Polii'):
        bpy.data.texts.remove(t)
          
BU.StripMaterials()

BU.Purge(); BU.Purge()

Panos=off

if Panos==on:
    PA = bpy.data.texts['Panoramic.py'].as_module()
    Camera = PA.SetPanos() 
    #PA.Set3D(Camera)
    PA.MakePanos(Camera)     
    
bpy.ops.file.make_paths_relative()

print()        
Timer.Report('entire project')    

if sys.platform == "darwin":
    os.system("say -v Xander En nu stoppen we er mee!")  
    