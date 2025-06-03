import bpy, bmesh, importlib, sys, io
from math import pi
import numpy as np
from contextlib import redirect_stdout

BU = bpy.data.texts['BlenderUtils.py'].as_module()
#NL = bpy.data.texts['NodeLanguage.py'].as_module()

on=1; off=0

MainDir = bpy.path.abspath("//")
O = bpy.data.objects

################################################################################
# Some basic functions
################################################################################

def LinkNodes(node_tree, from_node, from_slot_name, to_node, to_slot_name):
        input = to_node.inputs[to_slot_name]
        output = from_node.outputs[from_slot_name]
        node_tree.links.new(input, output)
        
def ar(M):
    return np.array(M)

################################################################################
# Setting up materials
################################################################################

def MakeImageMaterial(Name, FileName):
    # Creating material   
    mat=bpy.data.materials.new(Name+'_Mat')

    # Loading texture   
    tex=bpy.data.textures.new(Name+'_Tex', type = 'IMAGE')
    img = bpy.data.images.load(FileName)# load image
    tex.image = img
    mtex = mat.texture_slots.add()
    mtex.texture = tex

    # Setting up node system and linking to image
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img

    # Linking Diffuse BSDF node to image texture 
    matnodes = mat.node_tree.nodes
    Input=matnodes['Diffuse BSDF'].inputs['Color']
    Output=matnodes['Image Texture'].outputs['Color']
    mat.node_tree.links.new(Input, Output)
    return mat

################################################################################
# Setting up the Image-based materials - Rob Textures
################################################################################

def SetupRobMaterial(Name, TexturePath, TextureName,
                     Gamma1=0.8, Gamma2=0.4,
                     RampPos1=0.33, RampPos2=0.66): 
    
    Prelude=TextureName[0:(len(TextureName)-6)]
    Postlude=TextureName[(len(TextureName)-6):].replace('_','.')
    DiffName   = TexturePath+TextureName+'/'+Prelude+"diff_"+Postlude
    NormalName = TexturePath+TextureName+'/'+Prelude+"nor_"+Postlude
    SpecName   = TexturePath+TextureName+'/'+Prelude+"spec_"+Postlude   
    RoughName  = TexturePath+TextureName+'/'+Prelude+"rough_"+Postlude    
    BumpName   = TexturePath+TextureName+'/'+Prelude+"bump_"+Postlude
    DispName   = TexturePath+TextureName+'/'+Prelude+"disp_"+Postlude
    
    Mat = bpy.data.materials.new(name=Name)
    Mat.use_nodes = True
    MatNode = Mat.node_tree.nodes['Material Output']

    # --- Creating the Principled Diffusive node
    PrinNode = Mat.node_tree.nodes["Principled BSDF"]
    PrinNode.location = (-00.0, 400.0) 
    Input=MatNode.inputs['Surface']
    Output=PrinNode.outputs['BSDF']
    Mat.node_tree.links.new(Input, Output)
    LinkNodes(Mat.node_tree, PrinNode, 'BSDF', MatNode, 'Surface')    
    
    XColor = -400
    YColor = 800
    
    # Creating the color mix shader node
    RGBNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RGBNode.name="Color Mixing node"
    #RGBNode.inputs[0].default_value = MixLevel
    LinkNodes(Mat.node_tree, RGBNode, 'Color', PrinNode, "Base Color")
    RGBNode.location = (XColor, YColor)   
    
    # Creating the first Gamma node
    Gamma1Node=Mat.node_tree.nodes.new("ShaderNodeGamma")
    Gamma1Node.name="Decoloring node 1"
    Gamma1Node.inputs[1].default_value=Gamma1
    LinkNodes(Mat.node_tree, Gamma1Node, 'Color', RGBNode, "Color1")
    Gamma1Node.location = (XColor-200 , YColor)     
    
    # Creating the first Gamma node
    Gamma2Node=Mat.node_tree.nodes.new("ShaderNodeGamma")
    Gamma2Node.name="Decoloring node 2"
    Gamma2Node.inputs[1].default_value=Gamma2    
    LinkNodes(Mat.node_tree, Gamma2Node, 'Color', RGBNode, "Color2")
    Gamma2Node.location = (XColor-200, YColor-100)   
    
    # --- Creating the Diffusive Image Shader node
    DiffNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    DiffImage = bpy.data.images.load(filepath = DiffName)
    DiffImage.name="Image node"
    DiffNode.image=DiffImage 
    LinkNodes(Mat.node_tree, DiffNode, 'Color', Gamma1Node, "Color") 
    LinkNodes(Mat.node_tree, DiffNode, 'Color', Gamma2Node, "Color")     
    DiffNode.location = (XColor-500, YColor)   
    
    # Creating the Color Ramp node
    RampNode=Mat.node_tree.nodes.new("ShaderNodeValToRGB")
    RampNode.name="Color Ramp node"
    RampNode.color_ramp.elements[0].position = RampPos1
    RampNode.color_ramp.elements[1].position = RampPos2
    LinkNodes(Mat.node_tree, RampNode, 'Color', RGBNode, "Fac")
    RampNode.location = (XColor-300, YColor+250)    
    
    # Creating the Noise node
    NoiseNode=Mat.node_tree.nodes.new("ShaderNodeTexNoise")
    NoiseNode.name="NoiseNode"
    NoiseNode.inputs[2].default_value=1.5
    NoiseNode.inputs[3].default_value=0.5
    NoiseNode.inputs[4].default_value=2
    LinkNodes(Mat.node_tree, NoiseNode, 'Fac', RampNode, "Fac")
    NoiseNode.location = (XColor-500, YColor+250)          
    
    # --- Creating the Specular Image Shader node
    SpecNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    SpecNode.name="Specular Image"
    SpecImage = bpy.data.images.load(filepath = SpecName)
    SpecImage.colorspace_settings.name = 'Non-Color'    
    SpecNode.image=SpecImage 
    LinkNodes(Mat.node_tree, SpecNode, 'Color', PrinNode, "Specular") 
    SpecNode.location = (-400.0, 500.0)  
    
    # --- Creating the Roughness Image Shader node
    RoughNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    RoughImage = bpy.data.images.load(filepath = RoughName )
    RoughImage.colorspace_settings.name = 'Non-Color'
    RoughNode.name="Roughness node"
    RoughNode.image=RoughImage 
    LinkNodes(Mat.node_tree, RoughNode, 'Color', PrinNode, "Roughness") 
    RoughNode.location = (-400.0, 220.0)          
    
    # --- Creating the Bump Mixer Shader node
    BumpMixNode = Mat.node_tree.nodes.new("ShaderNodeBump")
    BumpMixNode.name="Bump Mixer Node"
    LinkNodes(Mat.node_tree, BumpMixNode, 'Normal', PrinNode, "Normal")   
    BumpMixNode.location = (-200.0, -70.0)  
    
    # --- Creating the Color Mixer Shader node
    RGBMixNode = Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RGBMixNode.name="RGB Mixer Node"
    LinkNodes(Mat.node_tree, RGBMixNode, 'Color', BumpMixNode, "Height")   
    RGBMixNode.inputs[0].default_value = 0.97
    RGBMixNode.inputs[2].default_value = (0, 0, 0, 1)
    RGBMixNode.location = (-400.0, -50.0) 
    
    # --- Creating the Bump Image Shader node
    BumpNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    BumpImage = bpy.data.images.load(filepath = BumpName)
    BumpNode.name="Bump Node"
    BumpNode.image=BumpImage 
    BumpImage.colorspace_settings.name = 'Non-Color'
    LinkNodes(Mat.node_tree, BumpNode, 'Color', RGBMixNode, "Color1")   
    BumpNode.location = (-700.0, -50.0)   
    
    # --- The Normal node, a double link ----------------------------------
    NormalNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    NormalImage = bpy.data.images.load(filepath = NormalName)
    NormalNode.name="Normal Node"
    NormalNode.image=NormalImage  
    NormalImage.colorspace_settings.name = 'Non-Color'
    NormalNode.location = (-700.0, -350.0)  
    
    # --- The normal map node ---------------------------------------------
    NormalMapNode = Mat.node_tree.nodes.new("ShaderNodeNormalMap") 
    LinkNodes(Mat.node_tree, NormalNode, 'Color', NormalMapNode, 'Color') 
    LinkNodes(Mat.node_tree, NormalMapNode, 'Normal', BumpMixNode, 'Normal')              
    NormalMapNode.location = (-400.0, -250.0)
    
    # --- Creating the Displacement Shader node
    DispNode = Mat.node_tree.nodes.new("ShaderNodeDisplacement")
    DispNode.name="Displacement Node"
    DispNode.label="Displacement Node"
    DispNode.inputs[1].default_value = 1.0
    DispNode.inputs[2].default_value = 0.5
    LinkNodes(Mat.node_tree, DispNode, "Displacement", MatNode, "Displacement") 
    DispNode.location = ar(PrinNode.location) + ar((0 , -650))  

    # --- Creating the Displacement Image Shader node
    DispImgNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    DispImage = bpy.data.images.load(filepath = DispName)
    DispImgNode.name="Displacement Image"
    DispImgNode.label="Displacement Image"
    DispImgNode.image=DispImage 
    LinkNodes(Mat.node_tree, DispImgNode, 'Color', DispNode, "Height")  
    DispImage.colorspace_settings.name = 'Non-Color' 
    DispImgNode.location = ar(NormalMapNode.location) + ar((-300 , -400))   
    
    # --- Add the Texture coordinate --------------------------------------
    
    MapNode = Mat.node_tree.nodes.new("ShaderNodeMapping")
    MapNode.name='MappingNode'
    LinkNodes(Mat.node_tree, MapNode, 'Vector', DiffNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', NormalNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', BumpNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', DispImgNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', RoughNode, 'Vector') 
    MapNode.location = (-1200.0, 500)
    
    # --- Add the Mapping node for the noise --------------------------------------
    
    NoiseMapNode = Mat.node_tree.nodes.new("ShaderNodeMapping")
    NoiseMapNode.name='NoiseMappingNode'
    LinkNodes(Mat.node_tree, NoiseMapNode, 'Vector', NoiseNode, 'Vector')  
    NoiseMapNode.location = (-1200.0, YColor+250)
    
    CoordNode = Mat.node_tree.nodes.new("ShaderNodeTexCoord")
    LinkNodes(Mat.node_tree, CoordNode, 'UV', MapNode, 'Vector') 
    LinkNodes(Mat.node_tree, CoordNode, 'UV', NoiseMapNode, 'Vector')     
    CoordNode.location = (-1400.0, 500)
    
    #Mat.cycles.displacement_method = 'BOTH'
    Mat.cycles.displacement_method = 'BUMP'

    return Mat

################################################################################
# Setting up the Castle materials - Rob Textures
################################################################################

def RobsCastleMaterial(Name, TexturePath, TextureName,
                     Gamma1=0.8, Gamma2=0.4): 
    
    Prelude=TextureName[0:(len(TextureName)-6)]
    Postlude=TextureName[(len(TextureName)-6):].replace('_','.')
    DiffName   = TexturePath+TextureName+'/'+Prelude+"diff_"+Postlude
    VoegDiffName = TexturePath+TextureName+'/'+Prelude+"diff_voeg_2k.png"
    NormalName = TexturePath+TextureName+'/'+Prelude+"nor_"+Postlude
    SpecName   = TexturePath+TextureName+'/'+Prelude+"spec_"+Postlude   
    RoughName  = TexturePath+TextureName+'/'+Prelude+"rough_"+Postlude    
    BumpName   = TexturePath+TextureName+'/'+Prelude+"bump_"+Postlude
    DispName   = TexturePath+TextureName+'/'+Prelude+"disp_"+Postlude
    
    Mat = bpy.data.materials.new(name=Name)
    Mat.use_nodes = True
    MatNode = Mat.node_tree.nodes['Material Output']

    # --- Creating the Principled Diffusive node
    PrinNode = Mat.node_tree.nodes["Principled BSDF"]
    PrinNode.location = (-00.0, 400.0) 
    PrinNode.inputs[5].default_value = 0.02
    Input=MatNode.inputs['Surface']
    Output=PrinNode.outputs['BSDF']
    Mat.node_tree.links.new(Input, Output)
    LinkNodes(Mat.node_tree, PrinNode, 'BSDF', MatNode, 'Surface')    
    
    XColor = -400
    YColor = 800

    # Creating the Voeg color mix shader node
    BlackRGBNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    BlackRGBNode.name="BlackRGBNode"
    BlackRGBNode.label="BlackRGBNode"
    #RGBNode.inputs[0].default_value = MixLevel
    LinkNodes(Mat.node_tree, BlackRGBNode, 'Color', PrinNode, "Base Color")
    BlackRGBNode.location = (-500, 700) 
    

    # Creating the Voeg color mix shader node
    VoegRGBNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    VoegRGBNode.name="Voeg Mixing node"
    #RGBNode.inputs[0].default_value = MixLevel
    LinkNodes(Mat.node_tree, VoegRGBNode, 'Color', BlackRGBNode, "Color2")
    VoegRGBNode.location = (-700, 700) 

    # --- Creating the Brightness-Contrast Shader node
    BCNode=Mat.node_tree.nodes.new("ShaderNodeBrightContrast")
    BCNode.name='BrightContrast'
    BCNode.inputs[1].default_value = -0.2
    BCNode.inputs[1].default_value = -0.2    
    LinkNodes(Mat.node_tree, BCNode, 'Color', VoegRGBNode, "Color2")   
    BCNode.location = ar(VoegRGBNode.location) + ar((-175,-200))
    
    # --- Creating the Diffusive Image Shader node
    VoegDiffNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    VoegDiffImage = bpy.data.images.load(filepath = VoegDiffName)
    VoegDiffImage.name="Image node"
    VoegDiffNode.image = VoegDiffImage 
    LinkNodes(Mat.node_tree, VoegDiffNode, 'Color', BCNode, "Color") 
    LinkNodes(Mat.node_tree, VoegDiffNode, 'Alpha', BlackRGBNode, "Fac")
    #LinkNodes(Mat.node_tree, VoegDiffNode, 'Color', BCNode, 'Color')     
    VoegDiffNode.location = ar(VoegRGBNode.location) + ar((-450,-300))  

    # Creating the Color Ramp node
    VoegRampNode=Mat.node_tree.nodes.new("ShaderNodeValToRGB")
    VoegRampNode.name="VoegRampNode"
    VoegRampNode.color_ramp.elements[0].position = 0.43
    VoegRampNode.color_ramp.elements[1].position = 0.76
    LinkNodes(Mat.node_tree, VoegRampNode, 'Color', VoegRGBNode, "Fac")
    VoegRampNode.location = ar(VoegRGBNode.location) + ar((-500 , +500))      
    
    # Creating the Noise node
    VoegNoiseNode=Mat.node_tree.nodes.new("ShaderNodeTexNoise")
    VoegNoiseNode.name="VoegNoiseNode"
    VoegNoiseNode.inputs[2].default_value=4.0
    VoegNoiseNode.inputs[3].default_value=0.5
    VoegNoiseNode.inputs[4].default_value=2
    LinkNodes(Mat.node_tree, VoegNoiseNode, 'Fac', VoegRampNode, "Fac")
    VoegNoiseNode.location = ar(VoegRampNode.location) + ar((-200 , 0))
    
    # Creating the color mix shader node
    RGBNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RGBNode.name="Color Mixing node"
    #RGBNode.inputs[0].default_value = MixLevel
    LinkNodes(Mat.node_tree, RGBNode, 'Color', VoegRGBNode, "Color1")
    RGBNode.location = ar(VoegRGBNode.location) + ar((-200 ,000))  
    
    # Creating the first Gamma node
    Gamma1Node=Mat.node_tree.nodes.new("ShaderNodeGamma")
    Gamma1Node.name="Decoloring node 1"
    Gamma1Node.inputs[1].default_value=Gamma1
    LinkNodes(Mat.node_tree, Gamma1Node, 'Color', RGBNode, "Color1")
    Gamma1Node.location = ar(RGBNode.location) + ar((-200 , 0))     
    
    # Creating the first Gamma node
    Gamma2Node=Mat.node_tree.nodes.new("ShaderNodeGamma")
    Gamma2Node.name="Decoloring node 1"
    Gamma2Node.inputs[1].default_value=Gamma2
    LinkNodes(Mat.node_tree, Gamma2Node, 'Color', RGBNode, "Color2")
    Gamma2Node.location = ar(RGBNode.location) + ar((-200 , -125))     
      
    # --- Creating the Diffusive Image Shader node
    DiffNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    DiffImage = bpy.data.images.load(filepath = DiffName)
    DiffImage.name="Image node"
    DiffNode.image=DiffImage 
    LinkNodes(Mat.node_tree, DiffNode, 'Color', Gamma1Node, "Color") 
    LinkNodes(Mat.node_tree, DiffNode, 'Color', Gamma2Node, 'Color')   
    LinkNodes(Mat.node_tree, DiffNode, 'Color', BlackRGBNode, 'Color1')   
    DiffNode.location = ar(Gamma1Node.location) + ar((-300,0))  
    
    # Creating the Color Ramp node
    RampNode=Mat.node_tree.nodes.new("ShaderNodeValToRGB")
    RampNode.name="Color Ramp node"
    RampNode.color_ramp.elements[0].position = 0.4
    RampNode.color_ramp.elements[1].position = 0.8
    LinkNodes(Mat.node_tree, RampNode, 'Color', RGBNode, "Fac")
    RampNode.location = ar(RGBNode.location) + ar((-300 , +250))      
    
    # Creating the Noise node
    NoiseNode=Mat.node_tree.nodes.new("ShaderNodeTexNoise")
    NoiseNode.name="NoiseNode"
    NoiseNode.inputs[2].default_value=2.0
    NoiseNode.inputs[3].default_value=0.5
    NoiseNode.inputs[4].default_value=2
    LinkNodes(Mat.node_tree, NoiseNode, 'Fac', RampNode, "Fac")
    NoiseNode.location = ar(RampNode.location) + ar((-200 , 0))
    
    # --- Creating the Specular Image Shader node
#    SpecNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
#    SpecNode.name="Specular Image"
#    SpecImage = bpy.data.images.load(filepath = SpecName)
#    SpecImage.colorspace_settings.name = 'Non-Color'    
#    SpecNode.image=SpecImage 
#    LinkNodes(Mat.node_tree, SpecNode, 'Color', PrinNode, "Specular") 
#    SpecNode.location = (-400.0, 500.0)  
    
    # --- Creating the Roughness Image Shader node
    RoughNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    RoughImage = bpy.data.images.load(filepath = RoughName )
    RoughImage.colorspace_settings.name = 'Non-Color'
    RoughNode.name="Roughness node"
    RoughNode.image=RoughImage 
    LinkNodes(Mat.node_tree, RoughNode, 'Color', PrinNode, "Roughness") 
    RoughNode.location = ar(PrinNode.location) + ar((-300 , -175))          
    
    # --- Creating the Bump Mixer Shader node
    BumpMixNode = Mat.node_tree.nodes.new("ShaderNodeBump")
    BumpMixNode.name="Bump Mixer Node"
    LinkNodes(Mat.node_tree, BumpMixNode, 'Normal', PrinNode, "Normal")   
    BumpMixNode.location = ar(PrinNode.location) + ar((-200 , -450))   
    
    # --- Creating the Color Mixer Shader node
    RGBMixNode = Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RGBMixNode.name="RGB Mixer Node"
    LinkNodes(Mat.node_tree, RGBMixNode, 'Color', BumpMixNode, "Height")   
    RGBMixNode.inputs[0].default_value = 0.97
    RGBMixNode.inputs[2].default_value = (0, 0, 0, 1)
    RGBMixNode.location = ar(BumpMixNode.location) + ar((-200 , 0)) 
    
    # --- Creating the Bump Image Shader node
    BumpNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    BumpImage = bpy.data.images.load(filepath = BumpName)
    BumpNode.name="Bump Node"
    BumpNode.image=BumpImage 
    BumpImage.colorspace_settings.name = 'Non-Color'
    LinkNodes(Mat.node_tree, BumpNode, 'Color', RGBMixNode, "Color1")   
    BumpNode.location = ar(RGBMixNode.location) + ar((-300 , 0))    
    
    # --- The normal map node ---------------------------------------------
    NormalMapNode = Mat.node_tree.nodes.new("ShaderNodeNormalMap") 
    LinkNodes(Mat.node_tree, NormalMapNode, 'Normal', BumpMixNode, 'Normal')              
    NormalMapNode.location = ar(PrinNode.location) + ar((-400 , -650))   

    # --- The Normal node, a double link ----------------------------------
    NormalNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    NormalImage = bpy.data.images.load(filepath = NormalName)
    NormalNode.name="Normal Node"
    NormalNode.image=NormalImage  
    LinkNodes(Mat.node_tree, NormalNode, 'Color', NormalMapNode, 'Color')     
    NormalImage.colorspace_settings.name = 'Non-Color'
    NormalNode.location = ar(NormalMapNode.location) + ar((-300 , -100))   

    # --- Creating the Displacement Shader node
    
    DispNode = Mat.node_tree.nodes.new("ShaderNodeDisplacement")
    DispNode.name="Displacement Node"
    DispNode.label="Displacement Node"
    DispNode.inputs[1].default_value = 0.25
    DispNode.inputs[2].default_value = 0.5
    LinkNodes(Mat.node_tree, DispNode, "Displacement", MatNode, "Displacement") 
    DispNode.location = ar(PrinNode.location) + ar((0 , -650))  

    # --- Creating the Displacement Image Shader node
    DispImgNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    DispImage = bpy.data.images.load(filepath = DispName)
    DispImgNode.name="Displacement Image"
    DispImgNode.label="Displacement Image"
    DispImgNode.image=DispImage 
    LinkNodes(Mat.node_tree, DispImgNode, 'Color', DispNode, "Height")  
    DispImage.colorspace_settings.name = 'Non-Color' 
    DispImgNode.location = ar(NormalMapNode.location) + ar((-300 , -400)) 
    
    # --- Add the Mapping node --------------------------------------
    
    MapNode = Mat.node_tree.nodes.new("ShaderNodeMapping")
    MapNode.name='MappingNode'
    LinkNodes(Mat.node_tree, MapNode, 'Vector', DiffNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', NormalNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', BumpNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', DispImgNode, 'Vector') 
    LinkNodes(Mat.node_tree, MapNode, 'Vector', RoughNode, 'Vector') 
    MapNode.location = ar(PrinNode.location) + ar((-1900.0, 100))
    
    # --- Add the Mapping node for the noise --------------------------------------
    
    NoiseMapNode = Mat.node_tree.nodes.new("ShaderNodeMapping")
    NoiseMapNode.name='NoiseMappingNode'
    LinkNodes(Mat.node_tree, NoiseMapNode, 'Vector', NoiseNode, 'Vector')  
    LinkNodes(Mat.node_tree, NoiseMapNode, 'Vector', VoegNoiseNode, 'Vector')  
    NoiseMapNode.location = ar(NoiseNode.location) + ar((-500.0, 0))
    
    CoordNode = Mat.node_tree.nodes.new("ShaderNodeTexCoord")
    LinkNodes(Mat.node_tree, CoordNode, 'UV', MapNode, 'Vector') 
    LinkNodes(Mat.node_tree, CoordNode, 'UV', NoiseMapNode, 'Vector')     
    CoordNode.location = ar(MapNode.location) + ar((-200.0, 0))
    
    Mat.cycles.displacement_method = 'BUMP'

    return Mat

################################################################################
# Setting up the Image-based materials
################################################################################

def SetupCrazyMaterial(Name, TexturePath="", TextureName="", MixColor=(1,1,1,1), MixLevel=0): 
    
    Prelude=TextureName
    Postlude='.png'
    DiffName   = TexturePath+TextureName+'/'+Prelude+"_COLOR"+Postlude
    NormalName = TexturePath+TextureName+'/'+Prelude+"_NRM"+Postlude
    BumpName   = TexturePath+TextureName+'/'+Prelude+"_DISP"+Postlude
    SpecName   = TexturePath+TextureName+'/'+Prelude+"_SPEC"+Postlude
    
    Mat = bpy.data.materials.new(name=Name)
    Mat.use_nodes = True
    MatNode = Mat.node_tree.nodes['Material Output']

    # --- Creating the Principled Diffusive node
    PrinNode = Mat.node_tree.nodes["Principled BSDF"]
    PrinNode.location = (-00.0, 400.0)   
    Input=MatNode.inputs['Surface']
    Output=PrinNode.outputs['BSDF']
    Mat.node_tree.links.new(Input, Output)
    LinkNodes(Mat.node_tree, PrinNode, 'BSDF', MatNode, 'Surface')    
    
    # Inserting the color mix shader node
    RGBNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RGBNode.name="Decoloring node"
    RGBNode.inputs['Color2'].default_value = MixColor
    RGBNode.inputs[0].default_value = 0.2
    LinkNodes(Mat.node_tree, RGBNode, 'Color', PrinNode, "Base Color")
    RGBNode.location = (-200.0, 400.0)   
    
    # --- Creating the Diffusive Image Shader node
    DiffNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    DiffImage = bpy.data.images.load(filepath = DiffName )
    DiffImage.name="Image node"
    DiffNode.image=DiffImage 
    LinkNodes(Mat.node_tree, DiffNode, 'Color', RGBNode, "Color1") 
    DiffNode.location = (-400.0, 400.0)    
    
    # --- Creating the Specular Image Shader node
    SpecNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    SpecImage = bpy.data.images.load(filepath = SpecName)
    SpecImage.name="Image node"
    SpecNode.image=SpecImage 
    SpecImage.colorspace_settings.name = 'Non-Color'
    LinkNodes(Mat.node_tree, SpecNode, 'Color', PrinNode, "Specular") 
    SpecNode.location = (-200.0, 200.0)  
    
    # --- Creating the Bump Shader node
    BumpNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    BumpImage = bpy.data.images.load(filepath = BumpName)
    BumpNode.name="Bump Node"
    BumpImage.colorspace_settings.name = 'Non-Color'
    BumpNode.image=BumpImage 
    LinkNodes(Mat.node_tree, BumpNode, 'Color', MatNode, "Displacement")
    BumpNode.location = (0.0, -200.0)   

    # --- The Normal node, a double link ----------------------------------
    NormalNode = Mat.node_tree.nodes.new("ShaderNodeTexImage")
    NormalImage = bpy.data.images.load(filepath = NormalName)
    NormalNode.name="Normal Node"
    NormalImage.colorspace_settings.name = 'Non-Color'
    NormalNode.image=NormalImage 
    NormalNode.location = (-400.0, -100.0)
    
    NormalMapNode = Mat.node_tree.nodes.new("ShaderNodeNormalMap") 
    LinkNodes(Mat.node_tree, NormalNode, 'Color', NormalMapNode, 'Color')     
    LinkNodes(Mat.node_tree, NormalMapNode, 'Normal', PrinNode, 'Normal')              
    NormalMapNode.location = (-200.0, -100.0)

    return Mat

################################################################################
# Saving and loading the UVs
################################################################################

def SaveUVs(obj, UVFolder): 
    FileName = obj.name
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.tex.verify()  # currently blender needs both layers.
    # Save UVs
    UVs=[]
    for f in bm.faces:
        for l in f.loops:
            UVs.append((l[uv_layer].uv[0], l[uv_layer].uv[1]))
    bm.to_mesh(me)
    UVm=np.array(UVs)
    np.save(UVFolder+FileName,UVm)
    print('=> Saved!')
 
def LoadUVs(obj, UVFolder): 
    FileName = obj.name
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()
    #bm.faces.layers.tex.verify()  # currently blender needs both layers.
    # Save UVs
    UVm=np.load(UVFolder+FileName+'.npy')
    i=0;
    for f in bm.faces:
        for l in f.loops:
            l[uv_layer].uv[0] = UVm[i][0]
            l[uv_layer].uv[1] = UVm[i][1]
            i=i+1
    bm.to_mesh(me)  
    
################################################################################
# Making a glass shader using nodes
################################################################################

def MakeRuitMat():
    RuitMat = bpy.data.materials.new(name="Ruit_Mat")

    RuitMat.use_nodes = True
    NT=RuitMat.node_tree
    MatNode = NT.nodes['Material Output']
    MatNode.location = (0.0, 0.0) 
    
    BSDFNode = NT.nodes["Principled BSDF"]
    NT.nodes.remove(BSDFNode)

    MixNode = NT.nodes.new("ShaderNodeMixShader")
    Input=MatNode.inputs['Surface']
    Output=MixNode.outputs['Shader']
    #NT.links.new(Input, Output)
    LinkNodes(NT, MixNode, 'Shader', MatNode, 'Surface') 
    MixNode.location = (-180.0, 0.0) 

    GlassNode = NT.nodes.new("ShaderNodeBsdfGlass")
    Input=MixNode.inputs[1]
    Output=GlassNode.outputs['BSDF']
    NT.links.new(Input, Output)
    GlassNode.location = (-400, 0.0) 
    
    TrnspNode = NT.nodes.new("ShaderNodeBsdfTransparent")
    Input=MixNode.inputs[2]
    Output=TrnspNode.outputs['BSDF']
    NT.links.new(Input, Output)
    TrnspNode.location = (-400, -200.0)

    MathNode = NT.nodes.new("ShaderNodeMath")
    LinkNodes(NT, MathNode, 'Value', MixNode, 'Fac') 
    MathNode.operation = 'MAXIMUM'
    MathNode.location = (-400, 200.0)
    
    LightNode = NT.nodes.new("ShaderNodeLightPath")
    LinkNodes(NT, LightNode, 1,  MathNode, 0) 
    LinkNodes(NT, LightNode, 5,  MathNode, 1) 
    LightNode.location = (-600, 200.0)    
    
    return RuitMat    

################################################################################
# Water materials
################################################################################

def WaterMat_Musgrave():
    WaterMat = bpy.data.materials.new(name="Waterplane_Mat")
    WaterMat.use_nodes = True
    NT=WaterMat.node_tree
    MatNode = NT.nodes['Material Output']
    #MatNode = bpy.ops.node.add_node(type="ShaderNodeOutputMaterial", use_transform=True)

    BSDFNode = NT.nodes["Principled BSDF"]
    NT.nodes.remove(BSDFNode)
        
    GlassNode = NT.nodes.new("ShaderNodeBsdfGlass")
    GlassNode.inputs[1].default_value = 0.0
    LinkNodes(NT, GlassNode, 'BSDF', MatNode, "Surface") 
    GlassNode.location = (0, 400) 
    
    DispNode = NT.nodes.new("ShaderNodeDisplacement")
    DispNode.inputs[2].default_value = 0.1
    LinkNodes(NT, DispNode, 0, MatNode, "Displacement") 
    DispNode.location = (-0, 200)        

    MathNode = NT.nodes.new("ShaderNodeMath")
    MathNode.operation = 'MULTIPLY'
    LinkNodes(NT, MathNode, 'Value', DispNode, 0) 
    MathNode.location = (-200, 200)
    
    MixNode = NT.nodes.new("ShaderNodeMixRGB")
    MixNode.inputs[0].default_value = 0.7
    LinkNodes(NT, MixNode, 'Color', MathNode, 'Value') 
    MixNode.location = (-400, 200)    
    
    Musgrave1= NT.nodes.new("ShaderNodeTexMusgrave")
    Musgrave1.inputs[1].default_value = 50.0
    Musgrave1.inputs[2].default_value = 2
    LinkNodes(NT, Musgrave1, 'Fac', MixNode, "Color1") 
    Musgrave1.location = (-600, 300)
    
    Musgrave2 = NT.nodes.new("ShaderNodeTexMusgrave")
    Musgrave2.inputs[1].default_value = 10.0
    Musgrave2.inputs[2].default_value = 3
    LinkNodes(NT, Musgrave2, 'Fac', MixNode, 'Color2')
    Musgrave2.location = (-600, 0)
    
    MapNode = NT.nodes.new("ShaderNodeMapping")
    MapNode.inputs[3].default_value[0] = 2   
    LinkNodes(NT, MapNode, 'Vector', Musgrave1, 'Vector')
    LinkNodes(NT, MapNode, 'Vector', Musgrave2, 'Vector')
    MapNode.location = (-800, 150)
  
    RampNode = NT.nodes.new("ShaderNodeValToRGB")
    RampNode.color_ramp.elements[0].position = 0.50
    RampNode.color_ramp.elements[1].position = 0.60
    RampNode.color_ramp.elements[0].color = (0.10, 0.10, 0.10, 1)
    RampNode.color_ramp.elements[1].color = (0.33, 0.33, 0.33, 1)
    LinkNodes(NT, RampNode, 'Color', MathNode, 1)
    RampNode.location = (-600, -300)     
    
    NoiseNode = NT.nodes.new("ShaderNodeTexNoise")
    NoiseNode.inputs[2].default_value = 0.1
    LinkNodes(NT, NoiseNode, 'Fac', RampNode, 'Fac')
    NoiseNode.location = (-800, -300)    
        
    GeoNode = NT.nodes.new("ShaderNodeNewGeometry")
    LinkNodes(NT, GeoNode, 'Position', MapNode, 'Vector')
    LinkNodes(NT, GeoNode, 'Position', NoiseNode, 'Vector')
    GeoNode.location = (-1000, 150)

    return WaterMat

def UpdatewithMoss(Mat):

    #Mat = bpy.data.materials["Base_Mat"]
    MatNode = Mat.node_tree.nodes['Material Output']
        
    # Naming the nodes that we attach to
    PrinNode = Mat.node_tree.nodes["Principled BSDF"]
    RGBNode = Mat.node_tree.nodes["Color Mixing node"]
    ColRampNode = Mat.node_tree.nodes["Color Ramp node"]

    # Inserting a new in between color mix shader node
    RockMossMixNode=Mat.node_tree.nodes.new("ShaderNodeMixRGB")
    RockMossMixNode.name="Decoloring node"
    LinkNodes(Mat.node_tree, RockMossMixNode, 'Color', PrinNode, "Base Color")
    LinkNodes(Mat.node_tree, RGBNode, 'Color', RockMossMixNode, 'Color1')
    RockMossMixNode.location = (-200.0, 1200.0)   

    # Inserting the Node mixing height and noise
    MathNode=Mat.node_tree.nodes.new("ShaderNodeMath")
    MathNode.name="Node mixing height and noise"
    MathNode.operation = 'SUBTRACT'
    LinkNodes(Mat.node_tree, MathNode, 'Value', RockMossMixNode, "Fac")
    MathNode.location = (-400.0, 1300.0)  

    # Creating the Color Ramp node
    RampNode=Mat.node_tree.nodes.new("ShaderNodeValToRGB")
    RampNode.name="Color Ramp Node for Moss"
    RampNode.color_ramp.elements[0].position = 0.40
    RampNode.color_ramp.elements[1].position = 0.75
    LinkNodes(Mat.node_tree, RampNode, 'Color', MathNode, 0)
    RampNode.location = (-700, 1300)    

    # Creating the Noise node
    NoiseNode=Mat.node_tree.nodes.new("ShaderNodeTexNoise")
    NoiseNode.name="Moss Ramp node"
    NoiseNode.inputs[2].default_value=20
    NoiseNode.inputs[3].default_value=1
    LinkNodes(Mat.node_tree, NoiseNode, 'Fac', RampNode, "Fac")
    NoiseNode.location = (-900, 1300) 

    # Texture Coordinates
    TexCoordNode=Mat.node_tree.nodes.new("ShaderNodeTexCoord")
    TexCoordNode.name="Texture Coordinates node"
    #LinkNodes(Mat.node_tree, TexCoordNode, 'UV', NoiseNode, "Vector")
    TexCoordNode.location = (-1400, 1200) 

    # Coordinate Converter Node
    CoordConvertNode=Mat.node_tree.nodes.new("ShaderNodeSeparateXYZ")
    CoordConvertNode.name="Texture Coordinates node"
    LinkNodes(Mat.node_tree, TexCoordNode, 0, CoordConvertNode, 'Vector')
    CoordConvertNode.location = (-1200, 1400) 
    
        # Inserting the Node mixing height and noise
    YMathNode=Mat.node_tree.nodes.new("ShaderNodeMath")
    YMathNode.name="HeightScalingNode"
    YMathNode.operation = 'MULTIPLY'
    YMathNode.inputs[1].default_value = 1
    LinkNodes(Mat.node_tree, YMathNode, 'Value', MathNode, 1)
    LinkNodes(Mat.node_tree, CoordConvertNode, 'Z', YMathNode, 'Value')
    YMathNode.location = (-800.0, 1400.0)  

    # Color dampener node for the moss
    MossDampNode=Mat.node_tree.nodes.new("ShaderNodeBrightContrast")
    MossDampNode.name="Moss Color Dampener"
    MossDampNode.inputs[1].default_value=-0.2
    LinkNodes(Mat.node_tree, MossDampNode, 'Color', RockMossMixNode, "Color2")
    MossDampNode.location = (-400 , 1700)  

    MossName = MainDir+"Textures/tree-grass-abstract-plant-row-lawn-1105873-pxhere.com.jpg"

    # Creating the Diffusive Image Shader node
    MossNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
    MossImage = bpy.data.images.load(filepath = MossName)
    MossImage.name="Image node"
    MossNode.image=MossImage 
    LinkNodes(Mat.node_tree, MossNode, 'Color', MossDampNode, "Color")  
    MossNode.location = (-700, 1800)  
    
#    # Add the Z elevation to the colorramp to color the base of the base wet
#    AddNode=Mat.node_tree.nodes.new("ShaderNodeMath")
#    AddNode.name="Addition node"
#    AddNode.operation = 'ADD'
#    LinkNodes(Mat.node_tree, AddNode, 'Value', RGBNode, "Fac")
#    LinkNodes(Mat.node_tree, CoordConvertNode, 'Z', AddNode, 1)
#    AddNode.location = (-600, 600)     

################################################################################
# Scaling the UVs
################################################################################

def ScaleUV(obj,Scale=1, Rotate=False, Projection="Cube"):
    
    # Unwrapping Object UVs   
    BU.SelectObject(obj)
    BU.EditMode()
    
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001) 
    
    if Projection=="Cube":
        bpy.ops.uv.cube_project()
    elif Projection=="Sphere":
        bpy.ops.uv.sphere_project(direction='VIEW_ON_POLES')
    elif Projection=="Smart":  
        bpy.ops.uv.smart_project()
    elif Projection=="Cylinder":
        bpy.ops.uv.cylinder_project()
    elif Projection=="View":
        bpy.ops.uv.project_from_view(camera_bounds=True, correct_aspect=False, scale_to_bounds=False)

    if Rotate==True: bpy.ops.mesh.uvs_rotate()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    Size=np.maximum(obj.dimensions[0],np.maximum(obj.dimensions[1], obj.dimensions[2]))

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    uv_layer = bm.loops.layers.uv.verify()
    #bm.faces.layers.tex.verify()  # currently blender needs both layers.

    # scale UVs
    for f in bm.faces:
        for l in f.loops:
            #print(l[uv_layer].uv)
            l[uv_layer].uv[0] *= Scale*Size
            l[uv_layer].uv[1] *= Scale*Size

    bm.to_mesh(me)

def LinkRobMaterial(Node_Tree, 
                    OutputNode, OutputPos,
                    InputNode, InputPos,                        
                    TexturePath, TextureName, Length,
                    Gamma1=0.8, Gamma2=0.4,
                    RampPos1=0.33, RampPos2=0.66,
                    LocX=0,LocY=0): 

    Prelude=TextureName[0:(len(TextureName)-6)]
    Postlude=TextureName[(len(TextureName)-6):].replace('_','.')
    DiffName   = TexturePath+TextureName+'/'+Prelude+"diff_"+Postlude
    NormalName = TexturePath+TextureName+'/'+Prelude+"nor_"+Postlude
    SpecName   = TexturePath+TextureName+'/'+Prelude+"spec_"+Postlude   
    RoughName  = TexturePath+TextureName+'/'+Prelude+"rough_"+Postlude    
    BumpName   = TexturePath+TextureName+'/'+Prelude+"bump_"+Postlude
    DispName   = TexturePath+TextureName+'/'+Prelude+"disp_"+Postlude
    
    N=Node_Tree.nodes

    # --- Creating the Principled Diffusive node
    PrinNode = N.new("ShaderNodeBsdfPrincipled")
    PrinNode.location = (LocX, LocY) 
    LinkNodes(Node_Tree, PrinNode, 'BSDF', OutputNode, OutputPos)    
    
    XColor = LocX-200
    YColor = LocY
    
    # Creating the color mix shader node
    RGBNode=N.new("ShaderNodeMixRGB")
    RGBNode.name="Color Mixing node"
    #RGBNode.inputs[0].default_value = MixLevel
    LinkNodes(Node_Tree, RGBNode, 'Color', PrinNode, "Base Color")
    RGBNode.location = (XColor, YColor)   
    
    # Creating the first Gamma node
    Gamma1Node=N.new("ShaderNodeGamma")
    Gamma1Node.name="Decoloring node 1"
    Gamma1Node.inputs[1].default_value=Gamma1
    LinkNodes(Node_Tree, Gamma1Node, 'Color', RGBNode, "Color1")
    Gamma1Node.location = (XColor-200 , YColor)     
    
    # Creating the first Gamma node
    Gamma2Node=N.new("ShaderNodeGamma")
    Gamma2Node.name="Decoloring node 2"
    Gamma2Node.inputs[1].default_value=Gamma2    
    LinkNodes(Node_Tree, Gamma2Node, 'Color', RGBNode, "Color2")
    Gamma2Node.location = (XColor-200, YColor-100)   
    
    # --- Creating the Diffusive Image Shader node
    DiffNode=N.new("ShaderNodeTexImage")
    DiffImage = bpy.data.images.load(filepath = DiffName)
    DiffNode.image=DiffImage 
    LinkNodes(Node_Tree, DiffNode, 'Color', Gamma1Node, "Color") 
    LinkNodes(Node_Tree, DiffNode, 'Color', Gamma2Node, "Color")     
    DiffNode.location = (XColor-500, YColor)   
    
    # Creating the Color Ramp node
    RampNode=N.new("ShaderNodeValToRGB")
    RampNode.name="Color Ramp node"
    RampNode.color_ramp.elements[0].position = RampPos1
    RampNode.color_ramp.elements[1].position = RampPos2
    LinkNodes(Node_Tree, RampNode, 'Color', RGBNode, "Fac")
    RampNode.location = (XColor-300, YColor+250)    
    
    # Creating the Noise node
    NoiseNode=N.new("ShaderNodeTexNoise")
    NoiseNode.name="NoiseNode"
    NoiseNode.inputs[2].default_value=1.0
    NoiseNode.inputs[3].default_value=0.5
    NoiseNode.inputs[4].default_value=2
    LinkNodes(Node_Tree, NoiseNode, 'Fac', RampNode, "Fac")
    NoiseNode.location = (XColor-500, YColor+250)          
    
    # --- Creating the Specular Image Shader node
    SpecNode=N.new("ShaderNodeTexImage")
    SpecNode.name="Specular Image"
    SpecImage = bpy.data.images.load(filepath = SpecName)
    SpecImage.colorspace_settings.name = 'Non-Color'    
    SpecNode.image=SpecImage 
    LinkNodes(Node_Tree, SpecNode, 'Color', PrinNode, "Specular") 
    SpecNode.location = (XColor-200, YColor-220)    
    
    # --- Creating the Roughness Image Shader node
    RoughNode=N.new("ShaderNodeTexImage")
    RoughImage = bpy.data.images.load(filepath = RoughName )
    RoughImage.colorspace_settings.name = 'Non-Color'
    RoughNode.name="Roughness node"
    RoughNode.image=RoughImage 
    LinkNodes(Node_Tree, RoughNode, 'Color', PrinNode, "Roughness") 
    RoughNode.location = (XColor-500, YColor-300)           
    
    # --- Creating the Bump Mixer Shader node
    BumpMixNode = N.new("ShaderNodeBump")
    BumpMixNode.name="Bump Mixer Node"
    LinkNodes(Node_Tree, BumpMixNode, 'Normal', PrinNode, "Normal")   
    BumpMixNode.location = (XColor-00.0, YColor-500.0)  
    
    # --- Creating the Color Mixer Shader node
    RGBMixNode = N.new("ShaderNodeMixRGB")
    RGBMixNode.name="RGB Mixer Node"
    LinkNodes(Node_Tree, RGBMixNode, 'Color', BumpMixNode, "Height")   
    RGBMixNode.inputs[0].default_value = 0.97
    RGBMixNode.inputs[2].default_value = (0, 0, 0, 1)
    RGBMixNode.location = (XColor-200.0, YColor-500.0) 
    
    # --- Creating the Bump Image Shader node
    BumpNode = N.new("ShaderNodeTexImage")
    BumpImage = bpy.data.images.load(filepath = BumpName)
    BumpNode.name="Bump Node"
    BumpNode.image=BumpImage 
    BumpImage.colorspace_settings.name = 'Non-Color'
    LinkNodes(Node_Tree, BumpNode, 'Color', RGBMixNode, "Color1")   
    BumpNode.location = (XColor-500.0, YColor-600.0)   
    
    # --- The Normal node, a double link ----------------------------------
    NormalNode = N.new("ShaderNodeTexImage")
    NormalImage = bpy.data.images.load(filepath = NormalName)
    NormalNode.name="Normal Node"
    NormalNode.image=NormalImage  
    NormalImage.colorspace_settings.name = 'Non-Color'
    NormalNode.location = (XColor-500.0, YColor-900.0)  
    
    # --- The normal map node ---------------------------------------------
    NormalMapNode = N.new("ShaderNodeNormalMap")
    NormalMapNode.name='Normal Map' 
    LinkNodes(Node_Tree, NormalNode, 'Color', NormalMapNode, 'Color') 
    LinkNodes(Node_Tree, NormalMapNode, 'Normal', BumpMixNode, 'Normal')              
    NormalMapNode.location = (XColor-200.0, YColor-700.0)
    
#        # --- Creating the Displacement Shader node
#        DispNode = N.new("ShaderNodeDisplacement")
#        DispNode.name="Displacement Node"
#        DispNode.inputs[1].default_value = 1.0
#        DispNode.inputs[2].default_value = 0.5
#        LinkNodes(Node_Tree, DispNode, "Displacement", MatNode, "Displacement") 
#        DispNode.location = (XColor, YColor-1000.0)  

#        # --- Creating the Displacement Image Shader node
#        DispImgNode = N.new("ShaderNodeTexImage")
#        DispImage = bpy.data.images.load(filepath = DispName)
#        DispImgNode.name="Displacement Image"
#        DispImgNode.image=DispImage 
#        LinkNodes(Node_Tree, DispImgNode, 'Color', DispNode, "Height")  
#        DispImage.colorspace_settings.name = 'Non-Color' 
#        DispImgNode.location = (XColor-200.0, YColor-1000.0)  
    
    # --- Add the Texture coordinate --------------------------------------
    
    MapNode = N.new("ShaderNodeMapping")
    MapNode.name='MappingNode'
    MapNode.inputs[3].default_value = (Length, Length, 1)
    LinkNodes(Node_Tree, MapNode, 'Vector', DiffNode, 'Vector') 
    LinkNodes(Node_Tree, MapNode, 'Vector', NormalNode, 'Vector') 
    LinkNodes(Node_Tree, MapNode, 'Vector', BumpNode, 'Vector') 
    #LinkNodes(Node_Tree, MapNode, 'Vector', DispImgNode, 'Vector') 
    LinkNodes(Node_Tree, MapNode, 'Vector', RoughNode, 'Vector') 
    MapNode.location = (XColor-700.0, YColor-400.0)  
    
    # --- Add the Mapping node for the noise --------------------------------------
    
    NoiseMapNode = N.new("ShaderNodeMapping")
    NoiseMapNode.name='NoiseMappingNode'
    NoiseMapNode.inputs[3].default_value = (Length, Length, 1)
    LinkNodes(Node_Tree, NoiseMapNode, 'Vector', NoiseNode, 'Vector')  
    NoiseMapNode.location = (XColor-700.0, YColor+200)
    
    LinkNodes(Node_Tree, InputNode, InputPos, MapNode, 'Vector') 
    LinkNodes(Node_Tree, InputNode, InputPos, NoiseMapNode, 'Vector')     

################################################################################
# Making a material node group
################################################################################

def CreateTextureGroup(Texture, Length, Type='TextureHeaven'):
    
    TexturePath = MainDir+'../Textures/'  

    Group = bpy.data.node_groups.new(Texture, 'ShaderNodeTree')
    N = Group.nodes

    # create group inputs
    group_inputs = N.new('NodeGroupInput')
    group_inputs.location = (-2000,0)
    Group.inputs.new('NodeSocketVector','Coordinates')

    # create group outputs
    group_outputs = N.new('NodeGroupOutput')
    group_outputs.location = (0,0)
    Group.outputs.new('NodeSocketShader','BSDF')

    LinkRobMaterial(Group, 
                    group_outputs,'BSDF',
                    group_inputs,'Coordinates',
                    TexturePath,Texture, Length,
                    Gamma1=1.0, Gamma2=0.8,
                    LocX=-300, LocY=00)
                    
    # --- The Normal node, a double link ----------------------------------

    Gamma1Node=bpy.data.node_groups["brown_mud_2k_jpg"].nodes["Decoloring node 1"]
    Gamma2Node=bpy.data.node_groups["brown_mud_2k_jpg"].nodes["Decoloring node 2"]
    
    GammaCollNode = N.new("ShaderNodeMath")    
    GammaCollNode.name="GammaCollNode"
    GammaCollNode.operation = 'MULTIPLY'
    GammaCollNode.inputs[0].default_value = 0.5
    LinkNodes(Group, GammaCollNode, 0, Gamma2Node, 1) 
    GammaCollNode.location=(-1200,-200)
    
    InverseNode = N.new("ShaderNodeMath")
    InverseNode.name="Inverse Node"
    InverseNode.operation = 'DIVIDE'
    InverseNode.inputs[0].default_value = 0.6
    InverseNode.location = (-1400.0, -200.0)   
    
    LinkNodes(Group, InverseNode, 0, Gamma1Node, 1) 
    LinkNodes(Group, InverseNode, 0, GammaCollNode, 1) 
    
    ZNode = N.new("ShaderNodeSeparateXYZ")
    ZNode.location = (-1600.0, -200.0)  
    LinkNodes(Group, ZNode,'Z', InverseNode, 1) 
    
    LinkNodes(Group, group_inputs,'Coordinates', ZNode, 0) 
            
    return Group              

def CreatePatchDriverGroup(Material, ImagePath):
    
    TexturePath = MainDir+'Textures/'  

    Group = bpy.data.node_groups.new(Material, 'ShaderNodeTree')
    N = Group.nodes
    NT = Group

    # create group inputs
    group_inputs = N.new('NodeGroupInput')
    group_inputs.location = (-1500,0)
    Group.inputs.new('NodeSocketVector','Coordinates')

    # create group outputs
    group_outputs = N.new('NodeGroupOutput')
    group_outputs.location = (0,0)
    Group.outputs.new('NodeSocketFloat','Value')

    MathNode = NT.nodes.new("ShaderNodeMath")
    LinkNodes(NT, MathNode, 'Value', group_outputs, 'Value') 
    MathNode.operation = 'ADD'
    MathNode.location = (-200, 0.0)
    
    MultNode = NT.nodes.new("ShaderNodeMath")
    LinkNodes(NT, MultNode, 0, MathNode, 0) 
    MultNode.operation = 'MULTIPLY'
    MultNode.location = (-400, 0.0)
    
    # Creating the Color Ramp node
    NoiseRampNode=NT.nodes.new("ShaderNodeValToRGB")
    NoiseRampNode.name="Noise Ramp node"
    NoiseRampNode.color_ramp.elements[0].position = 0.5
    NoiseRampNode.color_ramp.elements[1].position = 0.55
    LinkNodes(NT, NoiseRampNode, 'Color', MultNode, 0)
    NoiseRampNode.location = (-800, 300)    
    
    # Creating the Color Ramp node
    MapRampNode=NT.nodes.new("ShaderNodeValToRGB")
    MapRampNode.name="Map Ramp node"
    MapRampNode.color_ramp.elements[0].position = 0
    MapRampNode.color_ramp.elements[1].position = 0.21
    MapRampNode.color_ramp.elements.new(1)
    MapRampNode.color_ramp.elements[2].color = (0.0,0.0,0.0,1)
    LinkNodes(NT, MapRampNode, 'Color', MultNode, 1)
    MapRampNode.location = (-800, 0)    
                    
        # Creating the Noise node
    NoiseNode = NT.nodes.new("ShaderNodeTexNoise")
    NoiseNode.name="NoiseNode"
    NoiseNode.noise_dimensions = '2D'
    NoiseNode.inputs[2].default_value=500
    NoiseNode.inputs[3].default_value=1
    NoiseNode.inputs[4].default_value=1
    LinkNodes(NT, NoiseNode, 'Fac', NoiseRampNode, "Fac")
    NoiseNode.location = (-1100, +250)  
    
    # --- Creating the Diffusive Image Shader node
    MapNode=NT.nodes.new("ShaderNodeTexImage")
    MapImage = bpy.data.images.load(filepath = ImagePath)
    MapNode.image=MapImage 
    MapImage.colorspace_settings.name = 'Non-Color'
    LinkNodes(NT, MapNode, 'Color', MapRampNode, "Fac") 
    LinkNodes(NT, MapNode, 'Color', MathNode, 1) 
    LinkNodes(NT, group_inputs, 'Coordinates', MapNode, 'Vector') 
    MapNode.location = (-1100, 0)                
                    
    return Group            

################################################################################
# Assembling a multimaterial
################################################################################

def MakeMultiMaterial(Name, PrimeTexName, AddiTextName, MapFileNames, Length,Displacement=""):
    Mat=bpy.data.materials.new(Name)
    Mat.use_nodes=True
    N=Mat.node_tree.nodes
    N.remove(N['Principled BSDF'])
    
    MatNode=N['Material Output']
    MatNode.location=(0,0)
        
    TextNr = len(AddiTextName)    
        
    CoordNode = N.new("ShaderNodeTexCoord")
    CoordNode.name='CoordinateNode'
    CoordNode.location = (-800-TextNr*500, -400)    
    
    MapNode = N.new("ShaderNodeMapping")
    MapNode.name='CoordMappingNode'
    MapNode.location = (-600-TextNr*500, -400)   
    LinkNodes(Mat.node_tree,CoordNode,0,MapNode,0)

    PrimeTexture = CreateTextureGroup( PrimeTexName, Length )
    
    N = Mat.node_tree.nodes
    PrimeGroup=N.new(type="ShaderNodeGroup")
    PrimeGroup.width=200
    PrimeGroup.location=(-400-TextNr*500,-50)
    PrimeGroup.node_tree = PrimeTexture   
    
    Mat.node_tree.links.new( MapNode.outputs[0], PrimeGroup.inputs[0] )    
    
    PrevShaderNode=MatNode.inputs['Surface']
    NewGroup=PrimeGroup
    
    if AddiTextName==[]:    
        LinkNodes(Mat.node_tree, NewGroup, 0, MatNode, "Surface")                  
    else:
        # Creating the color mix shader node
        for i in range(TextNr):
            MixNode=Mat.node_tree.nodes.new("ShaderNodeMixShader")
            MixNode.name="MixNode-%d" % i
            MixNode.label=MixNode.name
            MixNode.inputs[0].default_value = 0
            #LinkNodes(Mat.node_tree, MixNode, 'Shader', PrevShaderNode)
            Mat.node_tree.links.new( MixNode.outputs[0], PrevShaderNode )
            MixNode.location = (-200-500*i, 0)    
            PrevShaderNode=MixNode.inputs[1]

            ShellTexture = CreateTextureGroup( AddiTextName[i], Length )  
            Mat.node_tree.links.new( NewGroup.outputs[0], MixNode.inputs[1] )

            NewGroup=N.new(type="ShaderNodeGroup")
            NewGroup.width=200
            NewGroup.location=(-500-500*i,-150)
            NewGroup.node_tree = ShellTexture  
        
            #LinkNodes(Mat.node_tree, ShellTexture, 0, MixNode, 'Shader')
            Mat.node_tree.links.new( NewGroup.outputs[0], MixNode.inputs[2] )
            Mat.node_tree.links.new( MapNode.outputs[0], NewGroup.inputs[0] )
            
            PathName   = MainDir+MapFileNames[i]
            
            # --- Creating the Diffusive Image Shader node
#            PathNode=Mat.node_tree.nodes.new("ShaderNodeTexImage")
#            PathImage = bpy.data.images.load(filepath = PathName)
#            PathImage.colorspace_settings.name = 'Non-Color'
#            PathNode.image=PathImage 
#            LinkNodes(Mat.node_tree,  MapNode, 0, PathNode, 'Vector')  
#            LinkNodes(Mat.node_tree, PathNode, 'Color', MixNode,0)    
#            PathNode.location = (-500-500*i, 200)  
            
            PatchDriver = CreatePatchDriverGroup(MapFileNames[i], PathName)
            
            #Mat.node_tree.links.new( PatchGroup.outputs[0], MixNode.inputs[1] )

            PatchGroup=N.new(type="ShaderNodeGroup")
            PatchGroup.width=200
            PatchGroup.location=(-500-500*i,150)
            PatchGroup.node_tree = PatchDriver  
            
            Mat.node_tree.links.new( PatchGroup.outputs[0], MixNode.inputs[0] )
            Mat.node_tree.links.new( CoordNode.outputs[0], PatchGroup.inputs[0] )
            
        Mat.node_tree.links.new( PrimeGroup.outputs[0], PrevShaderNode ) 
        
        if Displacement!="":
        
            DispNode=N.new("ShaderNodeDisplacement")
            DispNode.inputs[1].default_value = 0.5
            DispNode.inputs[2].default_value = 4
            #LinkNodes(Mat, DispNode, 'Color', MatNode, "Displacement") 
            Mat.node_tree.links.new( DispNode.outputs[0], MatNode.inputs[2] )            
            DispNode.location = (-300, -400)   
            
            # --- Creating the Diffusive Image Shader node
            MapNode=N.new("ShaderNodeTexImage")
            MapImage = bpy.data.images.load(filepath = MainDir+Displacement)
            MapNode.image=MapImage 
            MapImage.colorspace_settings.name = 'Non-Color'
            #LinkNodes(N, MapNode, 'Color', DispNode, "Height") 
            #LinkNodes(N, CoordNode, outputs[0], MapNode, 'Vector') 
            Mat.node_tree.links.new( MapNode.outputs['Color'], DispNode.inputs["Height"] )            
            Mat.node_tree.links.new( CoordNode.outputs[0], MapNode.inputs["Vector"] )                
            MapNode.location = (-600, -400)   
                    
    return Mat  

################################################################################
# The Texture tester program
################################################################################

if __name__ == "__main__":          
    
    ################################################################################
    # Main program
    ################################################################################

    print("#######################################################################")
    print("==> Starting ...")  
    print("#######################################################################\n")

    # --- Cleaning previous iterations ---------------------------------
        
    def WipeSlate():
        BaseComponentList=[]

        #BU.SetToObjectMode()    
        BU.DeleteAll(exclude=BaseComponentList)
        #BU.CleanAll()

        SK = bpy.data.texts['Sky.py'].as_module()
        SK.SetSky(RealSky=off, Evening=off)

    ################################################################################
    # The material 
    ################################################################################

    print("==> Setting up material .. \n") 

    # --- Parameters ---------------------------------------------------------------
    TexturePath = MainDir+'../Textures/'                     

    # --- Creating the material --------------------------------------------------------

    #Mat = RobsCastleMaterial('Wall_Mat', TexturePath, 'castle_brick_07_2k_jpg', Gamma1=1.0, Gamma2=0.6)
    #Mat.node_tree.nodes["NoiseMappingNode"].inputs[3].default_value[1] = 0.33

    Mat = SetupRobMaterial('Dakpan_Mat', TexturePath,'grey_roof_tiles_2k_jpg', Gamma1=1.0, Gamma2=1.2)

    MatScale = 3 # 1.2 Also change this in walls.py

    ################################################################################
    # The material sphere
    ################################################################################

    def MakeSphere():
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
        bpy.ops.object.shade_smooth()
        Sphere=BU.Active('Sphere')

        # Adding a camera
        bpy.ops.object.camera_add( location=(0, -3.5, 0), rotation=(90/180*pi, 0, 0))

        # Adding a subsurface modeifier
        BU.SelectObject(O['Sphere'])
        bpy.ops.object.modifier_add(type='SUBSURF')
        Sphere.modifiers["Subdivision"].render_levels = 3
        Sphere.modifiers["Subdivision"].levels = 3

        BU.EditMode()
        #bpy.ops.uv.sphere_project(direction='VIEW_ON_EQUATOR')
        bpy.ops.uv.sphere_project(direction='VIEW_ON_POLES')
        BU.ObjectMode()
        
        # Setting th sun direction
        O['Sun'].rotation_euler=(0,45/180*pi,-45/180*pi)
        
        # Making the background transparent
        bpy.context.scene.render.film_transparent = True
        
        Sphere.data.materials.append(Mat)
        #ScaleUV(Sphere, Scale=MatScale, Rotate=False, Projection='Sphere')     
        
    ################################################################################
    # The main program
    ################################################################################

    WipeSlate()
    # MakeSphere()
    
    bpy.ops.mesh.primitive_plane_add(size=2048, location=(0, 0, 0))
    Plane=BU.Active()
    
    PrimeTexName = 'brown_mud_02_2k_jpg'
    AddiTextName = ['floor_pebbles_01_2k_jpg','shell_floor_01_2k_jpg']
    MapFileNames = ['GrindPadMap.png','ErfMap.png']
    #AddiTextName = []
    
    Mat = MakeMultiMaterial("Multi_Mat", PrimeTexName, AddiTextName, MapFileNames, 2048,"DitchesMap.png")
    
    BU.SelectObject( O['Plane'] )
    Plane.data.materials.append( Mat )  
    bpy.context.object.active_material.cycles.displacement_method = 'BOTH'

    
    ################################################################################
    # Finishing up
    ################################################################################
        
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'    
            
    BU.Purge()        