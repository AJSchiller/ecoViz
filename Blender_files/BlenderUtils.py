import bpy, bmesh
from mathutils import Vector
from math import radians
from mathutils import Euler, Matrix
import numpy as np
import time

MainDir = bpy.path.abspath("//")
O=bpy.data.objects
C=bpy.data.collections

on  = True
off = False

def __init__():
    print('BlenderUtils loaded')

##########################################################################
# Profiling procedures
#    These functions help analysing the buildup of the scene
#    by counting the total memory usage, and reporting
##########################################################################

def TriCount(self):
        tris_count = 0
        for o in bpy.context.scene.objects:
            if o.type == 'MESH' and not o.hide_get():
                for p in o.data.polygons:
                    if len(p.vertices) > 3:
                        tris_count = tris_count + len(p.vertices) - 2
                    else:
                        tris_count = tris_count +1                 
        return tris_count
    
class TimerClass:

    def __init__(self, Profiler=off):
        self.start_time = time.time()
        self.profiler = Profiler

    def add_trick(self, trick):
        self.tricks.append(trick)
        
    def Report(self, Name, GiveMem=off):
        if GiveMem:
            tri_count = TriCount()
            print('=> Finished %s at %1.1f (s), Tri Count: %d' % 
                    (Name, ( time.time()-self.start_time), tri_count ))
        else:
            print('=> Finished %s at %1.1f (s)' % (Name, ( time.time()-self.start_time) ))  
            
##########################################################################
# Placing an object 
#   This is a general function that provides an efficient interface
#   To place a specific object
##########################################################################

def Place(Obj, Name="", Location=(0,0,0), Rotation=(0,0,0), Scale=1, Instanced=False, Collection=""):
    if Instanced==True:
        Obj=CopyObject(Obj)
        if Obj.name != "":
            Obj.name = Name
    Obj.location = Location
    Obj.rotation_euler = Rotation
    if Scale != 1:
        Obj.scale = (Scale, Scale, Scale)
        
    if Collection != "":
         Move_to_Collection([Obj], Collection)
#        if isinstance(Collection, str):
#            Col=C[Collection]
#        else:
#            Col=Collection      
#        BU.Move_to_Collection([Obj],Col)        
        
    return Obj

# --- Go into edit mode -----------------------------------------------

def EditMode():
    if len([obj.name for obj in bpy.data.objects]) > 0:
        bpy.ops.object.mode_set(mode='EDIT')

# --- Go into object mode ---------------------------------------------

def ObjectMode():
    if len([obj.name for obj in bpy.data.objects]) > 0:
        bpy.ops.object.mode_set(mode='OBJECT')
 
# --- Getting the active object ---------------------------------------
    
def Active(Name=""):
    obj = bpy.context.object
    if Name != "":
        obj.name = Name
    return obj   

# --- Short for np.array ----------------------------------------------

def ar(Array):
    return np.array(Array)     

# --- Check if object exists ---------------------------------------
    
def Exist(Obj):
    return bpy.data.objects.get(Obj) != None

# --- Apply given rotation and scale ----------------------------------

def ApplyRotationScale(ob, loc=(0,0,0), rot=(0,0,0), scl=(1,1,1)):

    euler = Euler(rot, 'XYZ')

    location, rotation, scale = ob.matrix_world.decompose()

    smat = Matrix()
    for i in range(3):
        smat[i][i] = scale[i] * scl[i]

    mat = Matrix.Translation(loc) @ euler.to_matrix().to_4x4() @ smat

    ob.data.transform(mat)

    ob.matrix_world = Matrix()
    
# --- Set shading to smooth (no ops) ----------------------------------

def Smooth(Obj):

    for poly in Obj.data.polygons:
        poly.use_smooth = True    
    
# --- Set active object -----------------------------------------------      
        
def SelectObject(obj, add=False ):
    if add == False:
        bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj                

# --- Delete all objects except those on the list ---------------------

def DeleteAll(exclude):  
    for obj in bpy.data.objects: 
        if not any(obj.name == Xname for Xname in exclude):
            bpy.data.objects.remove(obj)
    for ca in bpy.data.cameras:
        bpy.data.cameras.remove(ca)
    for cu in bpy.data.curves:
        bpy.data.curves.remove(cu)             
    for ma in bpy.data.materials:
        if not any(ma.name == Xname for Xname in exclude):
            bpy.data.materials.remove(ma)  
    #for im in bpy.data.images:
    #   bpy.data.images.remove(im)      
    for cl in bpy.data.collections: 
        bpy.data.collections.remove(cl)          
          
# --- Clean out all objects ------------------------------------------

def CleanOrphenData():
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)     
    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)      
    for block in bpy.data.objects:
        if block.users == 0:
            bpy.data.objects.remove(block)  
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block) 
    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block) 
    for block in bpy.data.collections: 
        if block.users == 0:
            bpy.data.collections.remove(block)    
    for block in bpy.data.node_groups:
        if block.users == 0:
            bpy.data.node_groups.remove(block)
    for block in bpy.data.actions:
        if block.users == 0:
            bpy.data.actions.remove(block)
    for block in bpy.data.particles:
        if block.users == 0:
            bpy.data.particles.remove(block)                                                                

def CleanAll():
    for item in bpy.data.meshes:        
        bpy.data.meshes.remove(item)
    for item in bpy.data.materials:
        bpy.data.materials.remove(item)
    for item in bpy.data.textures:
        bpy.data.textures.remove(item)
    for item in bpy.data.images:
        bpy.data.images.remove(item)     
    for item in bpy.data.lights:
        bpy.data.lights.remove(item)      
    for item in bpy.data.objects:
        bpy.data.objects.remove(item)  
    for item in bpy.data.materials:
        bpy.data.materials.remove(item) 
    for item in bpy.data.curves:
        bpy.data.curves.remove(item) 
    for item in bpy.data.collections: 
        bpy.data.collections.remove(item)    
    for item in bpy.data.node_groups:
        bpy.data.node_groups.remove(item)
    for item in bpy.data.actions:
        bpy.data.actions.remove(item)
    for item in bpy.data.particles:
        bpy.data.particles.remove(item)   
    #for item in bpy.data.libraries:
    #    bpy.data.libraries.remove(item)    
            
# [‘MESH’, ‘CURVE’, ‘SURFACE’, ‘META’, ‘FONT’, ‘ARMATURE’, ‘LATTICE’, 
# ‘EMPTY’, ‘CAMERA’, ‘LAMP’, ‘SPEAKER’]                                            

def StripMaterials():
    Meshes = [o for o in O if o.type=='MESH'] 

    for o in Meshes:
        for i,m in enumerate(o.data.materials): 
            if m != None:
                TotalName = m.name.split('.')
                if len(TotalName)>1:
                   if TotalName[0] in bpy.data.materials:
                       o.data.materials[i] = bpy.data.materials[TotalName[0]]

def Purge():
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
                        
# --- Copy Object -----------------------------------------------------
    
def CopyObject(Old_obj, Name="Copied_Object", Linked=on):
    New_obj=Old_obj.copy()
    New_obj.name=Name
    # Copying mesh if needed
    if Linked==off:
        New_obj.data=Old_obj.data.copy()
        New_obj.data.name=Name
    # Finishing up    
    New_obj.animation_data_clear()
    bpy.context.collection.objects.link(New_obj)
    return New_obj

# --- Copy and move ---------------------------------------------------

def Copy_n_Move(Old_obj, Name="Copied_Object", Move=(0,0,0), Linked=on):
    New_obj=CopyObject(Old_obj,Name,Linked)
    New_obj.location=np.array(New_obj.location)+np.array(Move)
    return New_obj

# --- Delete a specific python object ---------------------------------
    
def DeleteObject(obj):
    O.remove(obj)  
    
# --- Remove a named object from blender space ------------------------   
    
def RemoveObject(ObjectName="Dum"):
    if not bpy.data.objects.get(ObjectName) == None:
        O.remove(O[ObjectName])      
    
# --- Make an object the parent ---------------------------------------

def MakeParent(Parent,Child):
#    SelectObject(Parent)
#    Child.select_set(True)
#    bpy.ops.object.parent_set(type='OBJECT')
    Child.parent=Parent
    Child.matrix_parent_inverse = Parent.matrix_world.inverted()

def MakeFamily(Parent, Family):
    for C in Family:
        MakeParent(Parent=Parent, Child=C)

################################################################################
# Collection functions
################################################################################

# --- Finding the layer collection connection to a specific collection 

def FindLayerCollection(layerColl, collName):
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = FindLayerCollection(layer, collName)
        if found:
            return found

# --- Make a specific collection the active (layer) collection

def SetActiveCollection(Name):
    layer_collection = bpy.context.view_layer.layer_collection
    layerColl = FindLayerCollection(layer_collection, Name)
    bpy.context.view_layer.active_layer_collection = layerColl
        
# --- Reset the active collection to the base scene collection       
        
def ResetActiveCollection():
    scene_collection = bpy.context.view_layer.layer_collection
    bpy.context.view_layer.active_layer_collection = scene_collection  

# --- Moving objects into new or existing collection 

def Move_to_Collection(objs,Collection,Merge=False):

    # Set collection
    if isinstance(Collection, str):
        if Collection in C:
            Col=C[Collection]
        else:
            Col= bpy.data.collections.new(name = Collection)
            bpy.context.scene.collection.children.link(Col)  
    else:
        Col=Collection          
           
    # Link the objects to the Collection           
    for obj in objs:
        #print('Moving: %s, type: %s' % (obj.name, type(obj)) )
        found = False
        if type(obj) == bpy.types.Collection:    
            if not Merge:    
                if obj.name in bpy.context.scene.collection.children:    
                    bpy.context.scene.collection.children.unlink(obj)  
                else:
                    for c in C:
                        if obj.name in c.children:    
                            c.children.unlink(obj)                             
            Col.children.link(obj)                
        else:
            if not Merge:  
                PrevCol=obj.users_collection[0]                      
                PrevCol.objects.unlink(obj)
            Col.objects.link(obj)
    return Col 

# --- Create a new collection and making it the active layer collection

def CreateCollection(Name, Parent="", Active=True):
    myColl = bpy.data.collections.new(Name)
    bpy.context.scene.collection.children.link(myColl)  
    
    if not Parent=="":
        Move_to_Collection([myColl],C[Parent])
    
    SetActiveCollection(Name)    
        
    return myColl  
    
#--- Joining two projects ---------------------------------------------    
    
def JoinObjects(obj1,obj2):
    objs=[obj1,obj2]      
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs: obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.join()

    return Active()

# --- Joining a group objs of objects into a new one ------------------

def JoinAll(objs, NewName):
    # objectnames : List of object names to be saved
    # fullName : Full path of where to save to 
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
  
    # Select those in the objectname list
    for obj in objs: obj.select_set(True)
 
    bpy.context.view_layer.objects.active=objs[0]
    
    bpy.ops.object.join()
    
    new_obj=Active(NewName)
    new_obj.data.name=NewName
    
    return new_obj    

# --- Make a bar -----------------------------------------------------

def Cube(Name="Cube", location=(0,0,0),rotation=(0,0,0),dimensions=(1,1,1), align='Bottom'):
    bpy.ops.object.select_all(action='DESELECT')   
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj=Active(Name=Name)
    obj.data.name=Name
    obj.dimensions=dimensions
    if align=='Bottom':
        bpy.ops.object.mode_set(mode='EDIT')        
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.translate(value=(0, 0, dimensions[2]/2))
        bpy.ops.object.mode_set(mode='OBJECT')   
    obj.rotation_euler=rotation     
    bpy.ops.object.transform_apply(scale=True, rotation=True, location=False)
    return obj

# --- Cutter ---------------------------------------------------------------

def CutObject(Obj,Cutter,Remove=False):
    SelectObject(Obj)
    Obj.modifiers.new(name='Cutter',type='BOOLEAN')
    Obj.modifiers['Cutter'].object = Cutter
    Obj.modifiers['Cutter'].solver = 'EXACT' # 'FAST'
    Obj.modifiers['Cutter'].operation = 'DIFFERENCE'
    bpy.ops.object.modifier_apply(modifier='Cutter')  
    if Remove: O.remove(Cutter)
    
##########################################################################
# Activate GPU rendering 
##########################################################################

def Run_On_GPU(StartTime):
    prefs = bpy.context.preferences
    prefs.addons['cycles'].preferences.get_devices()
    cprefs = prefs.addons['cycles'].preferences
    #print(cprefs)

    # Attempt to set GPU device types if available
    for compute_device_type in ('CUDA', 'OPENCL', 'NONE'):
        try:
            cprefs.compute_device_type = compute_device_type
            break
        except TypeError:
            pass

    # Enable all GPU devices, skip CPU devices
    for device in cprefs.devices:
        print('=> Activating', device.name, 'at ', time.time() - StartTime)
        if 'CPU' in device.name:
            continue
        device.use = True

    scene = bpy.context.scene
    scene.cycles.device = 'GPU'

    print('\n########### CYCLES device:', scene.cycles.device, ' #####################\n')

# --- Saving to an FBX file -------------------------------------

def Save_all_to_fbx(objectnames, FullName):
    # objectnames : List of object names to be saved
    # fullName : Full path of where to save to 
    
    # Deselect all objects
    for obj in bpy.data.objects: obj.select_set(False)
  
    # Select those in the objectname list
    for objn in objectnames: bpy.data.objects[objn].select_set(True)
    
    bpy.ops.export_scene.fbx(check_existing=False, 
                             filepath=FullName,
                             use_selection=True,
                             object_types={'MESH'},
                             path_mode='RELATIVE')
    
# --- ImportObjects: loading a group of objects as a collection ----    
          
def ImportObjects(filename, Objects, Collection = bpy.data.scenes['Scene'].collection, Zpos=-3):

    if isinstance(Collection, str):
        if Collection in C:
            Col=C[Collection] 
        else:
            Col = bpy.data.collections.new(name = Collection)
            bpy.context.scene.collection.children.link(Col)  
    else:
        Col=Collection
    
    if isinstance(Objects, str):
        Objects=[Objects]
                
    with bpy.data.libraries.load(MainDir + filename) as (data_from, data_to): 
        data_to.objects = [name for name in data_from.objects if name.startswith(tuple(Objects))]               
    
    for obj in data_to.objects:
        if obj is not None:
           Col.objects.link(obj)    
        
#    if Collection!=bpy.data.scenes['Scene'].collecffion:
#        bpy.context.scene.collection.children.link(Collection) 
    
    mat_list = []
    
    for o in Col.objects:
        for s in o.material_slots:
            if s.material.name[-3:].isnumeric():
                # the last 3 characters are numbers
                if s.material.name[:-4] in mat_list:
                    # there is a material without the numeric extension so use it
                    s.material = mat_list[s.material.name[:-4]]
            else:
                if not s.material in mat_list: mat_list.append(s.material)        
                        
    if len(Objects)==1:
        return O[Objects[0]]
    else:
        return Col

def ImportTrees(filename, Objects, Collection = bpy.data.scenes['Scene'].collection, Zpos=-3):
    i = 0; TwigSet=[]
    
    if isinstance(Collection, str):
        if Collection in C:
            Col=C[Collection]
        else:
            Collection= bpy.data.collections.new(name = Collection)
            bpy.context.scene.collection.children.link(Collection)  
    
    if isinstance(Objects, str):
        Objects=[Objects]
                
    with bpy.data.libraries.load(MainDir + filename) as (data_from, data_to): 
        data_to.objects = [name for name in data_from.objects if name.startswith(tuple(Objects))]               
    
    for obj in data_to.objects:
        if obj is not None:
           Collection.objects.link(obj) 
    
    for Object in Collection.objects:
        
        for p in Object.particle_systems:
            Twig=p.settings.instance_object
            if Twig.name[-3:].isnumeric():
                ParentTwigName=Twig.name[:-4]
                if ParentTwigName in TwigSet:
                    p.settings.instance_object=O[Twig.name[:-4]]
            else:
                if not Twig.name in TwigSet:
                    TwigSet.append(Twig.name)
                        
    mat_list = data_to.objects[0].data.materials
    
    for o in O:
        if o.name[-3:].isnumeric():
            # the last 3 characters are numbers
            if o.name[:-4] in TwigSet:
                O.remove(o)
                
    #for Twigname in TwigSet:
    #    Move_to_Collection([O[Twigname]], Collection)                 
    
    return Collection     

def ImportObject(filename, Object, Zpos=0):

    ImportObjects(filename=filename, Objects=[Object], Collection = bpy.data.scenes['Scene'].collection, Zpos=Zpos)

    return O[Object]      

def ImportScene(filename, Exclude=[], Collection = bpy.data.scenes['Scene'].collection, Zpos=-3):

    if isinstance(Collection, str):
        if Collection in C:
            Col=C[Collection]
        else:
            Collection= bpy.data.collections.new(name = Collection)
            bpy.context.scene.collection.children.link(Collection)  
    
    if isinstance(Exclude, str):
        Exclude=[Exclude]
                
    with bpy.data.libraries.load(MainDir + filename) as (data_from, data_to): 
        data_to.objects = [name for name in data_from.objects if name not in Exclude]               
    
    for obj in data_to.objects:
        if obj is not None:
           Collection.objects.link(obj)    
        
#    if Collection!=bpy.data.scenes['Scene'].collection:
#        bpy.context.scene.collection.children.link(Collection) 
    
    mat_list = data_to.objects[0].data.materials
    
    for o in Collection.objects:
        for s in o.material_slots:
            if s.material.name[-3:].isnumeric():
                # the last 3 characters are numbers
                if s.material.name[:-4] in mat_list:
                    # there is a material without the numeric extension so use it
                    s.material = mat_list[s.material.name[:-4]]
                        
    return Collection      
        
def ImportCollection(filename, Collection, Zpos=-100, Instanced=False, Linked=False):

    bpy.ops.wm.append(
        directory=MainDir+filename+"/Collection/",
        filename=Collection,
        instance_collections=Instanced,
        link=Linked)
    
    if Instanced:
        Col=O[Collection]
    else:    
        Col = C[Collection]
        if Zpos != -100:
            for o in Col.objects:
                o.location[2]=Zpos    
    
    return Col          

def recurLayerCollection(layerColl, collName):
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = recurLayerCollection(layer, collName)
        if found:
            return found

def SetActiveCollection(Name):
    #Change the Active LayerCollection to 'My Collection'
    layer_collection = bpy.context.view_layer.layer_collection
    layerColl = recurLayerCollection(layer_collection, Name)
    bpy.context.view_layer.active_layer_collection = layerColl

def ImportInstanceCollections(filename, Objects, Collection):

    if isinstance(Collection, str):
        if Collection in C:
            Col=C[Collection]
        else:
            Col= bpy.data.collections.new(name = Collection)
            bpy.context.scene.collection.children.link(Col)  
    else:
        Col=Collection   
        
    OldCol = bpy.context.view_layer.active_layer_collection    
    SetActiveCollection(Col.name)
        
    section = "/Object/"    
    objects = []
    with bpy.data.libraries.load(MainDir+filename) as (data_from, data_to):
        for name in data_from.objects:
            if name in Objects:
                objects.append({'name': name})
 
    for o in objects:
        print('->',o)
        
    bpy.ops.wm.append(directory = MainDir+filename+section,files = objects, 
        link = True,autoselect = True )
 
    imported = bpy.context.selected_objects
    for o in imported:
        o.make_local()
        #print(o.name)
        #Move_to_Collection([o],Collection)
        
    bpy.context.view_layer.active_layer_collection = OldCol         
        
    return Col

def ImportCollections(filename, Collection, Zpos=0):

    bpy.ops.wm.append(
        directory=MainDir+filename+"/Collection/",
        filename=Collection)

def ImportMaterial(filename, Material, Linked=False):

    bpy.ops.wm.append(
        directory=MainDir+filename+"/Material/",
        filename=Material,
        link=Linked)

    return bpy.data.materials[Material] 
          
# --- a function to select vertices, edges, or faces in an object ---
                             
# gives the bounding box x, y, and z limits of an object
def get_bbox(obj):
    L=[]
    for vert in obj.data.vertices: L.append(vert.co)
    x_max,y_max,z_max=np.amax(np.array(L),axis=0)
    x_min,y_min,z_min=np.amin(np.array(L),axis=0)    
    return [(x_min,y_min,z_min),(x_max,y_max,z_max)]

# Checks whether a vertex, edge, or face is within a certain box
def in_bbox(lbound, ubound, v, buffer = 0.0001):
    return lbound[0] - buffer <= v[0] <= ubound[0] + buffer and \
            lbound[1] - buffer <= v[1] <= ubound[1] + buffer and \
            lbound[2] - buffer <= v[2] <= ubound[2] + buffer                             

# Selects those vertices, edges, or faces that are within a box defined relative 
# to an objects size.                              
def Select(lbound = (0, 0, 0), ubound = (0, 0, 0), relative=True,
                    select_mode = 'VERT', additive = False):
    
    if relative==True:
        obj=Active()
        [min_loc, max_loc] = get_bbox(obj)
        mean_loc = (ar(min_loc)+ar(max_loc))/2
        dev_loc = ar(max_loc)-mean_loc
        lbound = mean_loc + dev_loc*lbound
        ubound = mean_loc + dev_loc*ubound
    
    # Set selection mode, VERT, EDGE, or FACE
    bpy.ops.mesh.select_mode(type = select_mode)
    
    # Grab the transformation matrix
    world = bpy.context.object.matrix_world
    
    # Instantiate a bmesh object and ensure lookup table
    # Running bm.faces.ensure_lookup_table() works for all parts
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()
    
    # Initialize list of vertices and list of parts to be selected
    verts = []
    to_select = []
    
    # For VERT, EDGE, or FACE ...
    # 1. Grab list of coordinates
    # 2. Test if the piece is entirely within the rectangular
    #    prism defined by lbound and ubound
    # 3. Select each piece that returned True and deselect
    #    each piece that returned False in Step 2
    
    if select_mode == 'VERT':
        [verts.append(v.co.to_tuple()) for v in bm.verts]
        [to_select.append(in_bbox(lbound, ubound, v)) for v in verts]
        for vertObj, select in zip(bm.verts, to_select):
            if additive:
                vertObj.select |= select
            else:
                vertObj.select = select
            
    if select_mode == 'EDGE':
        [verts.append([v.co.to_tuple() for v in e.verts]) for e in bm.edges]
        [to_select.append(all(in_bbox(lbound, ubound, v) for v in e)) for e in verts]  
        for edgeObj, select in zip(bm.edges, to_select):
            if additive:
                edgeObj.select |= select
            else:
                edgeObj.select = select
            
    if select_mode == 'FACE':
        [verts.append([v.co.to_tuple() for v in f.verts]) for f in bm.faces]            
        [to_select.append(all(in_bbox(lbound, ubound, v) for v in f)) for f in verts] 
        for faceObj, select in zip(bm.faces, to_select): 
            if additive:
                faceObj.select |= select
            else:
                faceObj.select = select            
    
    return sum([1 for s in to_select if s])