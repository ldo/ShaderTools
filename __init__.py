#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "Shader Tools",
    "author": "Please press Credits Button for more details",
    "version": (0, 8, 1),
    "blender": (2, 6, 1),
    "api": 42614,
    "location": "Properties > Material",
    "description": "Database shaders interface",
    "warning": "Beta version",
    "wiki_url": "http://shadertools.tuxfamily.org/?page_id=36",
    "tracker_url": "",
    "category": "System"}

import bpy

import sqlite3
import os
import platform
import locale
import shutil
import zipfile
import time
import sys

def stripext(name, ext) :
    # returns name with ext stripped off if it occurs at end.
    if name.endswith(ext) :
        name = name[:- len(ext)]
    #end if
    return name
#end stripext

MaterialCategories = \
    (
        "CarPaint", "Dirt", "FabricClothes", "Fancy", "FibreFur",
        "Glass", "Halo", "Liquids", "Metal", "Misc", "Nature",
        "Organic", "Personal", "Plastic", "Sky", "Space", "Stone",
        "Toon", "Wall", "Water", "Wood",
    )

# ************************************************************************************
# *                                     HERE I UPDATE PATH                           *
# ************************************************************************************
BlendPath = os.path.dirname(bpy.data.filepath)
AppPath = os.path.join(bpy.utils.user_resource("SCRIPTS"), "addons", "shader_tools")
ImportPath = os.path.dirname(bpy.data.filepath)
ErrorsPath = os.path.join(AppPath, "erro")
OutPath = os.path.join(AppPath, "out")
ZipPath = os.path.join(AppPath, "zip")
DataBasePath = os.path.join(AppPath, "ShaderToolsDatabase.sqlite")
ConfigPath = os.path.join(AppPath, "config")
HistoryPath = os.path.join(AppPath, "history")
TempPath = os.path.join(AppPath, "temp")
BookmarksPathUser = os.path.join(bpy.utils.resource_path('USER', major=bpy.app.version[0], minor=bpy.app.version[1]), "config", "bookmarks.txt")

#Defaults configuration values
DefaultCreator = "You"
DefaultDescription = "material description"
DefaultWeblink = "http://"
DefaultMaterialName = "Material"
DefaultCategory = "Personal"
DefaultEmail = "my_email@company.com"
Resolution_X = 120
Resolution_Y = 120

DefaultLanguage = 'en_US'
#Config Path :
if os.path.exists(ConfigPath) :
    config = open(ConfigPath, 'r')
    AppPath = config.readline().rstrip("\n")
    DataBasePath = config.readline().rstrip("\n")
    DefaultCreator = config.readline().rstrip("\n")
    DefaultDescription = config.readline().rstrip("\n")
    DefaultWeblink = config.readline().rstrip("\n")
    DefaultMaterialName = config.readline().rstrip("\n")
    DefaultCategory = config.readline().rstrip("\n")
    DefaultEmail = config.readline().rstrip("\n")
    Resolution_X = config.readline().rstrip("\n")
    Resolution_Y = config.readline().rstrip("\n")
    DefaultLanguage = config.readline().rstrip("\n")
else:
    config = open(ConfigPath,'w')
    config.write(AppPath + '\n')
    config.write(DataBasePath + '\n')
    config.write(DefaultCreator + '\n')
    config.write(DefaultDescription + '\n')
    config.write(DefaultWeblink + '\n')
    config.write(DefaultMaterialName + '\n')
    config.write(DefaultCategory + '\n')
    config.write(DefaultEmail + '\n')
    config.write(str(Resolution_X) + '\n')
    config.write(str(Resolution_Y) + '\n')
    config.write(DefaultLanguage + '\n')
#end if
config.close()


if os.path.exists(TempPath) :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            os.remove(os.path.join(TempPath, f))
        else:
            os.remove(os.path.join(TempPath, f))
else:
    os.makedirs(TempPath)

# ************************************************************************************
# *                                       HISTORY FILE                               *
# ************************************************************************************

def LoadHistory() :
    # returns the contents of the history file, if it exists.
    if os.path.exists(HistoryPath) :
        HISTORY_FILE = []
        history = open(HistoryPath, 'r')
        history.readline() # ignore "[HISTORY]" header
        for i, l in enumerate(history) :
            l = l.rstrip("\n")
            prefix = "History%d=" % (i + 1)
            if l.startswith(prefix) :
                l = l[len(prefix):]
            #end if
            HISTORY_FILE.append(l)
        #end for
        history.close()
    else :
        HISTORY_FILE = None
    #end if
    return HISTORY_FILE
#end LoadHistory

def SaveHistory(HISTORY_FILE) :
    # saves the specified list of items to the history file.
    history = open(HistoryPath, 'w')
    history.write("[HISTORY]\n")
    for i, l in enumerate(HISTORY_FILE) :
        history.write("History%d=%s\n" % (i + 1, l))
    #end for
    history.flush()
    history.close()
#end SaveHistory

HISTORY_FILE = LoadHistory()
if HISTORY_FILE == None :
    HISTORY_FILE = 20 * [""]
    SaveHistory(HISTORY_FILE)
#end if

# ************************************************************************************
# *                                     LANGUAGE PARAMETERS                           *
# ************************************************************************************

LanguageKeys = \
    { # sets of keys for language strings, grouped by category prefix
        "Panel" : {"Name"},
        "Buttons" :
            {
                "Open", "Save", "Configuration", "Export",
                "Import", "Help", "Informations", "Create",
            },
        "OpenMenu" : {"Title"} | set("Label%02d" % i for i in range(1, 10)),
        "BookmarksMenu" : {"Name"},
        "ErrorsMenu" : set("Error%03d" % i for i in range(1, 21)),
        "InformationsMenu" :
            {
                "Title", "LabelName", "Name", "LabelCreator", "Creator",
                "LabelCategory", "Category", "LabelDescription", "Description",
                "LabelWebLink", "WebLink", "LabelEmail", "Email",
            },
        "WarningWin" : {"Title"} | set("Label%02d" % i for i in range(1, 11)),
        "SaveMenu" :
                {
                    "Title", "Label01", "Name", "Creator", "CreatorValue",
                    "CategoryDefault", "DescriptionLabel", "Description",
                    "WebLinkLabel", "WebLink", "EmailLabel", "Email",
                }
            |
                set("Warning%02d" % i for i in range(1, 6)),
        "SaveCategory" :
                {"Title", "CategoryTitle"}
            |
                set(MaterialCategories),
        "ConfigurationMenu" :
                {"Title", "ResolutionPreviewX", "ResolutionPreviewY", "DataBasePath",}
            |
                set("Label%02d" % i for i in range(1, 6))
            |
                set("Warning%02d" % i for i in range(1, 6)),
        "ExportMenu" : {"Title", "Label01", "Name", "Creator", "CreatorDefault", "TakePreview"},
        "ImportMenu" : {"Title"},
        "HelpMenu" : {"Title"} | set("Label%02d" % i for i in range(1, 41)),
    }

def LoadLanguageValues(languageUser, languageDict) :
    saveCategoryConfig = None
    languageFile = open(os.path.join(AppPath, "lang", languageUser), "r", encoding = "utf-8")
    for readValue in languageFile:
        readValue = readValue.rstrip("\n")
        section = None
        if readValue.startswith("[") and readValue.endswith("]") :
            saveCategoryConfig = readValue[1:-1]
        elif "=" in readValue :
            section, sectionValue = readValue.split('=', 1)
        elif readValue == "*!-*" :
            saveCategoryConfig = None
        #end if
        if (
                section != None
            and
                saveCategoryConfig != None
            and
                saveCategoryConfig in LanguageKeys
            and
                section in LanguageKeys[saveCategoryConfig]
        ) :
            languageDict[saveCategoryConfig + section] = sectionValue
        #end if
    #end for
    languageFile.close()
#end LoadLanguageValues

#Open language file:
LanguageValuesDict = {}
for k in LanguageKeys :
    for j in LanguageKeys[k] :
        LanguageValuesDict[k + j] = ""
    #end for
#end for
language = locale.getdefaultlocale()[0]
if os.path.exists(os.path.join(AppPath, "lang", language)) :
    LoadLanguageValues(language, LanguageValuesDict)
else:
    LoadLanguageValues('en_US', LanguageValuesDict)

#+
# Useful database stuff
#-

def SQLIter(Conn, Cmd, MapFn = lambda x : x) :
    """executes cmd on a new cursor from connection Conn and yields
    the results in turn."""
    cu = Conn.cursor()
    cu.execute(Cmd)
    while True :
        # yield MapFn(cu.next()) # pre Python 3
        next = cu.fetchone() # Python 3
        if next == None :
            raise StopIteration
        #end if
        yield MapFn(next)
    #end while
#end SQLIter

def SQLString(s) :
    """returns an sqlite string literal that evalutes to s."""
    if s != None :
        if type(s) == bytes :
            q = "X'" + "".join("%02X" % b for b in s) + "'"
        else :
            q = "'" + str(s).replace("'", "''") + "'"
        #end if
    else :
        q = "null"
    #end if
    return q
#end SQLString

def GetEachRecord(Conn, TableName, Fields, Condition = None, Values = None, Extra = None) :
    """generator which does an SQL query which can return 0 or more
    result rows, yielding each record in turn as a mapping from field
    name to field value. TableName can be a single table name, or a
    comma-separated list of names for a join. Extra allows
    specification of order/group clauses."""
    FieldNames = []
    for Field in Fields :
        Components = Field.split(" as ", 1)
        if len(Components) == 2 :
            FieldNames.append(Components[1].lstrip())
        else :
            FieldNames.append(Field)
        #end if
    #end for
    Cmd = \
      (
            "select "
        +
            ", ".join(Fields)
        +
            " from "
        +
            TableName
      )
    if Condition != None :
        if Values != None :
            if type(Values) == dict :
                Condition = \
                    (
                        Condition
                    %
                        dict
                          (
                            (FieldName, SQLString(Values[FieldName])) for FieldName in Values.keys()
                          )
                    )
            else : # assume list or tuple
                Condition = Condition % tuple(SQLString(Value) for Value in Values)
            #end if
        #end if
        Cmd += " where " + Condition
    #end if
    if Extra != None :
        Cmd += " " + Extra
    #end if
    return SQLIter \
      (
        Conn = Conn,
        Cmd = Cmd,
        MapFn = lambda Row : dict(zip(FieldNames, Row))
      )
#end GetEachRecord

def GetRecords(Conn, TableName, Fields = None, Condition = None, Values = None, Extra = None, FieldDefs = None) :
    if Fields == None :
        Fields = FieldDefs.keys()
    #end if
    Result = list(GetEachRecord(Conn, TableName, Fields, Condition, Values, Extra))
    if FieldDefs != None :
        for record in Result :
            for field in record :
                if "convert_in" in FieldDefs[field] :
                    record[field] = FieldDefs[field]["convert_in"](record[field])
                #end if
            #end for
        #end for
    #end if
    return Result
#end GetRecords

def InsertRecord(Cursor, TableName, Fields) :
    """inserts a new record into the specified Table. Fields is
    a mapping from field names to field values. Note caller must
    do a commit at some point."""
    Cursor.execute \
      (
            "insert into "
        +
            TableName
        +
            "("
        +
            ", ".join(Fields.keys())
        +
            ") values ("
        +
            ", ".join(SQLString(v) for v in Fields.values())
        +
            ")"
      )
#end InsertRecord

def LastInsertID(Conn) :
    """returns the automatically-generated rowid field
    from the last insert operation."""
    Cursor = Conn.cursor()
    Cursor.execute("select last_insert_rowid()")
    return Cursor.fetchone()[0]
#end LastInsertID

#+
# Database definitions
#-

tobool = lambda x : x == 1 # inbound convertor for boolean-valued fields
frombool = lambda x : int(x) # outbound convertor for boolean-valued fields
material_fields = \
    { # key is database field name, value is dict with following fields:
      # "attr" : identifies Blender object attribute corresponding to this field value
      # "convert_in", "convert_out" : optional type conversion functions
        "Mat_Index" : {}, # primary key
        "Mat_Name" : {},
        "Mat_Type" : {},
        # entries below with no "attr" keys in their dicts are unused!
        "Mat_Preview_render_type" : {},
        "Mat_diffuse_color_r" : {"attr" : ("diffuse_color", 0)},
        "Mat_diffuse_color_g" : {"attr" : ("diffuse_color", 1)},
        "Mat_diffuse_color_b" : {"attr" : ("diffuse_color", 2)},
        "Mat_diffuse_color_a" : {}, # not used
        "Mat_diffuse_shader" : {"attr" : ("diffuse_shader",)},
        "Mat_diffuse_intensity" : {"attr" : ("diffuse_intensity",)},
        "Mat_use_diffuse_ramp" : {"attr" : ("use_diffuse_ramp",)},
        "Mat_diffuse_roughness" : {"attr" : ("roughness",)},
        "Mat_diffuse_toon_size" : {"attr" : ("diffuse_toon_size",)},
        "Mat_diffuse_toon_smooth" : {"attr" : ("diffuse_toon_smooth",)},
        "Mat_diffuse_darkness" : {"attr" : ("darkness",)},
        "Mat_diffuse_fresnel" : {"attr" : ("diffuse_fresnel",)},
        "Mat_diffuse_fresnel_factor" : {"attr" : ("diffuse_fresnel_factor",)},
        "Mat_specular_color_r" : {"attr" : ("specular_color", 0)},
        "Mat_specular_color_g" : {"attr" : ("specular_color", 1)},
        "Mat_specular_color_b" : {"attr" : ("specular_color", 2)},
        "Mat_specular_color_a" : {}, # not used
        "Mat_specular_shader" : {"attr" : ("specular_shader",)},
        "Mat_specular_intensity" : {"attr" : ("specular_intensity",)},
        "Mat_specular_ramp" : {}, # handled specially below
        "Mat_specular_hardness" : {"attr" : ("specular_hardness",)},
        "Mat_specular_ior" : {"attr" : ("specular_ior",)},
        "Mat_specular_toon_size" : {"attr" : ("specular_toon_size",)},
        "Mat_specular_toon_smooth" : {"attr" : ("specular_toon_smooth",)},
        "Mat_shading_emit" : {"attr" : ("emit",)},
        "Mat_shading_ambient" : {"attr" : ("ambient",)},
        "Mat_shading_translucency" : {"attr" : ("translucency",)},
        "Mat_shading_use_shadeless" : {"attr" : ("use_shadeless",)},
        "Mat_shading_use_tangent_shading" : {"attr" : ("use_tangent_shading",)},
        "Mat_shading_use_cubic" : {"attr" : ("use_cubic",)},
        "Mat_transparency_use_transparency" : {"attr" : ("use_transparency",)},
        "Mat_transparency_method" : {"attr" : ("transparency_method",)},
        "Mat_transparency_alpha" : {"attr" : ("alpha",)},
        "Mat_transparency_fresnel" : {"attr" : ("raytrace_transparency.fresnel",)},
        "Mat_transparency_specular_alpha" : {"attr" : ("specular_alpha",)},
        "Mat_transparency_fresnel_factor" : {"attr" : ("raytrace_transparency.fresnel_factor",)},
        "Mat_transparency_ior" : {"attr" : ("raytrace_transparency.ior",)},
        "Mat_transparency_filter" : {"attr" : ("raytrace_transparency.filter",)},
        "Mat_transparency_falloff" : {"attr" : ("raytrace_transparency.falloff",)},
        "Mat_transparency_depth_max" : {"attr" : ("raytrace_transparency.depth_max",)},
        "Mat_transparency_depth" : {"attr" : ("raytrace_transparency.depth",)},
        "Mat_transparency_gloss_factor" : {"attr" : ("raytrace_transparency.gloss_factor",)},
        "Mat_transparency_gloss_threshold" : {"attr" : ("raytrace_transparency.gloss_threshold",)},
        "Mat_transparency_gloss_samples" : {"attr" : ("raytrace_transparency.gloss_samples",)},
        "Mat_raytracemirror_use" : {"attr" : ("raytrace_mirror.use",)},
        "Mat_raytracemirror_reflect_factor" : {"attr" : ("raytrace_mirror.reflect_factor",)},
        "Mat_raytracemirror_fresnel" : {"attr" : ("raytrace_mirror.fresnel",)},
        "Mat_raytracemirror_color_r" : {"attr" : ("mirror_color", 0)},
        "Mat_raytracemirror_color_g" : {"attr" : ("mirror_color", 1)},
        "Mat_raytracemirror_color_b" : {"attr" : ("mirror_color", 2)},
        "Mat_raytracemirror_color_a" : {}, # not used
        "Mat_raytracemirror_fresnel_factor" : {"attr" : ("raytrace_mirror.fresnel_factor",)},
        "Mat_raytracemirror_depth" : {"attr" : ("raytrace_mirror.depth",)},
        "Mat_raytracemirror_distance" : {"attr" : ("raytrace_mirror.distance",)},
        "Mat_raytracemirror_fade_to" : {"attr" : ("raytrace_mirror.fade_to",)},
        "Mat_raytracemirror_gloss_factor" : {"attr" : ("raytrace_mirror.gloss_factor",)},
        "Mat_raytracemirror_gloss_threshold" : {"attr" : ("raytrace_mirror.gloss_threshold",)},
        "Mat_raytracemirror_gloss_samples" : {"attr" : ("raytrace_mirror.gloss_samples",)},
        "Mat_raytracemirror_gloss_anisotropic" : {"attr" : ("raytrace_mirror.gloss_anisotropic",)},
        "Mat_subsurfacescattering_use" : {"attr" : ("subsurface_scattering.use",)},
        "Mat_subsurfacescattering_presets" : {}, # not used
        "Mat_subsurfacescattering_ior" : {"attr" : ("subsurface_scattering.ior",)},
        "Mat_subsurfacescattering_scale" : {"attr" : ("subsurface_scattering.scale",)},
        "Mat_subsurfacescattering_color_r" : {"attr" : ("subsurface_scattering.color", 0)},
        "Mat_subsurfacescattering_color_g" : {"attr" : ("subsurface_scattering.color", 1)},
        "Mat_subsurfacescattering_color_b" : {"attr" : ("subsurface_scattering.color", 2)},
        "Mat_subsurfacescattering_color_a" : {}, # not used
        "Mat_subsurfacescattering_color_factor" : {"attr" : ("subsurface_scattering.color_factor",)},
        "Mat_subsurfacescattering_texture_factor" : {"attr" : ("subsurface_scattering.texture_factor",)},
        "Mat_subsurfacescattering_radius_one" : {"attr" : ("subsurface_scattering.radius", 0)},
        "Mat_subsurfacescattering_radius_two" : {"attr" : ("subsurface_scattering.radius", 1)},
        "Mat_subsurfacescattering_radius_three" : {"attr" : ("subsurface_scattering.radius", 2)},
        "Mat_subsurfacescattering_front" : {"attr" : ("subsurface_scattering.front",)},
        "Mat_subsurfacescattering_back" : {"attr" : ("subsurface_scattering.back",)},
        "Mat_subsurfacescattering_error_threshold" : {"attr" : ("subsurface_scattering.error_threshold",)},
        "Mat_strand_root_size" : {"attr" : ("strand.root_size",)},
        "Mat_strand_tip_size" : {"attr" : ("strand.tip_size",)},
        "Mat_strand_size_min" : {"attr" : ("strand.size_min",)},
        "Mat_strand_blender_units" : {"attr" : ("strand.use_blender_units",)},
        "Mat_strand_use_tangent_shading" : {"attr" : ("strand.use_tangent_shading",)},
        "Mat_strand_shape" : {"attr" : ("strand.shape",)},
        "Mat_strand_width_fade" : {"attr" : ("strand.width_fade",)},
        "Mat_strand_blend_distance" : {"attr" : ("strand.blend_distance",)},
        "Mat_options_use_raytrace" : {"attr" : ("use_raytrace",)},
        "Mat_options_use_full_oversampling" : {"attr" : ("use_full_oversampling",)},
        "Mat_options_use_sky" : {"attr" : ("use_sky",)},
        "Mat_options_use_mist" : {"attr" : ("use_mist",)},
        "Mat_options_invert_z" : {"attr" : ("invert_z",)},
        "Mat_options_offset_z" : {"attr" : ("offset_z",)},
        "Mat_options_use_face_texture" : {"attr" : ("use_face_texture",)},
        "Mat_options_use_texture_alpha" : {"attr" : ("use_face_texture_alpha",)},
        "Mat_options_use_vertex_color_paint" : {"attr" : ("use_vertex_color_paint",)},
        "Mat_options_use_vertex_color_light" : {"attr" : ("use_vertex_color_light",)},
        "Mat_options_use_object_color" : {"attr" : ("use_object_color",)},
        "Mat_options_pass_index" : {"attr" : ("pass_index",)},
        "Mat_shadow_use_shadows" : {"attr" : ("use_shadows",)},
        "Mat_shadow_use_transparent_shadows" : {"attr" : ("use_transparent_shadows",)},
        "Mat_shadow_use_cast_shadows_only" : {"attr" : ("use_cast_shadows_only",)},
        "Mat_shadow_shadow_cast_alpha" : {"attr" : ("shadow_cast_alpha",)},
        "Mat_shadow_use_only_shadow" : {"attr" : ("use_only_shadow",)},
        "Mat_shadow_shadow_only_type" : {"attr" : ("shadow_only_type",)},
        "Mat_shadow_use_cast_buffer_shadows" : {"attr" : ("use_cast_buffer_shadows",)},
        "Mat_shadow_shadow_buffer_bias" : {"attr" : ("shadow_buffer_bias",)},
        "Mat_shadow_use_ray_shadow_bias" : {"attr" : ("use_ray_shadow_bias",)},
        "Mat_shadow_shadow_ray_bias" : {"attr" : ("shadow_ray_bias",)},
        "Mat_shadow_use_cast_approximate" : {"attr" : ("use_cast_approximate",)},
        # entries above with no "attr" keys in their dicts are unused!
        # following fields really useless, should be removed:
        "Idx_ramp_diffuse" : {},
        "Idx_ramp_specular" : {},
        "Idx_textures" : {},
    }
for \
    field \
in \
    (
        "Mat_use_diffuse_ramp",
        "Mat_shading_use_shadeless",
        "Mat_shading_use_cubic",
        "Mat_shading_use_tangent_shading",
        "Mat_shading_use_cubic",
        "Mat_transparency_use_transparency",
        "Mat_raytracemirror_use",
        "Mat_subsurfacescattering_use",
        "Mat_strand_blender_units",
        "Mat_strand_use_tangent_shading",
        "Mat_options_use_raytrace",
        "Mat_options_use_full_oversampling",
        "Mat_options_use_sky",
        "Mat_options_use_mist",
        "Mat_options_invert_z",
        "Mat_options_use_face_texture",
        "Mat_options_use_texture_alpha",
        "Mat_options_use_vertex_color_paint",
        "Mat_options_use_vertex_color_light",
        "Mat_options_use_object_color",
        "Mat_shadow_use_shadows",
        "Mat_shadow_use_transparent_shadows",
        "Mat_shadow_use_cast_shadows_only",
        "Mat_shadow_use_only_shadow",
        "Mat_shadow_use_cast_buffer_shadows",
        "Mat_shadow_use_ray_shadow_bias",
        "Mat_shadow_use_cast_approximate",
    ) \
:
    material_fields[field]["convert_in"] = tobool
    material_fields[field]["convert_out"] = frombool
#end for

texture_fields = \
    { # key is database field name, value is dict with following fields:
      # "attr" : identifies Blender object attribute corresponding to this field value
      # "convert_in", "convert_out" : optional type conversion function
      # "type": optional field indicating attribute is specific to a texture type
        "Tex_Index" : {}, # primary key
        "Tex_Name" : {},
        "Tex_Type" : {},
        "Tex_Preview_type" : {},
        "Tex_use_preview_alpha" : {"attr" : ("texture.use_preview_alpha",)},
        "Tex_type_blend_progression" : {"attr" : ("texture.progression",)},
        "Tex_type_blend_use_flip_axis" : {"attr" : ("texture.use_flip_axis",)},
        "Tex_type_clouds_cloud_type" : {"attr" : ("texture.cloud_type",)},
        "Tex_type_clouds_noise_type" : {"attr" : ("texture.noise_type",)},
        "Tex_type_clouds_noise_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_noise_distortion" : {}, # superfluous, "Tex_type_noise_distortion_noise_distortion" used instead
        "Tex_type_env_map_source" : {"attr" : ("texture.environment_map.source",)},
        "Tex_type_env_map_mapping" : {"attr" : ("texture.environment_map.mapping",)},
        "Tex_type_env_map_clip_start" : {"attr" : ("texture.environment_map.clip_start",)},
        "Tex_type_env_map_clip_end" : {"attr" : ("texture.environment_map.clip_end",)},
        "Tex_type_env_map_resolution" : {"attr" : ("texture.environment_map.resolution",)},
        "Tex_type_env_map_depth" : {"attr" : ("texture.environment_map.depth",)},
        "Tex_type_env_map_image_file" : {}, # fixme: not supported yet
        "Tex_type_env_map_zoom" : {"attr" : ("texture.environment_map.zoom",)},
        "Tex_type_magic_depth" : {"attr" : ("texture.noise_depth",)},
        "Tex_type_magic_turbulence" : {"attr" : ("texture.turbulence",)},
        "Tex_type_marble_marble_type" : {"attr" : ("texture.marble_type",)},
        "Tex_type_marble_noise_basis_2" : {"attr" : ("texture.noise_basis_2",)},
        "Tex_type_marble_noise_type" : {"attr" : ("texture.noise_type",)},
        "Tex_type_marble_noise_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_marble_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_marble_noise_depth" : {"attr" : ("texture.noise_depth",)},
        "Tex_type_marble_turbulence" : {"attr" : ("texture.turbulence",)},
        "Tex_type_marble_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_musgrave_type" : {"attr" : ("texture.musgrave_type",)},
        "Tex_type_musgrave_dimension_max" : {"attr" : ("texture.dimension_max",)},
        "Tex_type_musgrave_lacunarity" : {"attr" : ("texture.lacunarity",)},
        "Tex_type_musgrave_octaves" : {"attr" : ("texture.octaves",)},
        "Tex_type_musgrave_noise_intensity" : {"attr" : ("texture.noise_intensity",)},
        "Tex_type_musgrave_noise_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_musgrave_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_musgrave_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_musgrave_offset" : {"attr" : ("texture.offset",)},
        "Tex_type_musgrave_gain" : {"attr" : ("texture.gain",)},
        "Tex_type_clouds_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_clouds_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_clouds_noise_depth" : {"attr" : ("texture.noise_depth",)},
        "Tex_type_noise_distortion_distortion" : {"attr" : ("texture.distortion",)},
        "Tex_type_noise_distortion_texture_distortion" : {}, # superfluous, "Tex_type_noise_distortion_basis" used instead
        "Tex_type_noise_distortion_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_noise_distortion_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_noise_distortion_noise_distortion" : {"attr" : ("texture.noise_distortion",)},
        "Tex_type_noise_distortion_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_point_density_point_source" : {"attr" : ("texture.point_density.point_source",)},
        "Tex_type_point_density_radius" : {"attr" : ("texture.point_density.radius",)},
        "Tex_type_point_density_particule_cache_space" : {"attr" : ("texture.point_density.particle_cache_space",)},
        "Tex_type_point_density_falloff" : {"attr" : ("texture.point_density.falloff",)},
        "Tex_type_point_density_use_falloff_curve" : {"attr" : ("texture.point_density.use_falloff_curve",)},
        "Tex_type_point_density_falloff_soft" : {"attr" : ("texture.point_density.falloff_soft",)},
        "Tex_type_point_density_falloff_speed_scale" : {"attr" : ("texture.point_density.falloff_speed_scale",)},
        "Tex_type_point_density_speed_scale" : {"attr" : ("texture.point_density.speed_scale",)},
        "Tex_type_point_density_color_source" : {"attr" : ("texture.point_density.color_source",)},
        "Tex_type_stucci_type" : {"attr" : ("texture.stucci_type",)},
        "Tex_type_stucci_noise_type" : {"attr" : ("texture.noise_type",)},
        "Tex_type_stucci_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_stucci_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_stucci_turbulence" : {"attr" : ("texture.turbulence",)},
        "Tex_type_voronoi_distance_metric" : {"attr" : ("texture.distance_metric",)},
        "Tex_type_voronoi_minkovsky_exponent" : {"attr" : ("texture.minkovsky_exponent",)},
        "Tex_type_voronoi_color_mode" : {"attr" : ("texture.color_mode",)},
        "Tex_type_voronoi_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_voronoi_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_voronoi_weight_1" : {"attr" : ("texture.weight_1",)},
        "Tex_type_voronoi_weight_2" : {"attr" : ("texture.weight_2",)},
        "Tex_type_voronoi_weight_3" : {"attr" : ("texture.weight_3",)},
        "Tex_type_voronoi_weight_4" : {"attr" : ("texture.weight_4",)},
        "Tex_type_voronoi_intensity" : {"attr" : ("texture.noise_intensity",)},
        "Tex_type_voxel_data_file_format" : {"attr" : ("texture.voxel_data.file_format",)},
        "Tex_type_voxel_data_source_path" : {"attr" : ("texture.voxel_data.filepath",)},
        "Tex_type_voxel_data_use_still_frame" : {"attr" : ("texture.voxel_data.use_still_frame",)},
        "Tex_type_voxel_data_still_frame" : {"attr" : ("texture.voxel_data.still_frame",)},
        "Tex_type_voxel_data_interpolation" : {"attr" : ("texture.voxel_data.interpolation",)},
        "Tex_type_voxel_data_extension" : {"attr" : ("texture.voxel_data.extension",)},
        "Tex_type_voxel_data_intensity" : {"attr" : ("texture.voxel_data.intensity",)},
        "Tex_type_voxel_data_resolution_1" : {"attr" : ("texture.voxel_data.resolution", 0)},
        "Tex_type_voxel_data_resolution_2" : {"attr" : ("texture.voxel_data.resolution", 1)},
        "Tex_type_voxel_data_resoltion_3" : {"attr" : ("texture.voxel_data.resolution", 2)},
        "Tex_type_voxel_data_smoke_data_type" : {"attr" : ("texture.voxel_data.smoke_data_type",)},
        "Tex_type_wood_noise_basis_2" : {"attr" : ("texture.noise_basis_2",)},
        "Tex_type_wood_wood_type" : {"attr" : ("texture.wood_type",)},
        "Tex_type_wood_noise_type" : {"attr" : ("texture.noise_type",)},
        "Tex_type_wood_basis" : {"attr" : ("texture.noise_basis",)},
        "Tex_type_wood_noise_scale" : {"attr" : ("texture.noise_scale",)},
        "Tex_type_wood_nabla" : {"attr" : ("texture.nabla",)},
        "Tex_type_wood_turbulence" : {"attr" : ("texture.turbulence",)},
        "Tex_influence_use_map_diffuse" : {"attr" : ("use_map_diffuse",)},
        "Tex_influence_use_map_color_diffuse" : {"attr" : ("use_map_color_diffuse",)},
        "Tex_influence_use_map_alpha" : {"attr" : ("use_map_alpha",)},
        "Tex_influence_use_map_translucency" : {"attr" : ("use_map_translucency",)},
        "Tex_influence_use_map_specular" : {"attr" : ("use_map_specular",)},
        "Tex_influence_use_map_color_spec" : {"attr" : ("use_map_color_spec",)},
        "Tex_influence_use_map_map_hardness" : {"attr" : ("use_map_hardness",)},
        "Tex_influence_use_map_ambient" : {"attr" : ("use_map_ambient",)},
        "Tex_influence_use_map_emit" : {"attr" : ("use_map_emit",)},
        "Tex_influence_use_map_mirror" : {"attr" : ("use_map_mirror",)},
        "Tex_influence_use_map_raymir" : {"attr" : ("use_map_raymir",)},
        "Tex_influence_use_map_normal" : {"attr" : ("use_map_normal",)},
        "Tex_influence_use_map_warp" : {"attr" : ("use_map_warp",)},
        "Tex_influence_use_map_displacement" : {"attr" : ("use_map_displacement",)},
        "Tex_influence_use_map_rgb_to_intensity" : {"attr" : ("use_rgb_to_intensity",)},
        "Tex_influence_map_invert" : {"attr" : ("invert",)},
        "Tex_influence_use_stencil" : {"attr" : ("use_stencil",)},
        "Tex_influence_diffuse_factor" : {"attr" : ("diffuse_factor",)},
        "Tex_influence_color_factor" : {"attr" : ("diffuse_color_factor",)},
        "Tex_influence_alpha_factor" : {"attr" : ("alpha_factor",)},
        "Tex_influence_translucency_factor" : {"attr" : ("translucency_factor",)},
        "Tex_influence_specular_factor" : {"attr" : ("specular_factor",)},
        "Tex_influence_specular_color_factor" : {"attr" : ("specular_color_factor",)},
        "Tex_influence_hardness_factor" : {"attr" : ("hardness_factor",)},
        "Tex_influence_ambiant_factor" : {"attr" : ("ambient_factor",)},
        "Tex_influence_emit_factor" : {"attr" : ("emit_factor",)},
        "Tex_influence_mirror_factor" : {"attr" : ("mirror_factor",)},
        "Tex_influence_raymir_factor" : {"attr" : ("raymir_factor",)},
        "Tex_influence_normal_factor" : {"attr" : ("normal_factor",)},
        "Tex_influence_warp_factor" : {"attr" : ("warp_factor",)},
        "Tex_influence_displacement_factor" : {"attr" : ("displacement_factor",)},
        "Tex_influence_default_value" : {"attr" : ("default_value",)},
        "Tex_influence_blend_type" : {"attr" : ("blend_type",)},
        "Tex_influence_color_r" : {"attr" : ("color", 0)},
        "Tex_influence_color_g" : {"attr" : ("color", 1)},
        "Tex_influence_color_b" : {"attr" : ("color", 2)},
        "Tex_influence_color_a" : {}, # unused?
        "Tex_influence_bump_method" : {"attr" : ("bump_method",)},
        "Tex_influence_objectspace" : {"attr" : ("bump_objectspace",)},
        "Tex_mapping_texture_coords" : {"attr" : ("texture_coords",)},
        "Tex_mapping_mapping" : {"attr" : ("mapping",)},
        "Tex_mapping_use_from_dupli" : {}, # attr handled specially below
        "Tex_mapping_mapping_x" : {"attr" : ("mapping_x",)},
        "Tex_mapping_mapping_y" : {"attr" : ("mapping_y",)},
        "Tex_mapping_mapping_z" : {"attr" : ("mapping_z",)},
        "Tex_mapping_offset_x" : {"attr" : ("offset", 0)},
        "Tex_mapping_offset_y" : {"attr" : ("offset", 1)},
        "Tex_mapping_offset_z" : {"attr" : ("offset", 2)},
        "Tex_mapping_scale_x" : {"attr" : ("scale", 0)},
        "Tex_mapping_scale_y" : {"attr" : ("scale", 1)},
        "Tex_mapping_scale_z" : {"attr" : ("scale", 2)},
        "Tex_mapping_use_from_original" : {}, # attr handled specially below
        "Tex_colors_use_color_ramp" : {"attr" : ("texture.use_color_ramp",)},
        "Tex_colors_factor_r" : {"attr" : ("texture.factor_red",)},
        "Tex_colors_factor_g" : {"attr" : ("texture.factor_green",)},
        "Tex_colors_factor_b" : {"attr" : ("texture.factor_blue",)},
        "Tex_colors_intensity" : {"attr" : ("texture.intensity",)},
        "Tex_colors_contrast" : {"attr" : ("texture.contrast",)},
        "Tex_colors_saturation" : {"attr" : ("texture.saturation",)},
        "Mat_Idx" : {}, # Mat_Index value for parent material 
        # following fields really useless, should be removed:
        "Poi_Idx" : {},
        "Col_Idx" : {},
    }
for \
    field \
in \
    (
        "Tex_use_preview_alpha",
        "Tex_type_point_density_use_falloff_curve",
        "Tex_type_voxel_data_use_still_frame",
        "Tex_influence_use_map_diffuse",
        "Tex_influence_use_map_color_diffuse",
        "Tex_influence_use_map_alpha",
        "Tex_influence_use_map_translucency",
        "Tex_influence_use_map_specular",
        "Tex_influence_use_map_color_spec",
        "Tex_influence_use_map_map_hardness",
        "Tex_influence_use_map_ambient",
        "Tex_influence_use_map_emit",
        "Tex_influence_use_map_mirror",
        "Tex_influence_use_map_raymir",
        "Tex_influence_use_map_normal",
        "Tex_influence_use_map_warp",
        "Tex_influence_use_map_displacement",
        "Tex_influence_use_map_rgb_to_intensity",
        "Tex_influence_map_invert",
        "Tex_influence_use_stencil",
        "Tex_mapping_use_from_dupli",
        "Tex_colors_use_color_ramp",
        "Tex_mapping_use_from_original",
    ) \
:
    texture_fields[field]["convert_in"] = tobool
    texture_fields[field]["convert_out"] = frombool
#end for
for \
    tex_type, tex_name \
in \
    ( # luckily type-specific fields are named in a systematic way
        ("ENVIRONMENT_MAP", "env_map"),
        ("MAGIC", "magic"),
        ("MARBLE", "marble"),
        ("MUSGRAVE", "musgrave"),
        ("DISTORTED_NOISE", "noise_distortion"),
        ("STUCCI", "stucci"),
        ("VORONOI", "voronoi"),
        ("VOXEL_DATA", "voxel_data"),
        ("WOOD", "wood"),
        ("BLEND", "blend"),
        ("POINT_DENSITY", "point_density"),
        # IMAGE handled specially below
        ("CLOUDS", "clouds"),
    ) \
:
    for field in texture_fields :
        if field.startswith("Tex_type_" + tex_name + "_") :
            texture_fields[field]["type"] = tex_type
        #end for
    #end for
#end for
del tex_type, tex_name

color_ramp_fields = \
    {
        "Col_Index" : {}, # primary key
        "Col_Num_Material" : {}, # not really needed
        "Col_Num_Texture" : {}, # Tex_Index value for parent texture
        "Col_Flip" : {}, # not used?
        "Col_Active_color_stop" : {},
        "Col_Between_color_stop" : {}, # not really needed
        "Col_Interpolation" : {},
        "Col_Position" : {},
        "Col_Color_stop_one_r" : {},
        "Col_Color_stop_one_g" : {},
        "Col_Color_stop_one_b" : {},
        "Col_Color_stop_one_a" : {},
        "Col_Color_stop_two_r" : {}, # not used?
        "Col_Color_stop_two_g" : {}, # not used?
        "Col_Color_stop_two_b" : {}, # not used?
        "Col_Color_stop_two_a" : {}, # not used?
        # also in database schema, but not used:
        # "Col_Ramp_input",
        # "Col_Ramp_blend",
        # "Col_Ramp_factor",
    }
for \
    field \
in \
    (
        "Col_Flip",
    ) \
:
    color_ramp_fields[field]["convert_in"] = tobool
    color_ramp_fields[field]["convert_out"] = frombool
#end for

pointdensity_ramp_fields = \
    {
        "Poi_Index" : {}, # primary key
        "Poi_Num_Material" : {}, # not really needed
        "Poi_Num_Texture" : {}, # Tex_Index value for parent texture
        "Poi_Flip" : {}, # not used?
        "Poi_Active_color_stop" : {}, # not really needed
        "Poi_Between_color_stop" : {}, # not really needed
        "Poi_Interpolation" : {},
        "Poi_Position" : {},
        "Poi_Color_stop_one_r" : {},
        "Poi_Color_stop_one_g" : {},
        "Poi_Color_stop_one_b" : {},
        "Poi_Color_stop_one_a" : {},
        "Poi_Color_stop_two_r" : {}, # not used?
        "Poi_Color_stop_two_g" : {}, # not used?
        "Poi_Color_stop_two_b" : {}, # not used?
        "Poi_Color_stop_two_a" : {}, # not used?
        # also in database schema, but not used:
        # "Poi_Ramp_input",
        # "Poi_Ramp_blend",
        # "Poi_Ramp_factor",
    }
for \
    field \
in \
    (
        "Poi_Flip",
    ) \
:
    pointdensity_ramp_fields[field]["convert_in"] = tobool
    pointdensity_ramp_fields[field]["convert_out"] = frombool
#end for

diffuse_ramp_fields = \
    {
        "Dif_Index" : {}, # primary key
        "Dif_Num_material" : {}, # Mat_Index value for parent material
        "Dif_Flip" : {}, # not used?
        "Dif_Active_color_stop" : {}, # not really needed
        "Dif_Between_color_stop" : {}, # not really needed
        "Dif_Interpolation" : {},
        "Dif_Position" : {},
        "Dif_Color_stop_one_r" : {},
        "Dif_Color_stop_one_g" : {},
        "Dif_Color_stop_one_b" : {},
        "Dif_Color_stop_one_a" : {},
        "Dif_Color_stop_two_r" : {}, # not used?
        "Dif_Color_stop_two_g" : {}, # not used?
        "Dif_Color_stop_two_b" : {}, # not used?
        "Dif_Color_stop_two_a" : {}, # not used?
        "Dif_Ramp_input" : {},
        "Dif_Ramp_blend" : {},
        "Dif_Ramp_factor" : {},
    }
for \
    field \
in \
    (
        "Dif_Flip",
    ) \
:
    diffuse_ramp_fields[field]["convert_in"] = tobool
    diffuse_ramp_fields[field]["convert_out"] = frombool
#end for

specular_ramp_fields = \
    {
        "Spe_Index" : {}, # primary key
        "Spe_Num_Material" : {}, # Mat_Index value for parent material
        "Spe_Flip" : {}, # not used?
        "Spe_Active_color_stop" : {}, # not really needed
        "Spe_Between_color_stop" : {}, # not really needed
        "Spe_Interpolation" : {},
        "Spe_Position" : {},
        "Spe_Color_stop_one_r" : {},
        "Spe_Color_stop_one_g" : {},
        "Spe_Color_stop_one_b" : {},
        "Spe_Color_stop_one_a" : {},
        "Spe_Color_stop_two_r" : {}, # not used?
        "Spe_Color_stop_two_g" : {}, # not used?
        "Spe_Color_stop_two_b" : {}, # not used?
        "Spe_Color_stop_two_a" : {}, # not used?
        "Spe_Ramp_input" : {},
        "Spe_Ramp_blend" : {},
        "Spe_Ramp_factor" : {},
    }
for \
    field \
in \
    (
        "Spe_Flip",
    ) \
:
    specular_ramp_fields[field]["convert_in"] = tobool
    specular_ramp_fields[field]["convert_out"] = frombool
#end for

image_uv_fields = \
    (
        "Ima_Index", # primary key
        "Idx_Texture", # Tex_Index value for parent texture
        "Ima_Name",
        "Ima_Source", # saved, but not loaded?
        "Ima_Filepath",
        "Ima_Fileformat",
        "Ima_Fields", # should be boolean
        "Ima_Premultiply", # should be boolean
        "Ima_Fields_order",
        "Ima_Generated_type", # saved, but not loaded?
        "Ima_Generated_width", # saved, but not loaded?
        "Ima_Generated_height", # saved, but not loaded?
        "Ima_Float_buffer", # saved, but not loaded?
        "Ima_Blob",
    )

del tobool, frombool, field

# fixme: "RENDER" and "INFORMATIONS" tables seem to always have 1:1 record correspondence
# with "MATERIALS" table: this suggests they should not be separate tables, instead
# their fields should be put into "MATERIALS".

# ************************************************************************************
# *                                    IMPORTER SQL                                  *
# ************************************************************************************
def ImporterSQL(SearchName):
    # imports the material with the specified name from the database, and attaches
    # it to the current object (there must be one).

    print()
    print("                                        *****                         ")
    print()
    print("*******************************************************************************")
    print("*                                IMPORT BASE MATERIAL                         *")
    print("*******************************************************************************")

    ShaderToolsDatabase = sqlite3.connect(DataBasePath)

    MyMaterialIndex = 2 # default to lowest valid value in database
    #I split material name and i return material index
    for value in SearchName.split('_Ind_', 255):
        if value.endswith('.jpg'):
            MyMaterialIndex = stripext(value, '.jpg')

    Material = GetRecords \
      (
        Conn = ShaderToolsDatabase,
        TableName = "MATERIALS",
        Condition = "Mat_Index = %s",
        Values = [MyMaterialIndex],
        FieldDefs = material_fields
      )[0] # assume exactly 1 record
    Mat_Name = Material["Mat_Name"]

    #Here I restore imported values in Blender:
    obj = bpy.context.object
      # won't be None, because this script is only invocable via a custom panel
      # in the Materials tab in the Properties window, and that tab only appears
      # when something is selected that can take a material.

    def SetupObject(obj, fields, fielddefs, include = lambda field : True) :
        # common routine for converting field values into new attribute
        # values for an object.
        for field in fields :
            if include(field) :
                attr = fielddefs[field].get("attr")
                if attr != None :
                    idx = None
                    if len(attr) > 1 :
                        attr, idx = attr
                    else :
                        attr = attr[0]
                    #end if
                    attr = attr.split(".")
                    if idx == None :
                        attrtoset = attr[-1]
                        attr = attr[:-1]
                    #end if
                    subobj = obj
                    for name in attr :
                        subobj = getattr(subobj, name)
                    #end for
                    if idx != None :
                        subobj[idx] = fields[field]
                    else :
                        setattr(subobj, attrtoset, fields[field])
                    #end if
                #end if
            #end if
        #end for
        return obj
    #end SetupObject

    # Create Material :
    bpy.ops.object.material_slot_add()
    obj.material_slots[-1].material = SetupObject \
      (
        bpy.data.materials.new(Mat_Name),
        Material,
        material_fields
      )

    MyTextureResult = GetRecords \
      (
        Conn = ShaderToolsDatabase,
        TableName = "TEXTURES",
        Condition = "Mat_Idx = %s",
        Values = [MyMaterialIndex],
        FieldDefs = texture_fields
      ) # fixme: note no explicit ordering specified
    #I must extract IMAGES/UV before create Textures:
    MyTextureIdxResult = list(t["Tex_Index"] for t in MyTextureResult)
    Render = ""
    #I create a new folder contains all textures:
    CopyBlendFolder = ""
    Render_exists = False
    if os.path.exists(OutPath) :
        #Here I remove all files in this folder:
        files = os.listdir(OutPath)
        for f in files:
            if not os.path.isdir(f):
                os.remove(os.path.join(OutPath, f))
    else:
        os.makedirs(OutPath)

    #I must find all textures in database:
    for val in MyTextureIdxResult:
        if val != '' or val == None :
            #Now I generate image files:
            for \
                ThisImage \
            in \
                GetEachRecord \
                  (
                    Conn = ShaderToolsDatabase,
                    TableName = "IMAGE_UV",
                    Fields =
                        (
                            "Ima_Name",
                            "Ima_Filepath",
                            "Ima_Fileformat",
                            "Ima_Fields",
                            "Ima_Premultiply",
                            "Ima_Fields_order",
                            "Ima_Blob",
                        ),
                    Condition = "Idx_Texture = %s",
                    Values = [val]
                  ) \
            :
                MyImageUvRequest = ThisImage
                Render = ThisImage["Ima_Blob"]
                Render_exists = True
                if ThisImage["Ima_Name"] == '' :
                    adresse = os.path.join(OutPath, "error_save.jpg")
                    test = shutil.copy2(os.path.join(ErrorsPath, "error_save.jpg"), adresse)
                    ThisImage["Ima_filepath"] = os.path.join(AppPath, "error_save.jpg")
                else :
                    format_image = [".png", ".jpg", ".jpeg", ".tiff", ".tga", ".raw", ".bmp", ".hdr", ".gif", ".svg", ".wmf", ".pst"]
                    c = 0
                    for format in format_image:
                        if c == 0:
                            if ThisImage["Ima_Name"].endswith(format) :
                                adresse = os.path.join(OutPath, ThisImage["Ima_Name"])
                                c = 1

                            else:
                                adresse = os.path.join(OutPath, ThisImage["Ima_Name"] + "." +  ThisImage["Ima_Fileformat"])
                            #end if
                        #end if
                    #end for
                    generated_image = open(adresse,'wb')
                    generated_image.write(Render)
                    generated_image.close()
                #end if
            #end for
        #end if
    #end for

    #I copy all images files in ShaderToolsImport folder:
    print("*******************************************************")
    print(LanguageValuesDict['ErrorsMenuError001'])
    print(LanguageValuesDict['ErrorsMenuError006'])

    if Render_exists :
        # generate a unique folder name to hold the files
        c = 0
        while True :
            CopyBlendFolder = os.path.join(BlendPath, "ShaderToolsImport", Mat_Name + ("", "_%d" % c)[c != 0])
            if not os.path.exists(CopyBlendFolder) :
                # found unused name
                os.makedirs(CopyBlendFolder)
                break
            #end if
            # already exists, try another name
            c += 1
        #end while

        #Here I copy all files in Out Folder to ShaderToolsImport folder:
        files = os.listdir(OutPath)
        for f in files:
            if not os.path.isdir(f):
                shutil.copy2(os.path.join(OutPath, f), os.path.join(CopyBlendFolder, f))
    #end if

    #Now I treat textures informations
    for textureNumberSlot, ThisTexture in enumerate(MyTextureResult) :
        Tex_Type = ThisTexture["Tex_Type"]
        #Create texture :
        slot = obj.active_material.texture_slots.add()
        slot.texture = bpy.data.textures.new(name = ThisTexture["Tex_Name"], type = Tex_Type)
        SetupObject \
          (
            slot,
            ThisTexture,
            texture_fields,
            include = lambda field : texture_fields[field].get("type") in (None, Tex_Type)
          )
        if Tex_Type == 'POINT_DENSITY' :
            #My point density ramp:
            MyPointDensityRampResult = GetRecords \
              (
                Conn = ShaderToolsDatabase,
                TableName = "POINTDENSITY_RAMP",
                Condition = "Poi_Num_Texture = %s",
                Values = [ThisTexture["Tex_Index"]],
                FieldDefs = pointdensity_ramp_fields
              ) # fixme: note no explicit ordering specified
            RAMP_MIN_POSITION = 0.0
            RAMP_MAX_POSITION = 1.0
            if MyPointDensityRampResult != [] :
                ramp_last = len(MyPointDensityRampResult) - 1
                #Now I create ramps:
                for counter, values in enumerate(MyPointDensityRampResult) :
                    #Here my specular ramp :
                    ramp = bpy.context.object.active_material.texture_slots[textureNumberSlot].texture
                    if ramp.point_density.color_source == 'PARTICLE_SPEED' or ramp.point_density.color_source == 'PARTICLE_AGE' :
                        if counter == 0 :
                            #Here i get differentes color bands:
                            RAMP_MIN_POSITION = values["Poi_Position"]
                            ramp.point_density.color_ramp.elements[0].position = values["Poi_Position"]
                        #end if
                        if counter > 0 and counter < ramp_last:
                            #Here i get differentes color bands:
                            ramp.point_density.color_ramp.elements.new(position = values["Poi_Position"])
                        #end if
                        if counter == ramp_last :
                            RAMP_MAX_POSITION = values["Poi_Position"]
                            ramp.point_density.color_ramp.elements[counter].position = 1.0
                            #Debug first ramp and last ramp positions:
                            ramp.point_density.color_ramp.elements[0].position = RAMP_MIN_POSITION
                            ramp.point_density.color_ramp.elements[counter].position = RAMP_MAX_POSITION
                        #end if
                        ramp.point_density.color_ramp.interpolation  = values["Poi_Interpolation"]
                        ramp.point_density.color_ramp.elements[counter].color[0] = values["Poi_Color_stop_one_r"]
                        ramp.point_density.color_ramp.elements[counter].color[1] = values["Poi_Color_stop_one_g"]
                        ramp.point_density.color_ramp.elements[counter].color[2] = values["Poi_Color_stop_one_b"]
                        ramp.point_density.color_ramp.elements[counter].color[3] = values["Poi_Color_stop_one_a"]
                    #end if
                #end for
            #end if
        #end if

        if Tex_Type == 'IMAGE' :
            #I create image texture environnement:
            imagePath = os.path.join(CopyBlendFolder, MyImageUvRequest["Ima_Name"])
            img = bpy.data.images.load(filepath = imagePath)
            #Now I create file:
            slot.texture.image = img
            slot.texture.image.use_fields = MyImageUvRequest["Ima_Fields"]
            slot.texture.image.use_premultiply = MyImageUvRequest["Ima_Premultiply"]
            if MyImageUvRequest["Ima_Fields_order"] != '' : #Debug
                slot.texture.image.field_order = MyImageUvRequest["Ima_Fields_order"]
            #end if
        #end if

        if slot.texture_coords == 'UV' or slot.texture_coords == 'ORCO' :
            slot.use_from_dupli = ThisTexture["Tex_mapping_use_from_dupli"]
        #end if
        if slot.texture_coords == 'OBJECT' :
            slot.use_from_original = ThisTexture["Tex_mapping_use_from_original"]
        #end if

        #My colors ramp:
        MyColorRampResult = GetRecords \
          (
            Conn = ShaderToolsDatabase,
            TableName = "COLORS_RAMP",
            Condition = "Col_Num_Texture = %s",
            Values = [ThisTexture["Tex_Index"]],
            FieldDefs = color_ramp_fields
          ) # fixme: note no explicit ordering specified
        if MyColorRampResult != [] :
            ramp_last = len(MyColorRampResult) - 1
            #Now I create ramps:
            for counter, values in enumerate(MyColorRampResult) :
                #Here my specular ramp :
                ramp = bpy.context.object.active_material.texture_slots[textureNumberSlot].texture
                #Here my specular ramp :
                ramp.use_color_ramp = True
                if counter == 0 :
                    #Here i get differentes color bands:
                    RAMP_MIN_POSITION = values["Col_Position"]
                    ramp.color_ramp.elements[0].position = values["Col_Position"]
                #end if
                if counter > 0 and counter < ramp_last:
                    #Here i get differentes color bands:
                    ramp.color_ramp.elements.new(position = values["Col_Position"])
                #end if
                if counter == ramp_last :
                    RAMP_MAX_POSITION = values["Col_Position"]
                    ramp.color_ramp.elements[counter].position = 1.0
                    #Debug first ramp and last ramp positions:
                    ramp.color_ramp.elements[0].position = RAMP_MIN_POSITION
                    ramp.color_ramp.elements[counter].position = RAMP_MAX_POSITION
                #end if
                ramp.color_ramp.interpolation = values["Col_Interpolation"]
                ramp.color_ramp.elements[counter].color[0] = values["Col_Color_stop_one_r"]
                ramp.color_ramp.elements[counter].color[1] = values["Col_Color_stop_one_g"]
                ramp.color_ramp.elements[counter].color[2] = values["Col_Color_stop_one_b"]
                ramp.color_ramp.elements[counter].color[3] = values["Col_Color_stop_one_a"]
            #end for
        #end if MyColorRampResult != []
    #end for each texture

    #My diffuse ramp:
    MyDiffuseRampResult = GetRecords \
      (
        Conn = ShaderToolsDatabase,
        TableName = "DIFFUSE_RAMP",
        Condition = "Dif_Num_material = %s",
        Values = [MyMaterialIndex],
        FieldDefs = diffuse_ramp_fields
      ) # fixme: note no explicit ordering specified
    if MyDiffuseRampResult != [] :
        ramp_last = len(MyDiffuseRampResult) - 1
        #Now I create ramps:
        for counter, values in enumerate(MyDiffuseRampResult) :
            ramp = bpy.context.object.active_material
            ramp.use_diffuse_ramp = True
            if counter == 0 :
                #Here i get differentes color bands:
                RAMP_MIN_POSITION = values["Dif_Position"]
                ramp.diffuse_ramp.elements[0].position = values["Dif_Position"]
            #end if
            if counter > 0 and counter < ramp_last :
                #Here i get differentes color bands:
                ramp.diffuse_ramp.elements.new(position = values["Dif_Position"])
            #end if
            if counter == ramp_last :
                RAMP_MAX_POSITION = values["Dif_Position"]
                ramp.diffuse_ramp.elements[counter].position = 1.0
                #Debug first ramp and last ramp positions:
                ramp.diffuse_ramp.elements[0].position = RAMP_MIN_POSITION
                ramp.diffuse_ramp.elements[counter].position = RAMP_MAX_POSITION
            #end if
            ramp.diffuse_ramp_blend = values["Dif_Ramp_blend"]
            ramp.diffuse_ramp_input = values["Dif_Ramp_input"]
            ramp.diffuse_ramp_factor = values["Dif_Ramp_factor"]
            ramp.diffuse_ramp.interpolation = values["Dif_Interpolation"]
            ramp.diffuse_ramp.elements[counter].color[0] = values["Dif_Color_stop_one_r"]
            ramp.diffuse_ramp.elements[counter].color[1] = values["Dif_Color_stop_one_g"]
            ramp.diffuse_ramp.elements[counter].color[2] = values["Dif_Color_stop_one_b"]
            ramp.diffuse_ramp.elements[counter].color[3] = values["Dif_Color_stop_one_a"]
        #end for
    #end if

    #My specular ramp:
    MySpecularRampResult = GetRecords \
      (
        Conn = ShaderToolsDatabase,
        TableName = "SPECULAR_RAMP",
        Condition = "Spe_Num_Material = %s",
        Values = [MyMaterialIndex],
        FieldDefs = specular_ramp_fields
      ) # fixme: note no explicit ordering specified
    if MySpecularRampResult != []:
        ramp_last = len(MySpecularRampResult) - 1
        #Now I create ramps:
        for counter, values in enumerate(MySpecularRampResult) :
            ramp = bpy.context.object.active_material
            ramp.use_specular_ramp = True
            if counter == 0 :
                #Here i get differentes color bands:
                RAMP_MIN_POSITION = values["Spe_Position"]
                ramp.specular_ramp.elements[0].position = values["Spe_Position"]
            #end if
            if counter > 0 and counter < ramp_last :
                #Here i get differentes color bands:
                ramp.specular_ramp.elements.new(position = values["Spe_Position"])
            #end if
            if counter == ramp_last :
                RAMP_MAX_POSITION = values["Spe_Position"]
                ramp.specular_ramp.elements[counter].position = 1.0
                #Debug first ramp and last ramp positions:
                ramp.specular_ramp.elements[0].position = RAMP_MIN_POSITION
                ramp.specular_ramp.elements[counter].position = RAMP_MAX_POSITION
            #end if
            ramp.specular_ramp_blend = values["Spe_Ramp_blend"]
            ramp.specular_ramp_input = values["Spe_Ramp_input"]
            ramp.specular_ramp_factor = values["Spe_Ramp_factor"]
            ramp.specular_ramp.interpolation  = values["Spe_Interpolation"]
            ramp.specular_ramp.elements[counter].color[0] = values["Spe_Color_stop_one_r"]
            ramp.specular_ramp.elements[counter].color[1] = values["Spe_Color_stop_one_g"]
            ramp.specular_ramp.elements[counter].color[2] = values["Spe_Color_stop_one_b"]
            ramp.specular_ramp.elements[counter].color[3] = values["Spe_Color_stop_one_a"]
        #end for
    #end if

    ShaderToolsDatabase.close()
#end ImporterSQL


# ************************************************************************************
# *                                         EXPORTER                                 *
# ************************************************************************************
def Exporter(File_Path, Mat_Name, Inf_Creator, TakePreview):
    print()
    print("                                      *****                         ")
    print()
    print("*******************************************************************************")
    print("*                              EXPORT MATERIAL (.BLEX)                        *")
    print("*******************************************************************************")

    obj = bpy.context.object
    tex = bpy.context.active_object.active_material

    #Here I verify if Zip Folder exists:
    if not os.path.exists(ZipPath) :
        os.makedirs(ZipPath)

    #Here I remove all files in Zip Folder:
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f):
            os.remove(os.path.join(ZipPath, f))

    #I create a list before export material/textures configuration :
    MY_EXPORT_INFORMATIONS = ['# ****************************************************************\n',
                              '# Material name : ' + Mat_Name + '\n',
                              '# Created by ' + Inf_Creator + '\n',
                              '#           With Blender3D and BlenderShadersTools Add-on\n',
                              '# ****************************************************************\n',
                              '\n',
                              '# Imports :\n',
                              'import bpy\n',
                              'import os\n',
                              '\n',
                              '# Context :\n',
                              'obj = bpy.context.object\n',
                              'tex = bpy.context.active_object.active_material\n',
                              '\n',
                              '# Script Path :\n',
                              'Mat_Name = "' + Mat_Name + '"\n',
                              'Inf_Creator = "' + Inf_Creator + '"\n',
                              '!*- environnement path -*!\n',
                              '\n',
                              'test = Mat_Name + "_" + Inf_Creator + ".py"\n',
                              'scriptPath = scriptPath.replace(test, "")\n',
                              '\n',
                              '# Create Material :\n',
                              'def CreateMaterial(Mat_Name):\n',
                              '\t# Materials Values :\n',
                              '\tmat = bpy.data.materials.new(Mat_Name)\n',
                              '\tmat.diffuse_color[0] = ' + str(obj.active_material.diffuse_color[0]) + '\n',
                              '\tmat.diffuse_color[1] = ' + str(obj.active_material.diffuse_color[1]) + '\n',
                              '\tmat.diffuse_color[2] = ' + str(obj.active_material.diffuse_color[2]) + '\n',
                              '\tmat.diffuse_shader = "' + str(obj.active_material.diffuse_shader) + '"\n',
                              '\tmat.diffuse_intensity = ' + str(obj.active_material.diffuse_intensity) + '\n',
                              '\tmat.roughness = ' + str(obj.active_material.roughness) + '\n',
                              '\tmat.diffuse_toon_size = ' + str(obj.active_material.diffuse_toon_size) + '\n',
                              '\tmat.diffuse_toon_smooth = ' + str(obj.active_material.diffuse_toon_smooth) + '\n',
                              '\tmat.darkness  = ' + str(obj.active_material.darkness) + '\n',
                              '\tmat.diffuse_fresnel = ' + str(obj.active_material.diffuse_fresnel) + '\n',
                              '\tmat.diffuse_fresnel_factor  = ' + str(obj.active_material.diffuse_fresnel_factor) + '\n',
                              '\tmat.specular_shader  = "' + str(obj.active_material.specular_shader) + '"\n',
                              '\tmat.specular_color[0] = ' + str(obj.active_material.specular_color[0]) + '\n',
                              '\tmat.specular_color[1] = ' + str(obj.active_material.specular_color[1]) + '\n',
                              '\tmat.specular_color[2] = ' + str(obj.active_material.specular_color[2]) + '\n',
                              '\tmat.specular_intensity = ' + str(obj.active_material.specular_intensity) + '\n',
                              '\tmat.specular_hardness = ' + str(obj.active_material.specular_hardness) + '\n',
                              '\tmat.specular_ior = ' + str(obj.active_material.specular_ior) + '\n',
                              '\tmat.specular_toon_size = ' + str(obj.active_material.specular_toon_size) + '\n',
                              '\tmat.specular_toon_smooth = ' + str(obj.active_material.specular_toon_smooth) + '\n',
                              '\tmat.emit = ' + str(obj.active_material.emit) + '\n',
                              '\tmat.ambient  = ' + str(obj.active_material.ambient) + '\n',
                              '\tmat.translucency = ' + str(obj.active_material.translucency) + '\n',
                              '\tmat.use_shadeless = ' + str(obj.active_material.use_shadeless) + '\n',
                              '\tmat.use_tangent_shading = ' + str(obj.active_material.use_tangent_shading) + '\n',
                              '\tmat.use_transparency = ' + str(obj.active_material.use_transparency) + '\n',
                              '\tmat.transparency_method = "' + str(obj.active_material.transparency_method) + '"\n',
                              '\tmat.alpha = ' + str(obj.active_material.alpha) + '\n',
                              '\tmat.raytrace_transparency.fresnel = ' + str(obj.active_material.raytrace_transparency.fresnel) + '\n',
                              '\tmat.specular_alpha = ' + str(obj.active_material.specular_alpha) + '\n',
                              '\tmat.raytrace_transparency.fresnel_factor = ' + str(obj.active_material.raytrace_transparency.fresnel_factor) + '\n',
                              '\tmat.raytrace_transparency.ior = ' + str(obj.active_material.raytrace_transparency.ior) + '\n',
                              '\tmat.raytrace_transparency.filter = ' + str(obj.active_material.raytrace_transparency.filter) + '\n',
                              '\tmat.raytrace_transparency.falloff = ' + str(obj.active_material.raytrace_transparency.falloff) + '\n',
                              '\tmat.raytrace_transparency.depth_max = ' + str(obj.active_material.raytrace_transparency.depth_max) + '\n',
                              '\tmat.raytrace_transparency.depth = ' + str(obj.active_material.raytrace_transparency.depth) + '\n',
                              '\tmat.raytrace_transparency.gloss_factor = ' + str(obj.active_material.raytrace_transparency.gloss_factor) + '\n',
                              '\tmat.raytrace_transparency.gloss_threshold = ' + str(obj.active_material.raytrace_transparency.gloss_threshold) + '\n',
                              '\tmat.raytrace_transparency.gloss_samples = ' + str(obj.active_material.raytrace_transparency.gloss_samples) + '\n',
                              '\tmat.raytrace_mirror.use = ' + str(obj.active_material.raytrace_mirror.use) + '\n',
                              '\tmat.raytrace_mirror.reflect_factor = ' + str(obj.active_material.raytrace_mirror.reflect_factor) + '\n',
                              '\tmat.raytrace_mirror.fresnel = ' + str(obj.active_material.raytrace_mirror.fresnel) + '\n',
                              '\tmat.mirror_color[0] = ' + str(obj.active_material.mirror_color[0]) + '\n',
                              '\tmat.mirror_color[1] = ' + str(obj.active_material.mirror_color[1]) + '\n',
                              '\tmat.mirror_color[2] = ' + str(obj.active_material.mirror_color[2]) + '\n',
                              '\tmat.raytrace_mirror.fresnel_factor = ' + str(obj.active_material.raytrace_mirror.fresnel_factor) + '\n',
                              '\tmat.raytrace_mirror.depth = ' + str(obj.active_material.raytrace_mirror.depth) + '\n',
                              '\tmat.raytrace_mirror.distance = ' + str(obj.active_material.raytrace_mirror.distance) + '\n',
                              '\tmat.raytrace_mirror.fade_to = "' + str(obj.active_material.raytrace_mirror.fade_to) + '"\n',
                              '\tmat.raytrace_mirror.gloss_factor = ' + str(obj.active_material.raytrace_mirror.gloss_factor) + '\n',
                              '\tmat.raytrace_mirror.gloss_threshold = ' + str(obj.active_material.raytrace_mirror.gloss_threshold) + '\n',
                              '\tmat.raytrace_mirror.gloss_samples = ' + str(obj.active_material.raytrace_mirror.gloss_samples) + '\n',
                              '\tmat.raytrace_mirror.gloss_anisotropic = ' + str(obj.active_material.raytrace_mirror.gloss_anisotropic) + '\n',
                              '\tmat.subsurface_scattering.use  = ' + str(obj.active_material.subsurface_scattering.use ) + '\n',
                              '\tmat.subsurface_scattering.ior = ' + str(obj.active_material.subsurface_scattering.ior) + '\n',
                              '\tmat.subsurface_scattering.scale = ' + str(obj.active_material.subsurface_scattering.scale) + '\n',
                              '\tmat.subsurface_scattering.color[0] = ' + str(obj.active_material.subsurface_scattering.color[0]) + '\n',
                              '\tmat.subsurface_scattering.color[1] = ' + str(obj.active_material.subsurface_scattering.color[1]) + '\n',
                              '\tmat.subsurface_scattering.color[2] = ' + str(obj.active_material.subsurface_scattering.color[2]) + '\n',
                              '\tmat.subsurface_scattering.color_factor = ' + str(obj.active_material.subsurface_scattering.color_factor) + '\n',
                              '\tmat.subsurface_scattering.texture_factor = ' + str(obj.active_material.subsurface_scattering.texture_factor) + '\n',
                              '\tmat.subsurface_scattering.radius[0] = ' + str(obj.active_material.subsurface_scattering.radius[0]) + '\n',
                              '\tmat.subsurface_scattering.radius[1] = ' + str(obj.active_material.subsurface_scattering.radius[1]) + '\n',
                              '\tmat.subsurface_scattering.radius[2] = ' + str(obj.active_material.subsurface_scattering.radius[2]) + '\n',
                              '\tmat.subsurface_scattering.front = ' + str(obj.active_material.subsurface_scattering.front) + '\n',
                              '\tmat.subsurface_scattering.back = ' + str(obj.active_material.subsurface_scattering.back) + '\n',
                              '\tmat.subsurface_scattering.error_threshold = ' + str(obj.active_material.subsurface_scattering.error_threshold) + '\n',
                              '\tmat.strand.root_size = ' + str(obj.active_material.strand.root_size) + '\n',
                              '\tmat.strand.tip_size = ' + str(obj.active_material.strand.tip_size) + '\n',
                              '\tmat.strand.size_min = ' + str(obj.active_material.strand.size_min) + '\n',
                              '\tmat.strand.use_blender_units = ' + str(obj.active_material.strand.use_blender_units) + '\n',
                              '\tmat.strand.use_tangent_shading = ' + str(obj.active_material.strand.use_tangent_shading) + '\n',
                              '\tmat.strand.shape = ' + str(obj.active_material.strand.shape) + '\n',
                              '\tmat.strand.width_fade = ' + str(obj.active_material.strand.width_fade) + '\n',
                              '\tmat.strand.blend_distance = ' + str(obj.active_material.strand.blend_distance) + '\n',
                              '\tmat.use_raytrace = ' + str(obj.active_material.use_raytrace) + '\n',
                              '\tmat.use_full_oversampling = ' + str(obj.active_material.use_full_oversampling) + '\n',
                              '\tmat.use_sky = ' + str(obj.active_material.use_sky) + '\n',
                              '\tmat.use_mist = ' + str(obj.active_material.use_mist) + '\n',
                              '\tmat.invert_z = ' + str(obj.active_material.invert_z) + '\n',
                              '\tmat.offset_z = ' + str(obj.active_material.offset_z) + '\n',
                              '\tmat.use_face_texture = ' + str(obj.active_material.use_face_texture) + '\n',
                              '\tmat.use_face_texture_alpha = ' + str(obj.active_material.use_face_texture_alpha) + '\n',
                              '\tmat.use_vertex_color_paint = ' + str(obj.active_material.use_vertex_color_paint) + '\n',
                              '\tmat.use_vertex_color_light = ' + str(obj.active_material.use_vertex_color_light) + '\n',
                              '\tmat.use_object_color = ' + str(obj.active_material.use_object_color) + '\n',
                              '\tmat.pass_index = ' + str(obj.active_material.pass_index) + '\n',
                              '\tmat.use_shadows = ' + str(obj.active_material.use_shadows) + '\n',
                              '\tmat.use_transparent_shadows = ' + str(obj.active_material.use_transparent_shadows) + '\n',
                              '\tmat.use_cast_shadows_only = ' + str(obj.active_material.use_cast_shadows_only) + '\n',
                              '\tmat.shadow_cast_alpha = ' + str(obj.active_material.shadow_cast_alpha) + '\n',
                              '\tmat.use_only_shadow = ' + str(obj.active_material.use_only_shadow) + '\n',
                              '\tmat.shadow_only_type = "' + str(obj.active_material.shadow_only_type) + '"\n',
                              '\tmat.use_cast_buffer_shadows = ' + str(obj.active_material.use_cast_buffer_shadows) + '\n',
                              '\tmat.shadow_buffer_bias = ' + str(obj.active_material.shadow_buffer_bias) + '\n',
                              '\tmat.use_ray_shadow_bias = ' + str(obj.active_material.use_ray_shadow_bias) + '\n',
                              '\tmat.shadow_ray_bias = ' + str(obj.active_material.shadow_ray_bias) + '\n',
                              '\tmat.use_cast_approximate = ' + str(obj.active_material.use_cast_approximate) + '\n',
                              '\treturn mat\n',
                              '\n',
                              'bpy.ops.object.material_slot_add()\n',
                              'obj.material_slots[-1].material = CreateMaterial("MAT_EXP_' +  Mat_Name + '")\n\n\n']

    #I treat textures :
    textureName = False
    textureNumbers = -1
    TEX_VALUES_FOR_RAMPS = [] #This list it's values necessary for the ramps section

    for textureName in tex.texture_slots.values():
        textureNumbers = textureNumbers + 1

        if textureName == None or obj.active_material.texture_slots[textureNumbers].name == "":
            texureName = False

        else:
            textureName = True
            TEX_VALUES_FOR_RAMPS.append(textureNumbers)

        if textureName :
            mytex = ""
            MY_EXPORT_INFORMATIONS.append('\n')
            MY_EXPORT_INFORMATIONS.append('#Create texture : ' + obj.active_material.texture_slots[textureNumbers].name + '.\n')
            MY_EXPORT_INFORMATIONS.append('mytex = bpy.data.textures.new(name="' + obj.active_material.texture_slots[textureNumbers].name + '", type="' + obj.active_material.texture_slots[textureNumbers].texture.type + '")\n')
            MY_EXPORT_INFORMATIONS.append('slot =  obj.active_material.texture_slots.add()\n')
            MY_EXPORT_INFORMATIONS.append('slot.texture = mytex\n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.use_preview_alpha  = ' + str(tex.texture_slots[textureNumbers].texture.use_preview_alpha) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'CLOUDS':
                MY_EXPORT_INFORMATIONS.append('slot.texture.cloud_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.cloud_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_depth  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_depth) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'POINT_DENSITY':
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.point_source  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.point_source) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.radius  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.radius) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.particle_cache_space  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.particle_cache_space) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.falloff  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.falloff) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.use_falloff_curve  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.use_falloff_curve) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.falloff_soft  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.falloff_soft) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.falloff_speed_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.falloff_speed_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.speed_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.speed_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.point_density.color_source  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.point_density.color_source) +  '"\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'ENVIRONMENT_MAP':
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.source  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.source) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.mapping  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.mapping) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.clip_start  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.clip_start) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.clip_end  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.clip_end) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.resolution  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.resolution) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.depth  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.depth) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.environment_map.zoom  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.environment_map.zoom) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'IMAGE':
                print(LanguageValuesDict['ErrorsMenuError001'])
                print(LanguageValuesDict['ErrorsMenuError002'])
                print(LanguageValuesDict['ErrorsMenuError003'])

                if tex.texture_slots[textureNumbers].texture.image.source == 'FILE':
                    #Here create save path and  save source:
                    Tex_ima_filepath = obj.active_material.texture_slots[textureNumbers].texture.image.filepath

                    #I must found Image File Name
                    IMAGE_FILEPATH = Raw_Image_Path(Tex_ima_filepath)
                    IMAGE_FILENAME = Raw_Image_Name(IMAGE_FILEPATH)

                    if '*Error*' in IMAGE_FILEPATH:
                        ErrorsPathJpg = os.path.join(ErrorsPath, 'error_save.jpg')
                        shutil.copy2(ErrorsPathJpg, os.path.join(AppPath, 'error_save.jpg'))
                        IMAGE_FILEPATH = os.path.join(AppPath, 'error_save.jpg')
                        IMAGE_FILENAME = 'error_save.jpg'
                        print(LanguageValuesDict['ErrorsMenuError013'])

                    #I treat informations:
                    MY_EXPORT_INFORMATIONS.append('imagePath = os.path.join(scriptPath, Mat_Name + "_" + "' + IMAGE_FILENAME +  '")\n')
                    MY_EXPORT_INFORMATIONS.append('img=bpy.data.images.load(filepath=imagePath)\n')

                    save_path = stripext(os.path.join(ZipPath, Mat_Name), '.py')

                    #Now I create file:
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image  = img\n')
                    MY_EXPORT_INFORMATIONS.append('#slot.texture.image.name  = "' + IMAGE_FILENAME +  '"\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_fields  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_fields) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_premultiply  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_premultiply) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.field_order  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.image.field_order) +  '"\n')

                    #I copy images :
                    shutil.copy2(IMAGE_FILEPATH, save_path + "_" + IMAGE_FILENAME)
                    print(LanguageValuesDict['ErrorsMenuError005'])

                    print("*******************************************************************************")

                if tex.texture_slots[textureNumbers].texture.image.source == 'GENERATED':
                    myImg = str(obj.active_material.texture_slots[textureNumbers].texture.image.name)
                    myImg = '"' + myImg
                    MY_EXPORT_INFORMATIONS.append('imagePath = os.path.join(scriptPath, Mat_Name + "_" + ' + myImg +  '.png")\n')
                    MY_EXPORT_INFORMATIONS.append('img=bpy.data.images.load(filepath=imagePath)\n')

                    save_path = os.path.join(ZipPath, Mat_Name)

                    save_path = stripext(save_path, '.py')

                    #Now I create file:
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image  = img\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_fields  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_fields) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.generated_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.image.generated_type) +  '"\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.generated_width  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.generated_width) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.generated_height  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.generated_height) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_generated_float  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_generated_float) +  '\n')

                    #I copy images :
                    save_path = save_path + "_" + str(obj.active_material.texture_slots[textureNumbers].texture.image.name) + ".png"

                    if os.path.exists(save_path) :
                        os.remove(save_path)

                    bpy.data.images[obj.active_material.texture_slots[textureNumbers].texture.image.name].save_render(filepath=save_path)
                    Tex_ima_filepath = save_path

                    print(LanguageValuesDict['ErrorsMenuError005'])
                    print("*******************************************************************************")

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'MAGIC':
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_depth  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_depth) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.turbulence  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.turbulence) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'MARBLE':
                MY_EXPORT_INFORMATIONS.append('slot.texture.marble_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.marble_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis_2  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis_2) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.turbulence  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.turbulence) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_depth  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_depth) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.turbulence  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.turbulence) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'MUSGRAVE':
                MY_EXPORT_INFORMATIONS.append('slot.texture.musgrave_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.musgrave_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.dimension_max  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.dimension_max) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.lacunarity  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.lacunarity) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.octaves  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.octaves) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_intensity  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_intensity) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.offset  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.offset) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.gain  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.gain) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'DISTORTED_NOISE':
                MY_EXPORT_INFORMATIONS.append('slot.texture.distortion  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.distortion) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_distortion  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_distortion) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'STUCCI':
                MY_EXPORT_INFORMATIONS.append('slot.texture.stucci_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.stucci_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.turbulence  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.turbulence) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'VORONOI':
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_intensity  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_intensity) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.distance_metric  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.distance_metric) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.minkovsky_exponent  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.minkovsky_exponent) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.color_mode  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.color_mode) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.weight_1  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.weight_1) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.weight_2  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.weight_2) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.weight_3  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.weight_3) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.weight_4  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.weight_4) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'VOXEL_DATA':
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.file_format  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.file_format) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.filepath  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.filepath) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.use_still_frame  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.use_still_frame) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.still_frame  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.still_frame) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.interpolation  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.interpolation) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.extension  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.extension) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.intensity  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.intensity) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.resolution[0]  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.resolution[0]) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.resolution[1]  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.resolution[1]) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.resolution[2]  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.resolution[2]) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.voxel_data.smoke_data_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.voxel_data.smoke_data_type) +  '"\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'WOOD':
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis_2  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis_2) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.wood_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.wood_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_type  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_type) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_basis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_basis) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.noise_scale  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.noise_scale) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.nabla  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.nabla) +  '\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.turbulence  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.turbulence) +  '\n')

            if bpy.context.object.active_material.texture_slots[textureNumbers].texture.type == 'BLEND':
                MY_EXPORT_INFORMATIONS.append('slot.texture.progression  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.progression) +  '"\n')
                MY_EXPORT_INFORMATIONS.append('slot.texture.use_flip_axis  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.use_flip_axis) +  '"\n')

            MY_EXPORT_INFORMATIONS.append('slot.texture.factor_red  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.factor_red) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.factor_green  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.factor_green) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.factor_blue  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.factor_blue) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.intensity  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.intensity) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.contrast  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.contrast) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture.saturation  =  ' + str(obj.active_material.texture_slots[textureNumbers].texture.saturation) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.texture_coords  =  "' + str(obj.active_material.texture_slots[textureNumbers].texture_coords) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.mapping  =  "' + str(obj.active_material.texture_slots[textureNumbers].mapping) +  '" \n')

            if obj.active_material.texture_slots[textureNumbers].texture_coords == 'UV' or obj.active_material.texture_slots[textureNumbers].texture_coords == 'ORCO':
                MY_EXPORT_INFORMATIONS.append('slot.use_from_dupli  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_from_dupli) +  ' \n')

            if obj.active_material.texture_slots[textureNumbers].texture_coords == 'OBJECT':
                MY_EXPORT_INFORMATIONS.append('slot.use_from_original  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_from_original) +  ' \n')

            MY_EXPORT_INFORMATIONS.append('slot.mapping_x  =  "' + str(obj.active_material.texture_slots[textureNumbers].mapping_x) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.mapping_y  =  "' + str(obj.active_material.texture_slots[textureNumbers].mapping_y) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.mapping_z  =  "' + str(obj.active_material.texture_slots[textureNumbers].mapping_z) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.offset[0]  =  ' + str(obj.active_material.texture_slots[textureNumbers].offset[0]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.offset[1]  =  ' + str(obj.active_material.texture_slots[textureNumbers].offset[1]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.offset[2]  =  ' + str(obj.active_material.texture_slots[textureNumbers].offset[2]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.scale[0]  =  ' + str(obj.active_material.texture_slots[textureNumbers].scale[0]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.scale[1]  =  ' + str(obj.active_material.texture_slots[textureNumbers].scale[1]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.scale[2]  =  ' + str(obj.active_material.texture_slots[textureNumbers].scale[2]) +  ' \n')

            MY_EXPORT_INFORMATIONS.append('slot.use_map_diffuse  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_diffuse) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_color_diffuse  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_color_diffuse) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_alpha  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_alpha) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_translucency  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_translucency) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_specular  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_specular) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_color_spec  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_color_spec) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_hardness  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_hardness) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_ambient  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_ambient) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_emit  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_emit) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_mirror  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_mirror) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_raymir  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_raymir) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_normal  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_normal) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_warp  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_warp) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_map_displacement  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_map_displacement) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_rgb_to_intensity  =  ' + str(obj.active_material.texture_slots[textureNumbers].use_rgb_to_intensity) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.invert =  ' + str(obj.active_material.texture_slots[textureNumbers].invert) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.diffuse_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].diffuse_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.diffuse_color_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].diffuse_color_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.alpha_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].alpha_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.translucency_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].translucency_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.specular_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].specular_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.specular_color_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].specular_color_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.hardness_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].hardness_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.ambient_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].ambient_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.emit_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].emit_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.mirror_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].mirror_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.raymir_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].raymir_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.normal_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].normal_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.warp_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].warp_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.displacement_factor  =  ' + str(obj.active_material.texture_slots[textureNumbers].displacement_factor) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.default_value  =  ' + str(obj.active_material.texture_slots[textureNumbers].default_value) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.color[0]  =  ' + str(obj.active_material.texture_slots[textureNumbers].color[0]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.color[1]  =  ' + str(obj.active_material.texture_slots[textureNumbers].color[1]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.color[2]  =  ' + str(obj.active_material.texture_slots[textureNumbers].color[2]) +  ' \n')
            MY_EXPORT_INFORMATIONS.append('slot.bump_method  =  "' + str(obj.active_material.texture_slots[textureNumbers].bump_method) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.bump_objectspace  =  "' + str(obj.active_material.texture_slots[textureNumbers].bump_objectspace) +  '" \n')
            MY_EXPORT_INFORMATIONS.append('slot.use_stencil  = ' + str(obj.active_material.texture_slots[textureNumbers].use_stencil) + '\n')
            MY_EXPORT_INFORMATIONS.append('slot.blend_type  =  "' + str(obj.active_material.texture_slots[textureNumbers].blend_type) +  '" \n')

    #Here my diffuse ramp :
    ramp = bpy.context.object.active_material
    MY_EXPORT_INFORMATIONS.append('\n\n')
    MY_EXPORT_INFORMATIONS.append('# Create new context :\n')
    MY_EXPORT_INFORMATIONS.append('ramp = bpy.context.object.active_material\n')
    MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION = 0.0\n')
    MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION = 1.0\n\n')

    #Here my diffuse ramp :
    if ramp.use_diffuse_ramp :
        counter = 0
        loop = 0
        values = ""
        MY_EXPORT_INFORMATIONS.append('ramp.use_diffuse_ramp = True\n')

        for values in ramp.diffuse_ramp.elements.items():
            loop = loop + 1

        while counter <= loop:
            if counter == 0:
                #Here i get differentes color bands:
                MY_EXPORT_INFORMATIONS.append('\n# diffuse ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION =' +str(ramp.diffuse_ramp.elements[0].position) + '\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[0].position='+ str(ramp.diffuse_ramp.elements[counter].position) +'\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_blend  =  "' + str(ramp.diffuse_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_input  =  "' + str(ramp.diffuse_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_factor  =  ' + str(ramp.diffuse_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.interpolation  =  "' + str(ramp.diffuse_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[3]) +  ' \n')

            if counter > 0 and counter < loop - 1 :
                #Here i get differentes color bands:
                MY_EXPORT_INFORMATIONS.append('\n# diffuse ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements.new(position=' + str(ramp.diffuse_ramp.elements[counter].position) + ')\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_blend  =  "' + str(ramp.diffuse_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_input  =  "' + str(ramp.diffuse_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_factor  =  ' + str(ramp.diffuse_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.interpolation  =  "' + str(ramp.diffuse_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[3]) +  ' \n')

            if counter == loop - 1:
                MY_EXPORT_INFORMATIONS.append('\n# diffuse ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION =' +str(ramp.diffuse_ramp.elements[counter].position) + '\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) +'].position=1.0\n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_blend  =  "' + str(ramp.diffuse_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_input  =  "' + str(ramp.diffuse_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp_factor  =  ' + str(ramp.diffuse_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.interpolation  =  "' + str(ramp.diffuse_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.diffuse_ramp.elements[counter].color[3]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[0].position = RAMP_MIN_POSITION \n')
                MY_EXPORT_INFORMATIONS.append('ramp.diffuse_ramp.elements[' +  str(counter) + '].position = RAMP_MAX_POSITION \n')

            counter = counter + 1

    #Here my specular ramp :
    if ramp.use_specular_ramp :
        counter = 0
        loop = 0
        values = ""
        MY_EXPORT_INFORMATIONS.append('ramp.use_specular_ramp = True\n')
        MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION = 0.0\n')
        MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION = 1.0\n\n')

        for values in ramp.specular_ramp.elements.items():
            loop = loop + 1

        while counter <= loop:
            if counter == 0:
                #Here i get differentes color bands:
                MY_EXPORT_INFORMATIONS.append('\n# Specular ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION =' +str(ramp.specular_ramp.elements[0].position) + '\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[0].position='+ str(ramp.specular_ramp.elements[counter].position) +'\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_blend  =  "' + str(ramp.specular_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_input  =  "' + str(ramp.specular_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_factor  =  ' + str(ramp.specular_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.interpolation  =  "' + str(ramp.specular_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.specular_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.specular_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.specular_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.specular_ramp.elements[counter].color[3]) +  ' \n')

            if counter > 0 and counter < loop - 1 :
                #Here i get differentes color bands:
                MY_EXPORT_INFORMATIONS.append('\n# Specular ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements.new(position=' + str(ramp.specular_ramp.elements[counter].position) + ')\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_blend  =  "' + str(ramp.specular_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_input  =  "' + str(ramp.specular_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_factor  =  ' + str(ramp.specular_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.interpolation  =  "' + str(ramp.specular_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.specular_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.specular_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.specular_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.specular_ramp.elements[counter].color[3]) +  ' \n')

            if counter == loop - 1:
                MY_EXPORT_INFORMATIONS.append('\n# Specular ramps datas ' + str(counter) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION =' +str(ramp.specular_ramp.elements[counter].position) + '\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) +'].position=1.0\n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_blend  =  "' + str(ramp.specular_ramp_blend) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_input  =  "' + str(ramp.specular_ramp_input) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp_factor  =  ' + str(ramp.specular_ramp_factor) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.interpolation  =  "' + str(ramp.specular_ramp.interpolation) +  '" \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.specular_ramp.elements[counter].color[0]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.specular_ramp.elements[counter].color[1]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.specular_ramp.elements[counter].color[2]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.specular_ramp.elements[counter].color[3]) +  ' \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[0].position = RAMP_MIN_POSITION \n')
                MY_EXPORT_INFORMATIONS.append('ramp.specular_ramp.elements[' +  str(counter) + '].position = RAMP_MAX_POSITION \n')

            counter = counter + 1

    #Here I create my textures conditions :
    textureName = False
    textureNumbers = -1
    textureNumberSlot = -1

    for textureName in ramp.texture_slots.values():
        textureNumbers = textureNumbers + 1
        textureNumberSlot = textureNumberSlot + 1

        if textureName != None :
            #If my texture slot it's created and ramp color it's used do :
            if ramp.texture_slots[textureNumbers].texture.use_color_ramp :
                counter = 0
                loop = 0
                values = ""

                val = 0
                cou = 0

                for val in TEX_VALUES_FOR_RAMPS:
                    if val == textureNumberSlot:
                        textureNumberSlot = cou
                    else:
                        cou = cou + 1

                MY_EXPORT_INFORMATIONS.append('\n# Texture color ramps datas ' + str(textureNumberSlot) + ' :\n')
                MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.use_color_ramp = True\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION = 0.0\n')
                MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION = 1.0\n\n')

                for values in ramp.texture_slots[textureNumbers].texture.color_ramp.elements.items():
                    loop = loop + 1

                while counter <= loop:
                    if counter == 0:
                        #Here i get differentes color bands:
                        MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION =' +str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[0].position) + '\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[0].position='+ str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].position) +'\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.interpolation) +  '" \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[0]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[1]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[2]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[3]) +  ' \n')

                    if counter > 0 and counter < loop - 1 :
                        #Here i get differentes color bands:
                        MY_EXPORT_INFORMATIONS.append('\n# Texture color ramps datas ' + str(textureNumberSlot) + ' :\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements.new(position=' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].position) + ')\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.interpolation) +  '" \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[0]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[1]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[2]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[3]) +  ' \n')

                    if counter == loop - 1:
                        MY_EXPORT_INFORMATIONS.append('\n# Texture color ramps datas ' + str(textureNumberSlot) + ' :\n')
                        MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION =' +str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].position) + '\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) +'].position=1.0\n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.interpolation) +  '" \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[0]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[1]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[2]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.color_ramp.elements[counter].color[3]) +  ' \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[0].position = RAMP_MIN_POSITION \n')
                        MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.color_ramp.elements[' +  str(counter) + '].position = RAMP_MAX_POSITION \n')

                    counter = counter + 1

    #Here I create my Point Density conditions :
    textureName = False
    textureNumbers = -1
    textureNumberSlot = -1

    for textureName in ramp.texture_slots.values():
        textureNumbers = textureNumbers + 1
        textureNumberSlot = textureNumberSlot + 1

        if textureName != None :
            #If my texture slot it's created and point density ramp it's used do :
            if ramp.texture_slots[textureNumbers].texture.type == 'POINT_DENSITY':
                if ramp.texture_slots[textureNumbers].texture.point_density.color_source == 'PARTICLE_AGE' or ramp.texture_slots[textureNumbers].texture.point_density.color_source == 'PARTICLE_SPEED':
                    counter = 0
                    loop = 0
                    values = ""
                    val = 0
                    cou = 0

                    for val in TEX_VALUES_FOR_RAMPS:
                        if val == textureNumberSlot:
                            textureNumberSlot = cou
                        else:
                            cou = cou + 1

                    MY_EXPORT_INFORMATIONS.append('\n# Texture point density ramps datas ' + str(textureNumberSlot) + ' :\n')
                    MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION = 0.0\n')
                    MY_EXPORT_INFORMATIONS.append('RAMP_MAX_POSITION = 1.0\n\n')

                    for values in ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements.items():
                        loop = loop + 1

                    while counter <= loop:
                        if counter == 0:
                            #Here i get differentes color bands:
                            MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION =' +str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[0].position) + '\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[0].position='+ str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].position) +'\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.interpolation) +  '" \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[0]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[1]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[2]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[3]) +  ' \n')

                        if counter > 0 and counter < loop - 1 :
                            #Here i get differentes color bands:
                            MY_EXPORT_INFORMATIONS.append('\n# Texture point density ramps datas ' + str(textureNumberSlot) + ' :\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements.new(position=' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].position) + ')\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.interpolation) +  '" \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[0]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[1]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[2]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[3]) +  ' \n')

                        if counter == loop - 1:
                            MY_EXPORT_INFORMATIONS.append('\n# Texture point density ramps datas ' + str(textureNumberSlot) + ' :\n')
                            MY_EXPORT_INFORMATIONS.append('RAMP_MIN_POSITION =' +str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].position) + '\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) +'].position=1.0\n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.interpolation  =  "' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.interpolation) +  '" \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[0]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[0]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[1]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[1]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[2]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[2]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' + str(counter) + '].color[3]  =  ' + str(ramp.texture_slots[textureNumbers].texture.point_density.color_ramp.elements[counter].color[3]) +  ' \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[0].position = RAMP_MIN_POSITION \n')
                            MY_EXPORT_INFORMATIONS.append('ramp.texture_slots[' + str(textureNumberSlot) + '].texture.point_density.color_ramp.elements[' +  str(counter) + '].position = RAMP_MAX_POSITION \n')

                        counter = counter + 1

    #I create a file on the Filepath :
    File_Path = stripext(File_Path, '.py')
    #File_Path = File_Path.replace('.', '')
    Mat_Name = stripext(Mat_Name, '.py')
    Mat_Name = Mat_Name.replace('.', '')

    #fileExport =  File_Path + "_" + Inf_Creator + ".py"
    fileExport =  os.path.join(ZipPath, Mat_Name + "_" + Inf_Creator + ".py")

    file = open(fileExport, "w")
    for line in MY_EXPORT_INFORMATIONS:
        file.write(line)
    file.close()

    #Now I zip files :
    ZipFile_path = File_Path + "_" + Inf_Creator + ".blex"
    z=zipfile.ZipFile(ZipFile_path,'w', zipfile.ZIP_DEFLATED)

    #I zip files in Zip Folder:
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f):
            ZipFile_Write = os.path.join(ZipPath, f)
            z.write(ZipFile_Write, os.path.basename(ZipFile_Write), zipfile.ZIP_DEFLATED)

    z.close()

    #I create or the preview file:
    if TakePreview :
        MyPreviewResult = TakePreviewRender(Inf_Creator, Mat_Name)
        PreviewFilePath = File_Path + "_" + Inf_Creator + ".jpg"
        imageFileJPG = open(PreviewFilePath,'wb')
        imageFileJPG.write(MyPreviewResult)
        imageFileJPG.close()

# ************************************************************************************
# *                                     RAW IMAGE PATH                               *
# ************************************************************************************
def Raw_Image_Path(Image_Path):
    Image_Path = Image_Path.replace("'", "") # only needed because caller might have quoted it
    SaveOriginalName = Image_Path

    #Relative/Absolute Paths:
    if '..' in Image_Path or './' in Image_Path:
        Image_Path = os.path.normpath(Image_Path)

    SaveOriginalPath = Image_Path

    if not os.path.exists(Image_Path) :
        Image_Path = os.path.join(BlendPath, Image_Path)

    if not os.path.exists(Image_Path) :
        Image_Path = '~' + SaveOriginalPath

    if not os.path.exists(Image_Path) :
        SaveOriginalName = SaveOriginalName.replace("'", "")
        print(LanguageValuesDict['ErrorsMenuError009'] + '"' + SaveOriginalName + '"')
        print(LanguageValuesDict['ErrorsMenuError010'])
        print(LanguageValuesDict['ErrorsMenuError011'])
        print(LanguageValuesDict['ErrorsMenuError012'])
        Image_Path = "*Error*"

    return Image_Path

# ************************************************************************************
# *                                     RAW IMAGE NAME                               *
# ************************************************************************************
def Raw_Image_Name(Image_Path):
    Image_Path = Image_Path.replace("'", '')
    return Image_Path.split(os.path.sep)[-1]

# ************************************************************************************
# *                                   PREPARE SQL REQUEST                            *
# ************************************************************************************
def PrepareSqlUpdateSaveRequest(ShaderToolsDatabase, Cursor, Mat_Name):
    print()
    print("                                        *****                         ")
    print()
    print("*******************************************************************************")
    print("*                                   SAVE MATERIAL                             *")
    print("*******************************************************************************")

    obj = bpy.context.object
    SSS_Mat_Name = Mat_Name

    def GetObjectFields(obj, fields, fielddefs, include = lambda field : True) :
        # common routine for converting object attribute values into database field values.
        for field in fielddefs :
            if include(field) :
                attr = fielddefs[field].get("attr")
                if attr != None :
                    idx = None
                    if len(attr) > 1 :
                        attr, idx = attr
                    else :
                        attr = attr[0]
                    #end if
                    val = obj
                    for name in attr.split(".") :
                        val = getattr(val, name)
                    #end for
                    if idx != None :
                        val = val[idx]
                    #end if
                    if "convert_out" in fielddefs[field] :
                        val = fielddefs[field]["convert_out"](val)
                    #end if
                    fields[field] = val
                #end if
            #end if
        #end for
    #end GetObjectFields

    Material = \
        {
            "Mat_Name" : "MAT_PRE_" + Mat_Name,
            "Mat_Type" : obj.active_material.type,
            "Mat_Preview_render_type" : obj.active_material.preview_render_type,
            "Mat_diffuse_color_a" : 0, # not used
            "Mat_specular_color_a" : 0, # not used
            "Mat_raytracemirror_color_a" : 0, # not used
            "Mat_subsurfacescattering_presets" : "SSS_PRE_" + SSS_Mat_Name, # not used
            "Mat_subsurfacescattering_color_a" : 0, # not used
          # Note I'm not bothering to define Idx_ramp_diffuse, Idx_ramp_specular or Idx_textures fields
        }
    GetObjectFields(obj.active_material, Material, material_fields)
    InsertRecord(Cursor, "MATERIALS", Material)
    Mat_Index = LastInsertID(ShaderToolsDatabase)

    #************************** MY TEXTURES *****************************
    #Textures values :
    tex = bpy.context.active_object.active_material
    for textureNumbers, textureName in enumerate(tex.texture_slots.values()) :
        if textureName != None :
            texslot = tex.texture_slots[textureNumbers]
            Tex_Type = texslot.texture.type
            Texture = \
                {
                    "Mat_Idx" : Mat_Index,
                    "Tex_Name" : texslot.name,
                    "Tex_Type" : Tex_Type,
                    "Tex_Preview_type" : tex.preview_render_type,
                  # Note I'm not bothering to define Col_Idx or Poi_Idx fields
                    "Tex_influence_color_a" : 0, # unused?
                }
            GetObjectFields \
              (
                texslot,
                Texture,
                texture_fields,
                include = lambda field : texture_fields[field].get("type") in (None, Tex_Type)
              )
            if texslot.texture_coords == 'ORCO' or texslot.texture_coords == 'UV' :
                Texture["Tex_mapping_use_from_dupli"] = texslot.use_from_dupli
            #end if
            if texslot.texture_coords == 'OBJECT':
                Texture["Tex_mapping_use_from_original"] = texslot.use_from_original
            #end if
            InsertRecord(Cursor, "TEXTURES", Texture)
            Tex_Index = LastInsertID(ShaderToolsDatabase)

            if texslot.texture.type == 'IMAGE':
                #CLASSIC IMAGE FILE :
                ThisImage = \
                    {
                        "Idx_Texture" : Tex_Index,
                        "Ima_Name" : "",
                        "Ima_Fileformat" : "",
                        "Ima_Fields" : int(False),
                        "Ima_Premultiply" : int(False),
                        "Ima_Fields_order" : "",
                        "Ima_Generated_width" : 0,
                        "Ima_Generated_height" : 0,
                        "Ima_Float_buffer" : int(False),
                        "Ima_Blob" : "",
                    }
                print(LanguageValuesDict['ErrorsMenuError001'])
                print(LanguageValuesDict['ErrorsMenuError002'])
                print(LanguageValuesDict['ErrorsMenuError003'])
                if texslot.texture.image.source == 'FILE':
                    #I must found Image File Name
                    ThisImage["Ima_Filepath"] = texslot.texture.image.filepath
                    IMAGE_FILEPATH = Raw_Image_Path(ThisImage["Ima_Filepath"])
                    IMAGE_FILENAME = Raw_Image_Name(IMAGE_FILEPATH)
                    if '*Error*' in IMAGE_FILEPATH:
                        ErrorsPathJpg = os.path.join(ErrorsPath, 'error_save.jpg')
                        shutil.copy2(ErrorsPathJpg, os.path.join(AppPath, 'error_save.jpg'))
                        IMAGE_FILEPATH = os.path.join(AppPath, 'error_save.jpg')
                        IMAGE_FILENAME = 'error_save.jpg'
                        print(LanguageValuesDict['ErrorsMenuError013'])
                    else:
                        ThisImage["Ima_Name"] = IMAGE_FILENAME
                        ThisImage["Ima_Source"] = texslot.texture.image.source
                        ThisImage["Ima_Fileformat"] = texslot.texture.image.file_format
                        ThisImage["Ima_Fields"] = texslot.texture.image.use_fields
                        ThisImage["Ima_Premultiply"] = texslot.texture.image.use_premultiply
                        ThisImage["Ima_Fields_order"] = texslot.texture.image.field_order
                    #end if
                #GENERATED IMAGE FILE (UV FILE) :
                if texslot.texture.image.source == 'GENERATED':
                    ThisImage["Ima_Filepath"] = texslot.texture.image.filepath
                    ThisImage["Ima_Name"] = texslot.texture.image.name
                    ThisImage["Ima_Source"] = texslot.texture.image.source
                    ThisImage["Ima_Fileformat"] = "PNG"
                    ThisImage["Ima_Generated_type"] = texslot.texture.image.generated_type
                    ThisImage["Ima_Generated_width"] = texslot.texture.image.generated_width
                    ThisImage["Ima_Generated_height"] = texslot.texture.image.generated_height
                    ThisImage["Ima_Float_buffer"] = texslot.texture.image.use_generated_float
                    save_name = ThisImage["Ima_Name"]
                    save_path = os.path.join(AppPath, save_name.replace('.', '') + ".png")
                    if os.path.exists(save_path) :
                        os.remove(save_path)
                    #end if
                    bpy.data.images[save_name].save_render(filepath=save_path)
                    IMAGE_FILEPATH = save_path
                #end if
                file = open(IMAGE_FILEPATH, "rb")
                ThisImage["Ima_Blob"] = file.read()
                file.close()
                ThisImage["Ima_Filepath"] = IMAGE_FILEPATH
                InsertRecord(Cursor, "IMAGE_UV", ThisImage)
                if os.path.exists(ThisImage["Ima_Filepath"]) :
                   os.remove(ThisImage["Ima_Filepath"])
                #end if
                print(LanguageValuesDict['ErrorsMenuError004'])
                print("*******************************************************************************")
            #end if

            ramp = texslot.texture

            #Here my color ramp :
            if ramp.use_color_ramp :
                for counter in range(0, len(ramp.color_ramp.elements.items())) :
                    ramp_elt = ramp.color_ramp.elements[counter]
                    InsertRecord \
                      (
                        Cursor = Cursor,
                        TableName = "COLORS_RAMP",
                        Fields =
                            {
                                "Col_Num_Material" : Mat_Index,
                                "Col_Num_Texture" : Tex_Index,
                                "Col_Flip" : int(False),
                                "Col_Active_color_stop" : 0,
                                "Col_Between_color_stop" : ramp.color_ramp.interpolation,
                                "Col_Interpolation" : ramp.color_ramp.interpolation,
                                "Col_Position" : ramp_elt.position,
                                "Col_Color_stop_one_r" : ramp_elt.color[0],
                                "Col_Color_stop_one_g" : ramp_elt.color[1],
                                "Col_Color_stop_one_b" : ramp_elt.color[2],
                                "Col_Color_stop_one_a" : ramp_elt.color[3],
                                "Col_Color_stop_two_r" : 0,
                                "Col_Color_stop_two_g" : 0,
                                "Col_Color_stop_two_b" : 0,
                                "Col_Color_stop_two_a" : 0,
                            }
                      )
                #end for
            #end if

            #Here my point density ramp :
            if (
                    ramp.type == 'POINT_DENSITY'
                and
                    (
                        ramp.point_density.color_source == 'PARTICLE_SPEED'
                    or
                        ramp.point_density.color_source == 'PARTICLE_AGE'
                    )
            ) :
                for counter in range(0, len(ramp.point_density.color_ramp.elements.items())) :
                    ramp_elt = ramp.point_density.color_ramp.elements[counter]
                    InsertRecord \
                      (
                        Cursor = Cursor,
                        TableName = "POINTDENSITY_RAMP",
                        Fields =
                            {
                                "Poi_Num_Material" : Mat_Index,
                                "Poi_Num_Texture" : Tex_Index,
                                "Poi_Flip" : int(False),
                                "Poi_Active_color_stop" : 0,
                                "Poi_Between_color_stop" : ramp.point_density.color_ramp.interpolation,
                                "Poi_Interpolation" : ramp.point_density.color_ramp.interpolation,
                                "Poi_Position" : ramp_elt.position,
                                "Poi_Color_stop_one_r" : ramp_elt.color[0],
                                "Poi_Color_stop_one_g" : ramp_elt.color[1],
                                "Poi_Color_stop_one_b" : ramp_elt.color[2],
                                "Poi_Color_stop_one_a" : ramp_elt.color[3],
                                "Poi_Color_stop_two_r" : 0,
                                "Poi_Color_stop_two_g" : 0,
                                "Poi_Color_stop_two_b" : 0,
                                "Poi_Color_stop_two_a" : 0,
                            }
                      )
                #end for
            #end if

        #end if textureName != None
    #end for textures

    #************************** MY RAMPS *****************************
    ramp = bpy.context.object.active_material

    if ramp.use_diffuse_ramp :
        for counter in range(0, len(ramp.diffuse_ramp.elements.items())) :
            ramp_elt = ramp.diffuse_ramp.elements[counter]
            InsertRecord \
              (
                Cursor = Cursor,
                TableName = "DIFFUSE_RAMP",
                Fields =
                    {
                        "Dif_Num_Material" : Mat_Index,
                        "Dif_Flip" : int(False),
                        "Dif_Active_color_stop" : 0,
                        "Dif_Between_color_stop" : ramp.diffuse_ramp.interpolation,
                        "Dif_Interpolation" : ramp.diffuse_ramp.interpolation,
                        "Dif_Position" : ramp_elt.position,
                        "Dif_Color_stop_one_r" : ramp_elt.color[0],
                        "Dif_Color_stop_one_g" : ramp_elt.color[1],
                        "Dif_Color_stop_one_b" : ramp_elt.color[2],
                        "Dif_Color_stop_one_a" : ramp_elt.color[3],
                        "Dif_Color_stop_two_r" : 0.0,
                        "Dif_Color_stop_two_g" : 0.0,
                        "Dif_Color_stop_two_b" : 0.0,
                        "Dif_Color_stop_two_a" : 0.0,
                        "Dif_Ramp_input" : ramp.diffuse_ramp_input,
                        "Dif_Ramp_blend" : ramp.diffuse_ramp_blend,
                        "Dif_Ramp_factor" : ramp.diffuse_ramp_factor,
                    }
              )
        #end for
    #end if

    #Here my specular ramp :
    if ramp.use_specular_ramp :
        for counter in range(0, len(ramp.specular_ramp.elements.items())) :
            ramp_elt = ramp.specular_ramp.elements[counter]
            InsertRecord \
              (
                Cursor = Cursor,
                TableName = "SPECULAR_RAMP",
                Fields =
                    {
                        "Spe_Num_Material" : Mat_Index,
                        "Spe_Flip" : int(False),
                        "Spe_Active_color_stop" : 0,
                        "Spe_Between_color_stop" : ramp.specular_ramp.interpolation,
                        "Spe_Interpolation" : ramp.specular_ramp.interpolation,
                        "Spe_Position" : ramp_elt.position,
                        "Spe_Color_stop_one_r" : ramp_elt.color[0],
                        "Spe_Color_stop_one_g" : ramp_elt.color[1],
                        "Spe_Color_stop_one_b" : ramp_elt.color[2],
                        "Spe_Color_stop_one_a" : ramp_elt.color[3],
                        "Spe_Color_stop_two_r" : 0,
                        "Spe_Color_stop_two_g" : 0,
                        "Spe_Color_stop_two_b" : 0,
                        "Spe_Color_stop_two_a" : 0,
                        "Spe_Ramp_input" : ramp.specular_ramp_input,
                        "Spe_Ramp_blend" : ramp.specular_ramp_blend,
                        "Spe_Ramp_factor" : ramp.specular_ramp_factor,
                    }
              )
        #end for
    #end if

    # ShaderToolsDatabase.commit() # leave to caller to do
    return Mat_Index
#end PrepareSqlUpdateSaveRequest

# ************************************************************************************
# *                                TAKE OBJECT PREVIEW RENDER                        *
# ************************************************************************************
def TakePreviewRender(Inf_Creator, Mat_Name):
    #Here the Preview Render
    #I must save render configuration before save preview image of object :
    ren = bpy.context.scene.render
    resX = ren.resolution_x
    resY = ren.resolution_y
    ratio = ren.resolution_percentage
    pixX = ren.pixel_aspect_x
    pixY = ren.pixel_aspect_y
    antialiasing = ren.antialiasing_samples
    filepath = ren.filepath
    format = ren.image_settings.file_format
    mode = ren.image_settings.color_mode

    #I save preview image of object :
    ren.resolution_x = int(Resolution_X)
    ren.resolution_y = int(Resolution_Y)
    ren.resolution_percentage = 100
    ren.pixel_aspect_x = 1.0
    ren.pixel_aspect_y = 1.0
    ren.antialiasing_samples = '16'
    ren.filepath = os.path.join(AppPath, Mat_Name + "_" + Inf_Creator + "_preview.jpg")
    ren.image_settings.file_format = 'JPEG'
    ren.image_settings.color_mode = 'RGB'

    bpy.ops.render.render()
    bpy.data.images['Render Result'].save_render(filepath=ren.filepath)

    #I must restore render values configuration :
    ren.resolution_x = resX
    ren.resolution_y = resY
    ren.resolution_percentage = ratio
    ren.pixel_aspect_x = pixX
    ren.pixel_aspect_y = pixY
    ren.antialiasing_samples = antialiasing
    ren.filepath = filepath
    ren.image_settings.file_format = format
    ren.image_settings.color_mode = mode

    #I do a preview of scene and i send render in memory:
    PreviewFileImage = open(os.path.join(AppPath, Mat_Name + "_" + Inf_Creator + "_preview.jpg"),'rb')
    PreviewFileImageInMemory = PreviewFileImage.read()
    PreviewFileImage.close()

    #Remove Preview File:
    os.remove(os.path.join(AppPath, Mat_Name + "_" + Inf_Creator + "_preview.jpg"))

    return PreviewFileImageInMemory

# ************************************************************************************
# *                                     UPDATE DATABASE                              *
# ************************************************************************************
def UpdateDatabase(Inf_Creator, Inf_Category, Inf_Description, Inf_Weblink, Inf_Email, Mat_Name):
    ShaderToolsDatabase = sqlite3.connect(DataBasePath)
    Cursor = ShaderToolsDatabase.cursor()
    Mat_Index = PrepareSqlUpdateSaveRequest(ShaderToolsDatabase, Cursor, Mat_Name)
    InsertRecord \
      (
        Cursor = Cursor,
        TableName = "INFORMATIONS",
        Fields =
            {
                "Inf_Creator" : Inf_Creator,
                "Inf_Category" : Inf_Category,
                "Inf_Description" : Inf_Description,
                "Inf_Weblink" : Inf_Weblink,
                "Inf_Email" : Inf_Email,
                "Mat_Index" : Mat_Index,
            }
      )
    InsertRecord \
      (
        Cursor = Cursor,
        TableName = "RENDER",
        Fields =
            {
                "Ren_Color_Management" : int(bpy.context.scene.render.use_color_management),
                "Ren_Preview_Object" : TakePreviewRender(Inf_Creator, Mat_Name),
                "Mat_Index" : Mat_Index,
            }
      )
    ShaderToolsDatabase.commit()
    ShaderToolsDatabase.close()
    return {'FINISHED'}
#end UpdateDatabase

# ************************************************************************************
# *                                     SEARCH SHADERS                               *
# ************************************************************************************
def SearchShaders(self, context):

    #I must verify if search file not exist :
    if not os.path.exists(os.path.join(TempPath, "searching")) :

        #I create file until user do not cancel or valid choice :
        searchFile = open(os.path.join(TempPath, "searching"), 'w')
        searchFile.close()

        #Here I remove all files in the Tempory Folder:
        if os.path.exists(TempPath) :
            files = os.listdir(TempPath)
            for f in files:
                if not os.path.isdir(f) and f.endswith(".jpg"):
                    os.remove(os.path.join(TempPath, f))

        else:
            os.makedirs(TempPath)

        #Here I copy all files in Base Preview Folder:
        files = os.listdir(shaderFolderPath)
        for f in files:
            if not os.path.isdir(f) and f.endswith(".jpg"):
                shutil.copy2(os.path.join(shaderFolderPath, f), os.path.join(TempPath, f))


    #Here I remove all files in Base Preview Folder:
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            os.remove(os.path.join(shaderFolderPath, f))

    #Now I must copy files corresponding search entry :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            if self.Search.upper() in f.upper():
                shutil.copy2(os.path.join(TempPath, f), os.path.join(shaderFolderPath, f))


    bpy.ops.file.refresh()




# ************************************************************************************
# *                                 SEARCH SHADERS HISTORY                           *
# ************************************************************************************
def SearchShadersEnum(self, context):

    #I must verify if search file not exist :
    if not os.path.exists(os.path.join(TempPath, "searching")) :

        #I create file until user do not cancel or valid choice :
        searchFile = open(os.path.join(TempPath, "searching"), 'w')
        searchFile.close()

        #Here I remove all files in the Tempory Folder:
        if os.path.exists(TempPath) :
            files = os.listdir(TempPath)
            for f in files:
                if not os.path.isdir(f) and f.endswith(".jpg"):
                    os.remove(os.path.join(TempPath, f))
        else:
            os.makedirs(TempPath)

        #Here I copy all files in Base Preview Folder:
        files = os.listdir(shaderFolderPath)
        for f in files:
            if not os.path.isdir(f) and f.endswith(".jpg"):
                shutil.copy2(os.path.join(shaderFolderPath, f), os.path.join(TempPath, f))

    #Here I remove all files in Base Preview Folder:
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            os.remove(os.path.join(shaderFolderPath, f))

    #Now I must copy files corresponding search entry :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            if True in map(lambda h : os.path.normcase(f) == os.path.normcase(h), HISTORY_FILE) :
                shutil.copy2(os.path.join(TempPath, f), os.path.join(shaderFolderPath, f))

    bpy.ops.file.refresh()


# ************************************************************************************
# *                                        OPEN SHADERS                              *
# ************************************************************************************
class OpenShaders(bpy.types.Operator):
    bl_idname = "object.shadertools_openshaders"
    bl_label = LanguageValuesDict['OpenMenuTitle']
    bl_options = {'REGISTER', 'UNDO'}

    filename = bpy.props.StringProperty(subtype="FILENAME")

    Search = bpy.props.StringProperty(name='', update=SearchShaders)
    History = bpy.props.EnumProperty \
      (
        name = '',
        update = SearchShadersEnum,
        items =
            lambda self, context :
                    (
                        ('', "---- " + LanguageValuesDict['OpenMenuLabel09'] + " ----", ""),
                    )
                +
                    tuple((h, h, "") for h in HISTORY_FILE)
      )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(icon ='NEWFOLDER' ,text=" " + LanguageValuesDict['OpenMenuLabel08'] + " : ")
        row = layout.row(align=True)
        row.prop(self, 'Search')
        row = layout.row(align=True)
        row.label(text = 500 * "-")
        row = layout.row(align=True)
        row.label(icon ='MATERIAL', text=LanguageValuesDict['OpenMenuLabel09'] + " :")
        row = layout.row(align=True)
        row.prop(self, 'History', text ='')
        row = layout.row(align=True)

    def execute(self, context):
        global HISTORY_FILE
        selectedFile = stripext(self.filename, '.jpg')
        if os.path.exists(os.path.join(TempPath, "searching")) :
            os.remove(os.path.join(TempPath, "searching"))
        #I update history file:
        if selectedFile != "" :
            HISTORY_FILE = [selectedFile] + HISTORY_FILE[:-1]
            SaveHistory(HISTORY_FILE)
        #end if
        ImporterSQL(self.filename)
        #bpy.ops.script.python_file_run(filepath=os.path.join(AppPath, "__init__.py"))
          # am I right this was only needed to update above EnumProperty before it was dynamic?
        return {'FINISHED'}

    def invoke(self, context, event):
        ShaderToolsDatabase = sqlite3.connect(DataBasePath)
        # NOW I MUST CREATE THUMBNAILS IN THE SHADERS TEMPORY FOLDER:
        for \
            Material \
        in \
            GetEachRecord \
              (
                Conn = ShaderToolsDatabase,
                TableName = "MATERIALS inner join RENDER on MATERIALS.Mat_Index = RENDER.Mat_Index",
                Fields = 
                    (
                        "MATERIALS.Mat_Index as Mat_Index",
                        "MATERIALS.Mat_Name as Mat_Name",
                        "RENDER.Ren_Preview_Object as Ren_Preview_Object",
                    ),
                Condition = "MATERIALS.Mat_Index > 1 and RENDER.Ren_Preview_Object is not null"
              ) \
        :
            NameFileJPG = Material["Mat_Name"] + "_Ind_%d.jpg" % Material["Mat_Index"]
            NameFileJPG = NameFileJPG.replace('MAT_PRE_', '')
            NameFileJPG = os.path.join(shaderFolderPath, NameFileJPG)
            imageFileJPG = open(NameFileJPG,'wb')
            imageFileJPG.write(Material["Ren_Preview_Object"])
            imageFileJPG.flush()
            imageFileJPG.close()
        #end for
        ShaderToolsDatabase.close()

        if os.path.exists(os.path.join(AppPath, "first")) :
            bpy.ops.object.shadertools_warning('INVOKE_DEFAULT')
            os.remove(os.path.join(AppPath, "first"))
            time.sleep(1)

        else:
            wm = context.window_manager
            wm.fileselect_add(self)

        return {'RUNNING_MODAL'}

# ************************************************************************************
# *                                          CREDITS                                 *
# ************************************************************************************
class Credits(bpy.types.Operator):
    bl_idname = "object.shadertools_credits"
    bl_label = "Credits"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label("Credits :", icon='QUESTION')
        row = layout.row(align=True)
        row.label("Author : ")
        row.label("GRETETE Karim alias Tinangel")
        row = layout.row(align=True)
        row.label("Community : ")
        row.label("Blender Clan")
        row = layout.row(align=True)
        row.label("Translate : ")
        row.label("French : Tinangel")
        row = layout.row(align=True)
        row.label(" ")
        row.label("Deutsch : Kgeogeo")
        row = layout.row(align=True)
        row.label(" ")
        row.label("English : Tinangel")
        row = layout.row(align=True)
        row.label("Developer : ")
        row.label("Tinangel")
        row = layout.row(align=True)
        row.label("")
        row.label("Lawrence D'Oliveiro (Clean up code)")
        row = layout.row(align=True)
        row.label("Testing & corrections : ")
        row.label("Ezee, LA-Crobate,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("blendman, LadeHeria,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("Fadge")
        row = layout.row(align=True)
        row.label("Comments & suggestions : ")
        row.label("_tibo_, Bjo, julsengt, zeauro, Ezee,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("Julkien, meltingman, eddy, lucky,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("LA-Crobate, Fadge, blendman, Adreze,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("LadeHeria, thomas56, kgeogeo,")
        row = layout.row(align=True)
        row.label(" ")
        row.label("killpatate")
        row = layout.row(align=True)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width = 400)

    def execute(self, context):
        return {'FINISHED'}

# ************************************************************************************
# *                                           HELP                                   *
# ************************************************************************************
class Help(bpy.types.Operator):
    bl_idname = "object.shadertools_help"
    bl_label = LanguageValuesDict['HelpMenuTitle']

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel01'], icon='HELP')
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel02'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel03'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel04'], icon='NEWFOLDER')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel05'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel06'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel07'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel08'])
        row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel09'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel10'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel11'], icon='MATERIAL')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel12'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel13'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel14'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel15'], icon='SCRIPTWIN')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel16'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel17'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel18'])
        row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel19'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel20'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel21'], icon='BLENDER')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel22'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel23'])
        row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel24'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel25'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel26'], icon='TEXT')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel27'])
        row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel28'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel29'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel30'], icon='QUESTION')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel31'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['HelpMenuLabel32'])
        row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel33'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel34'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel35'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel36'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel37'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel38'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel39'])
        #row = layout.row(align=True)
        #row.label(LanguageValuesDict['HelpMenuLabel40'])
        #row = layout.row(align=True)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=900, height=768)

    def execute(self, context):
        return {'FINISHED'}

# ************************************************************************************
# *                                       IMPORTER                                   *
# ************************************************************************************
def Importer(File_Path, Mat_Name):
    ImportPath = os.path.dirname(bpy.data.filepath)


    #Blend file must be saved before import a file :
    print("*******************************************************")
    print(LanguageValuesDict['ErrorsMenuError001'])
    print(LanguageValuesDict['ErrorsMenuError006'])

    #Here I verify if Zip Folder exists:
    if not os.path.exists(ZipPath) :
        os.makedirs(ZipPath)

    #Here I remove all files in Zip Folder:
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f):
            os.remove(os.path.join(ZipPath, f))

    def unzip(ZipFile_Name, BlendDestination = ''):
        if BlendDestination == '': BlendDestination = os.getcwd()
        zfile = zipfile.ZipFile(ZipFile_Name, 'r')
        for z in zfile.namelist():
            if os.path.isdir(z):
                try: os.makedirs(os.path.join(BlendDestination, z))
                except: pass
            else:
                try: os.makedirs(os.path.join(BlendDestination, + os.path.dirname(z)))
                except: pass
                data = zfile.read(z)
                fp = open(os.path.join(BlendDestination, z), "wb")
                fp.write(data)
                fp.close()
        zfile.close()

    unzip(File_Path, ZipPath)

    #I must create a Folder in .blend Path :
    #Here i verify if ShaderToolsImport Folder exists:
    CopyBlendFolder = os.path.join(ImportPath, "ShaderToolsImport")

    if not os.path.exists(CopyBlendFolder) :
        os.makedirs(CopyBlendFolder)

    #Here i verify if Material Name Folder exists:
    CopyMatFolder = os.path.join(ImportPath, "ShaderToolsImport", Mat_Name)
    CopyMatFolder = stripext(CopyMatFolder, '.blex')
    Mat_Name_folder = stripext(Mat_Name, '.blex')

    # generate a unique folder name to hold the files
    c = 0
    while True :
        CopyMatFolder = os.path.join(ImportPath, "ShaderToolsImport", Mat_Name_folder + ("", "_%d" % c)[c != 0])
        if not os.path.exists(CopyMatFolder) :
            # found unused name
            os.makedirs(CopyMatFolder)
            break
        #end if
        # already exists, try another name
        c += 1
    #end while

    #Now I can copy Zip Files in new Material Folder:
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f):
            shutil.copy2(os.path.join(ZipPath, f), os.path.join(CopyMatFolder, f))


    #Here I must find .py script:
    script_name = ''
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith('.py'):
            script_name = f

    if script_name == '':
        print(LanguageValuesDict['ErrorsMenuError008'])

    else:

        #Here I save script in a list:
        MY_SCRIPT_LIST = []
        env_file = open(os.path.join(CopyMatFolder, script_name),'r')

        for values in env_file:
            if values == "!*- environnement path -*!" or values == "!*- environnement path -*!\n":
                path = "scriptPath = '" + CopyMatFolder + "'"

                MY_SCRIPT_LIST.append(path)
            else:
                MY_SCRIPT_LIST.append(values)

        env_file.close()

        #I remove old script and I create a new script in Material Folder:
        os.remove(os.path.join(CopyMatFolder, script_name))
        new_script = open(os.path.join(CopyMatFolder, script_name), "w")

        c = 0
        for values in MY_SCRIPT_LIST:
            new_script.write(MY_SCRIPT_LIST[c])
            c = c +1

        new_script.close()

        #Now I execute the zip script file:
        bpy.ops.script.python_file_run(filepath=os.path.join(CopyMatFolder, script_name))



    print(LanguageValuesDict['ErrorsMenuError007'])
    print("*******************************************************")


# ************************************************************************************
# *                                           IMPORT                                 *
# ************************************************************************************
class Import(bpy.types.Operator):
    bl_idname = "object.shadertools_import"
    bl_label = LanguageValuesDict['ImportMenuTitle']

    filename = bpy.props.StringProperty(subtype="FILENAME")
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        Importer(self.filepath, self.filename)
        return {'FINISHED'}

# ************************************************************************************
# *                                           EXPORT                                 *
# ************************************************************************************
class Export(bpy.types.Operator):
    bl_idname = "object.shadertools_export"
    bl_label = LanguageValuesDict['ExportMenuTitle']

    DefaultCreator = DefaultCreator.replace('\n', '')
    filename = bpy.props.StringProperty(subtype="FILENAME")
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    #I prepare the window :
    Inf_Creator = bpy.props.StringProperty(name=LanguageValuesDict['ExportMenuCreator'], default=DefaultCreator)
    Take_a_preview = bpy.props.BoolProperty(name=LanguageValuesDict['ExportMenuTakePreview'], default=False)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LanguageValuesDict['ExportMenuLabel01'] + ":")
        row = layout.row(align=True)
        row.prop(self, "Inf_Creator")
        row = layout.row(align=True)
        row.prop(self, "Take_a_preview")
        row = layout.row(align=True)

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        Exporter(self.filepath, self.filename, self.Inf_Creator, self.Take_a_preview)
        return {'FINISHED'}

# ************************************************************************************
# *                                    SAVE CURRENT SHADER                           *
# ************************************************************************************
class SaveCurrentConfiguration(bpy.types.Operator):
    bl_idname = "object.shadertools_saveconfiguration"
    bl_label = LanguageValuesDict['SaveMenuTitle']

    #I normalize values:
    DefaultCreator = DefaultCreator.replace('\n', '')
    DefaultDescription = DefaultDescription.replace('\n', '')
    DefaultWeblink = DefaultWeblink.replace('\n', '')
    DefaultMaterialName = DefaultMaterialName.replace('\n', '')
    DefaultCategory = DefaultCategory.replace('\n', '')
    DefaultEmail = DefaultEmail.replace('\n', '')

    #I prepare the window :
    Inf_Creator = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuCreator'], default=DefaultCreator)
    Inf_Category = bpy.props.EnumProperty \
      (
        name = LanguageValuesDict['SaveCategoryTitle'],
        items =
                (
                    ('', "---- " + LanguageValuesDict['SaveCategoryCategoryTitle'] + " ----", ""),
                )
            +
                tuple
                  (
                    (c, LanguageValuesDict["SaveCategory" + c], "") for c in MaterialCategories
                  ),
        default = DefaultCategory
      )

    Inf_Description = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuDescriptionLabel'], default=DefaultDescription)
    Inf_Weblink = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuWebLinkLabel'], default=DefaultWeblink)
    Inf_Email = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuEmailLabel'], default=DefaultEmail)
    Mat_Name = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuName'], default=DefaultMaterialName)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LanguageValuesDict['SaveMenuLabel01'] + ":")
        row = layout.row(align=True)
        row.prop(self, "Mat_Name")
        row = layout.row(align=True)
        row.prop(self, "Inf_Creator")
        row = layout.row(align=True)
        row.prop(self, "Inf_Category")
        row = layout.row(align=True)
        row.prop(self, "Inf_Description")
        row = layout.row(align=True)
        row.prop(self, "Inf_Weblink")
        row = layout.row(align=True)
        row.prop(self, "Inf_Email")

    def invoke(self, context, event):
        #I verify if an object it's selected :
        wm = context.window_manager
        wm.invoke_props_dialog(self, width=500)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        time.sleep(1) #Wait one second before execute Update because Blender can executing other thread and can crashed
        UpdateDatabase(self.Inf_Creator, self.Inf_Category, self.Inf_Description, self.Inf_Weblink, self.Inf_Email,self.Mat_Name)
        return {'FINISHED'}

# ************************************************************************************
# *                                  UPDATE WARNING                                  *
# ************************************************************************************
class UpdateWarning(bpy.types.Operator):
    bl_idname = "object.shadertools_warning"
    bl_label = LanguageValuesDict['WarningWinTitle']

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LanguageValuesDict['WarningWinLabel01'], icon='RADIO')
        row = layout.row(align=True)
        row.label(LanguageValuesDict['WarningWinLabel02'])
        row = layout.row(align=True)
        row.label(LanguageValuesDict['WarningWinLabel03'])
        row = layout.row(align=True)

    def invoke(self, context, event):
        #I verify if an object it's selected :
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500, height=480)

    def execute(self, context):
        return {'FINISHED'}

# ************************************************************************************
# *                                      CONFIGURATION                               *
# ************************************************************************************
class Configuration(bpy.types.Operator):
    bl_idname = "object.shadertools_configuration"
    bl_label = LanguageValuesDict['ConfigurationMenuTitle']

    #I normalize values:
    DefaultCreator = DefaultCreator.replace('\n', '')
    DefaultDescription = DefaultDescription.replace('\n', '')
    DefaultWeblink = DefaultWeblink.replace('\n', '')
    DefaultMaterialName = DefaultMaterialName.replace('\n', '')
    DefaultCategory = DefaultCategory.replace('\n', '')
    DefaultEmail = DefaultEmail.replace('\n', '')
    Resolution_X = str(Resolution_X)
    Resolution_Y = str(Resolution_Y)
    Resolution_X = str(Resolution_X.replace('\n', ''))
    Resolution_Y = str(Resolution_Y.replace('\n', ''))
    DefaultLanguage = DefaultLanguage.replace('\n', '')

    #I prepare the window :
    DataBasePathFile = bpy.props.StringProperty(name=LanguageValuesDict['ConfigurationMenuDataBasePath'], default=DataBasePath)
    Inf_Creator = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuCreator'], default=DefaultCreator)
    Inf_Category = bpy.props.EnumProperty \
      (
        name = LanguageValuesDict['SaveCategoryTitle'],
        items =
                (
                    ('', "---- " + LanguageValuesDict['SaveCategoryCategoryTitle'] + " ----", ""),
                )
            +
                tuple
                  (
                    (c, LanguageValuesDict["SaveCategory" + c], "") for c in MaterialCategories
                  ),
        default = DefaultCategory
      )

    Inf_Description = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuDescriptionLabel'], default=DefaultDescription)
    Inf_Weblink = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuWebLinkLabel'], default=DefaultWeblink)
    Inf_Email = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuEmailLabel'], default=DefaultEmail)

    Mat_Name = bpy.props.StringProperty(name=LanguageValuesDict['SaveMenuName'], default=DefaultMaterialName)


    Inf_ResolutionX = bpy.props.StringProperty(name=LanguageValuesDict['ConfigurationMenuResolutionPreviewX'], default=Resolution_X)
    Inf_ResolutionY = bpy.props.StringProperty(name=LanguageValuesDict['ConfigurationMenuResolutionPreviewY'], default=Resolution_Y)
    Inf_Language = bpy.props.EnumProperty \
      (
        name = LanguageValuesDict['ConfigurationMenuLabel05'],
        items =
            ( # fixme: build this list dynamically and put language names into lang files themselves
                ('en_US', 'English', ""),
                ('fr_FR', 'French', ""),
                ('de_DE', 'Deutsch', ""),
                ('es_ES', 'Spanish', ""),
            ),
        default = DefaultLanguage
      )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LanguageValuesDict['ConfigurationMenuLabel04'] + ":")
        row = layout.row(align=True)
        row.prop(self, "Inf_Language")
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LanguageValuesDict['ConfigurationMenuLabel02'] + ":")
        row = layout.row(align=True)
        row.prop(self, "DataBasePathFile")
        row = layout.row(align=True)
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LanguageValuesDict['SaveMenuLabel01'] + ":")
        row = layout.row(align=True)
        row.prop(self, "Mat_Name")
        row = layout.row(align=True)
        row.prop(self, "Inf_Creator")
        row = layout.row(align=True)
        row.prop(self, "Inf_Category")
        row = layout.row(align=True)
        row.prop(self, "Inf_Description")
        row = layout.row(align=True)
        row.prop(self, "Inf_Weblink")
        row = layout.row(align=True)
        row.prop(self, "Inf_Email")
        row = layout.row(align=True)
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LanguageValuesDict['ConfigurationMenuLabel03'] + ":")
        row = layout.row(align=True)
        row.prop(self, "Inf_ResolutionX")
        row = layout.row(align=True)
        row.prop(self, "Inf_ResolutionY")
        row = layout.row(align=True)

    def invoke(self, context, event):
        #I verify if an object it's selected :
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def execute(self, context):
        #Delete configuration file:
        os.remove(ConfigPath)

        #Create a new configuration file:
        config = open(ConfigPath,'w')
        config.write(AppPath + '\n')
        config.write(self.DataBasePathFile + '\n')
        config.write(self.Inf_Creator + '\n')
        config.write(self.Inf_Description + '\n')
        config.write(self.Inf_Weblink + '\n')
        config.write(self.Mat_Name + '\n')
        config.write(self.Inf_Category + '\n')
        config.write(self.Inf_Email + '\n')
        config.write(self.Inf_ResolutionX + '\n')
        config.write(self.Inf_ResolutionY + '\n')
        config.write(self.Inf_Language + '\n')

        config.close()

        bpy.ops.script.python_file_run(filepath=os.path.join(AppPath, "__init__.py"))
        return {'FINISHED'}

# ************************************************************************************
# *                                     CREATE NEW                                   *
# ************************************************************************************
class CreateNew(bpy.types.Operator):
    bl_idname = "object.shadertools_createnew"
    bl_label = "New"

    def execute(self, context):
        #I delete old modele and I copy new empty modele:
        if os.path.exists(os.path.join(AppPath, "env_base_save.blend")) :
            os.remove(os.path.join(AppPath, "env_base_save.blend"))

        if os.path.exists(os.path.join(AppPath, "env_base_save")) :
            shutil.copy2(os.path.join(AppPath, "env_base_save"), os.path.join(AppPath, "env_base_save.blend"))


        #I open modele file:
        if platform.system() == 'Windows':
            env_base_save= os.popen('"' + os.path.join(AppPath, 'env_base_save.blend') + '"')

        if platform.system() == 'Darwin':
            env_base_save= os.popen("open '" + bpy.app.binary_path + " '" + os.path.join(AppPath, "env_base_save.blend") + "'")

        if platform.system() == 'Linux':
            env_base_save= os.popen(bpy.app.binary_path + " '" + os.path.join(AppPath, "env_base_save.blend") + "'")

        return {'FINISHED'}

# ************************************************************************************
# *                                           MAIN                                   *
# ************************************************************************************

MyRegClasses = \
    (
        SaveCurrentConfiguration,
        UpdateWarning,
        OpenShaders,
        Configuration,
        Export,
        Import,
        Credits,
        CreateNew,
        Help,
    )

def add_my_panel(self, context) :
    layout = self.layout
    row = layout.row()
    row.operator(OpenShaders.bl_idname, text=LanguageValuesDict['ButtonsOpen'], icon="NEWFOLDER" )
    row.operator(SaveCurrentConfiguration.bl_idname, text=LanguageValuesDict['ButtonsSave'], icon="MATERIAL" )
    row.operator(Export.bl_idname, text=LanguageValuesDict['ButtonsExport'], icon="SCRIPTWIN" )
    row.operator(Import.bl_idname, text=LanguageValuesDict['ButtonsImport'], icon="SCRIPTWIN" )
    row = layout.row()
    row.operator(CreateNew.bl_idname, text=LanguageValuesDict['ButtonsCreate'], icon="BLENDER" )
    row.operator(Configuration.bl_idname, text=LanguageValuesDict['ButtonsConfiguration'], icon="TEXT" )
    row.operator(Help.bl_idname, text=LanguageValuesDict['ButtonsHelp'], icon="HELP")
    row.operator(Credits.bl_idname, text="Credits", icon="QUESTION")
    row = layout.row()
#end add_my_panel

def register():
    for c in MyRegClasses :
        bpy.utils.register_class(c)
    #end for
    bpy.types.MATERIAL_PT_context_material.append(add_my_panel)
#end register

def unregister():
    bpy.types.MATERIAL_PT_context_material.remove(add_my_panel)
    for c in MyRegClasses :
        bpy.utils.unregister_class(c)
    #end for
#end unregister

# ************************************************************************************
# *                           UPDATE BOOKMARKS INFORMATIONS                          *
# ************************************************************************************

#Create a new configuration file:
#Bookmarks USER
shaderFolderPath = os.path.join(AppPath, LanguageValuesDict['BookmarksMenuName'])
if os.path.exists(BookmarksPathUser) :
    shutil.copy2(BookmarksPathUser, BookmarksPathUser+"_2")
    value = ""
    bookmarks_category = False
    updateInformation = True
    MY_BOOKMARKS_FILE = []
    #I verify Shader tempory File is correcly created:
    if not os.path.exists(shaderFolderPath) :
        os.makedirs(shaderFolderPath)

    #Here I copy bookmarks and i verify if Shader Tempory folder exist:
    bookmarkspathfile = open(BookmarksPathUser,'r')
    for value in bookmarkspathfile:
        MY_BOOKMARKS_FILE.append(value)

        if value=='[Bookmarks]' or value=='[Bookmarks]\n':
            bookmarks_category = True

        if value=='[Recent]' or value=='[Recent]\n':
            bookmarks_category = False

        if bookmarks_category :
            if shaderFolderPath in value:
                updateInformation = False #No update necessary

    bookmarkspathfile.close()

    #I create new bookmarks:
    if updateInformation :
        print("I update")
        os.remove(BookmarksPathUser)
        bookmarkspathfile = open(BookmarksPathUser,'w')
        for value in MY_BOOKMARKS_FILE:

            if value=='[Bookmarks]' or value=='[Bookmarks]\n':
                bookmarkspathfile.write(value)
                bookmarkspathfile.write(shaderFolderPath+"\n")
            else:
                bookmarkspathfile.write(value)

        bookmarkspathfile.close()
        if not os.path.exists(os.path.join(AppPath, "first")) :
            firstFile = open(os.path.join(AppPath, "first"),'w')
            firstFile.write("update bookmarks\n")
            firstFile.close()


#Delete Preview Jpg:
if os.path.exists(shaderFolderPath) :
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and f.endswith(".jpg"):
            os.remove(os.path.join(shaderFolderPath, f))

        else:
            os.remove(os.path.join(shaderFolderPath, f))

if __name__ == "__main__":
    register()
