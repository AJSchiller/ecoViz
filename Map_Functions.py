# import fiona
import geopandas as gpd
import json
import matplotlib.pyplot as plt
from math import sqrt, pi
import numpy as np
from PIL import Image, ImageDraw
# from rasterio import mask as msk
from scipy.ndimage.filters import gaussian_filter
from scipy import ndimage as nd
from shapely.geometry import polygon,box
import shapely
import warnings

# # Enable fiona driver
# from fiona.drvsupport import supported_drivers
# supported_drivers['KML'] = 'rw'

on = 1
off = 0

def PlotPanel(fig, ax, imdata, cmap='terrain', clim=0, xylim=0, orientation='vertical', title="", colorbar=True, extent=None):
    im = ax.imshow(imdata, cmap=cmap, clim=clim, extent=extent);
    if title != "":
        ax.set_title(title, y=1.03, fontsize=20);
    if xylim != 0:
        ax.set_xlim((xylim[0], xylim[1]))
        ax.set_ylim((xylim[3], xylim[2]));
    if colorbar:
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, orientation=orientation);
    return im

def PlotLine(fig, ax, Val, xylim=0, title="", colorbar=True):        
    pl = ax.plot(Val, cmap=cmap, clim=clim, extent=extent);
    if title != "":
        ax.set_title(title, y=1.03, fontsize=20);
    if xylim != 0:
        ax.set_xlim((xylim[0], xylim[1]))
        ax.set_ylim((xylim[3], xylim[2]));
    return pl

def Normalise(D):
    return (D - np.min(D)) / (np.max(D) - np.min(D))

def Coord_to_MatPos(Coord):
        return (int(1024 + Coord[0]), int(1024 - Coord[1]))
    
def Coords_to_Poly(Coords):
    Output = []
    for Coord in Coords:
        Output.append(Coord_to_MatPos(Coord))
    return Output

def MakePolygon(Poly, shape, width=5, fill=1, sigma=0):
    img = Image.new('L', shape, 0)
    ImageDraw.Draw(img).line(Poly, width=width, fill=fill)
    mask = np.array(img)
    if sigma > 0:
        mask = gaussian_filter(np.float32(mask), sigma=sigma)
    return mask

def MakePolyMask(Poly, shape, fill=1, sigma=0):
    img = Image.new('L', shape, 0)
    ImageDraw.Draw(img).polygon(Poly, fill=fill)
    mask = np.array(img)
    if sigma > 0:
        mask = gaussian_filter(np.float32(mask), sigma=sigma)
    return mask

def DrawLine(KML_file, Elevation, boundingbox, Resolution, Width=5):
    Coords    = getKLMCoords(KML_file)
    Dyke_Poly = Coord_to_Indices(Coords, boundingbox, Resolution)
    Dyke_line = MakePolygon(Dyke_Poly, Elevation, width=Width, fill=1)
    return Dyke_line, Dyke_Poly

def MakeDyke_old(Dyke_Poly, Landscape, DykeHeight=7, Dyke_Slope = 0.33, Dyke_Width=5, Pave=on):
    
    Dyke_line = MakePolygon(Dyke_Poly, Landscape, width=Dyke_Width, fill=1)

    # Compute distance from dyke top, and shape dyke
    Dyke_Distance = nd.distance_transform_edt(Dyke_line==0, return_indices=False)
    Dyke_Profile  = np.maximum(0, DykeHeight - Dyke_Slope * Dyke_Distance)
    Dyke_Profile  = gaussian_filter(Dyke_Profile, sigma=0.5)
    return Dyke_Profile, Dyke_mask

def MakeDyke(Dyke_Poly, Landscape, Dyke_Height, Dyke_Slope, Dyke_Width, Sigma=0.5):
    
    # Plotting the dyke on the landscape canvas
    Dyke_line     = MakePolygon(Dyke_Poly, Landscape, width=int(Dyke_Width*1.5), fill=1)

    # Compute distance from dyke top, and shape dyke
    Dyke_Distance = nd.distance_transform_edt(Dyke_line==0, return_indices=False)
    Dyke_Profile  = np.maximum(0, Dyke_Height - Dyke_Slope * Dyke_Distance)
    Dyke_Profile  = gaussian_filter(Dyke_Profile, sigma=Sigma)
    Dyke_mask     = Dyke_Profile > 0.01
    
    return Dyke_Profile, Dyke_mask

def MaskGeoPolygon(df, dataset, Filled=True):
    geo = gpd.GeoDataFrame({'geometry': df.geometry}, index=[0], crs='epsg:28992')
    coords = getFeatures(geo)
    out_img, out_transform = msk.mask(dataset, shapes=coords, filled=Filled, invert=False, crop=False, pad=True)
    out_meta = dataset.meta.copy()

    mask_int, mask_transform = msk.mask(dataset, shapes=coords, invert=False, nodata= -1e6)
    mask_img = np.ones_like(mask_int)
    mask_img[mask_int == -1e6]=0
    
    return mask_int, mask_transform, np.array(coords[0]['coordinates'])

def TransposeMaskGeo(df, dataset, transpose, Filled=True):
    geo = gpd.GeoDataFrame({'geometry': df.geometry}, index=[0], crs='epsg:28992')
    coords = getFeatures(geo)
    coords_list = coords[0]['coordinates'][0]
    coords[0]['coordinates'][0] = [[i[0] + transpose[0], i[1] + transpose[1]] for i in coords_list]
                # `transpose` is a tuple of the form `(x, y)`
                # with the number of steps to move the coordinates along the x and y axes respectively

    mask_int, mask_transform = msk.mask(dataset, shapes=coords, invert=False, nodata= -1e6)
    
    return mask_int[0]

def getFeatures(df):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(df.to_json())['features'][0]['geometry']]

def ReadKML(kml_file, CRS='epsg:28992'):
            
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = gpd.read_file(kml_file, driver='KML')

        # Drop Z dimension of polygons that occurs often in kml 
        df.geometry = df.geometry.map(lambda polygon: shapely.ops.transform(lambda x, y, z: (x, y), polygon))

        # Switch to AHN projection frame
        df = df.to_crs({'init': CRS}) 
    
    return df

def getKLMCoords(Name, CRS='epsg:28992'):
    df = ReadKML(Name, CRS=CRS)
    geo = gpd.GeoDataFrame({'geometry': df.geometry}, index=[0])
    
    if getFeatures(geo)[0]['type'] == 'Polygon':
        out = np.array(getFeatures(geo)[0]['coordinates'][0])
        
    elif getFeatures(geo)[0]['type'] == 'LineString':
        out = np.array(getFeatures(geo)[0]['coordinates'])
        
    elif getFeatures(geo)[0]['type'] == 'Point':
        out = np.array(getFeatures(geo)[0]['coordinates'])   

    return out

def GetMapCenter(Name):
    Coords = getKLMCoords(Name)
    return np.mean(Coords[:,0]), np.mean(Coords[:,1])    
    
def Coord_to_Indices(Coordinates, bbox, Resolution):
    Indices = np.zeros_like(np.array(Coordinates))
    if len(Coordinates.shape) > 1:
        Indices[:,0] = ( (Coordinates[:,0] - bbox[0]) / Resolution)
        Indices[:,1] = (-(Coordinates[:,1] - bbox[3]) / Resolution)
        Set = [(int(I[0]), int(I[1])) for I in Indices]
    else:
        Indices[0] = int( (Coordinates[0] - bbox[0]) / Resolution)
        Indices[1] = int(-(Coordinates[1] - bbox[3]) / Resolution)        
        Set = (Indices[0], Indices[1])
    return Set

def MakeGap(Name, GapSize, Dyke_Width, X, Y, boundingbox, Resolution):
    Coords   = np.array(ReadKML(Name)['geometry'][0].coords)[0]
    Indices  = Coord_to_Indices(Coords, boundingbox, Resolution)
    Distance = np.sqrt((X - (Indices[0])) ** 2 + (Y - (Indices[1])) ** 2)
    Gap      = 1 - (Distance < (GapSize / 2 + Dyke_Width))
    return Gap

def MergeData(data, shape, MC):
    """Creates an array 'Map' defined by shape. Stores data in Map, within the area bounded by MC (marsh corners).

    Arguments:
        data {np.array} -- Array of data to load into Map
        shape {tuple} -- Shape of Map
        MC {list} -- marsh corner coordinates withing the Map [x_min, x_max, y_min, y_max]

    Returns:
        Map {np.array} -- Map
    """

    Map = np.zeros(shape)
    Map[MC[2]:(MC[3]+1), MC[0]:(MC[1]+1)] = data

    return Map

def DiffuseBoundaries(Matrix, Boundaries, Value, Time):

    for t in range(Time):
        Matrix = Matrix * Boundaries + (1 - Boundaries) * Value
        Matrix = gaussian_filter(Matrix, sigma=1)

    return Matrix

def Rotate(Angle, Pos, Xm, Ym):

    Rotation = Angle / 180 * pi
    Xr   =  np.cos(Rotation) * (Xm - Pos[0]) + np.sin(Rotation) * (Ym - Pos[1])  # "clockwise"
    Yr   = -np.sin(Rotation) * (Xm - Pos[0]) + np.cos(Rotation) * (Ym - Pos[1])

    return (Xr + Pos[0], Yr + Pos[1])

def Cover(V, a, b):
    # Computing cover from an elevation or random map:
    return 1 / (1 + np.exp(-a * (V - b)))

# Conversion to Blender orientation

def rebin(a, shape):
    """Reshapes a map.

    Args:
        a (array): map to be reshaped.
        shape (tuple): output shape.

    Returns:
        (array): reshaped map.
    """
    
    sh = shape[0], a.shape[0] // shape[0], shape[1], a.shape[1] // shape[1]
    
    return a.reshape(sh).mean(-1).mean(1)

def Conv(I, shape):
    """Converts maps to Blender orientation.

    Args:
        I (array): map to be converted.
        shape (tuple): output shape.

    Returns:
        (array): converted map.
    """
    
    Is = rebin(I, shape)
    If = np.flipud(Is.T)
    
    return If

def MapHabitat(M):
    """Converts habitat map to mask.

    Args:
        M (array): map to be converted.
    
    Returns:
        (array): mask.
    """
    
    return np.minimum(1, np.maximum(0, M))