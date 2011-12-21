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






# ************************************************************************************
# *                                      IMPORTS MODULES                             *
# ************************************************************************************
import bpy
from bpy.types import Header
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       )

import sqlite3
import os
import platform
import locale
import shutil
import zipfile
import time
import sys


# ************************************************************************************
# *                                     MY GLOBAL VALUES                             *
# ************************************************************************************
MY_RENDER_TABLE = []

MY_MATERIAL_TABLE = []

MY_INFORMATION_TABLE = []

NAME_ACTIVE_MATERIAL = False



# ************************************************************************************
# *                                     HERE I UPDATE PATH                           *
# ************************************************************************************
DefaultCreator = "You"
DefaultDescription = "material description"
DefaultWeblink = "http://"
DefaultMaterialName = "Material"
DefaultCategory = "Personal"
DefaultEmail = "my_email@company.com"
Resolution_X = 120
Resolution_Y = 120

BlendPath = os.path.dirname(bpy.data.filepath)
AppPath = os.path.join(bpy.utils.user_resource("SCRIPTS"), "addons", "shader_tools")
ExportPath = os.path.dirname(bpy.data.filepath) # not used anywhere
ImportPath = os.path.dirname(bpy.data.filepath)
ErrorsPath = os.path.join(AppPath, "erro")
OutPath = os.path.join(AppPath, "out")
DataBasePath = os.path.join(AppPath, "ShaderToolsDatabase.sqlite")
ZipPath = os.path.join(AppPath, "zip")


#Config Path :
if os.path.exists(os.path.join(AppPath, "config")) :
    config = open(os.path.join(AppPath, "config"), 'r')
    AppPath = config.readline().rstrip("\n")
    ExportPath = config.readline().rstrip("\n")
    DataBasePath = config.readline().rstrip("\n")
    DefaultCreator = config.readline().rstrip("\n")
    DefaultDescription = config.readline().rstrip("\n")
    DefaultWeblink = config.readline().rstrip("\n")
    DefaultMaterialName = config.readline().rstrip("\n")
    DefaultCategory = config.readline().rstrip("\n")
    DefaultEmail = config.readline().rstrip("\n")
    Resolution_X = config.readline().rstrip("\n")
    Resolution_Y = config.readline().rstrip("\n")


    if ExportPath == "" or ExportPath == "\n":
        config.close()
        config = open(os.path.join(AppPath, "config"), 'w')
        config.write(AppPath + '\n')
        config.write(ExportPath + '\n')
        config.write(DataBasePath + '\n')
        config.write(DefaultCreator + '\n')
        config.write(DefaultDescription + '\n')
        config.write(DefaultWeblink + '\n')
        config.write(DefaultMaterialName + '\n')
        config.write(DefaultCategory + '\n')
        config.write(DefaultEmail + '\n')
        config.write(str(Resolution_X) + '\n')
        config.write(str(Resolution_Y) + '\n')


else:
    config = open(os.path.join(AppPath, "config"),'w')
    config.write(AppPath + '\n')
    config.write(ExportPath + '\n')
    config.write(DataBasePath + '\n')
    config.write(DefaultCreator + '\n')
    config.write(DefaultDescription + '\n')
    config.write(DefaultWeblink + '\n')
    config.write(DefaultMaterialName + '\n')
    config.write(DefaultCategory + '\n')
    config.write(DefaultEmail + '\n')
    config.write(str(Resolution_X) + '\n')
    config.write(str(Resolution_Y) + '\n')


config.close()


BookmarksPathUser = os.path.join(bpy.utils.resource_path('USER', major=bpy.app.version[0], minor=bpy.app.version[1]), "config", "bookmarks.txt")
BookmarksPathSystem = os.path.join(bpy.utils.resource_path('SYSTEM', major=bpy.app.version[0], minor=bpy.app.version[1]), "config", "bookmarks.txt")



TempPath = os.path.join(AppPath, "temp")
if os.path.exists(TempPath) :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
            os.remove(os.path.join(TempPath, f))
        else:
            os.remove(os.path.join(TempPath, f))

else:
    os.mkdir(TempPath)







# ************************************************************************************
# *                                       HISTORY FILE                               *
# ************************************************************************************
HISTORY_FILE = []

if os.path.exists(os.path.join(AppPath, "history")) :
    history = open(os.path.join(AppPath, "history"),'r')
    x = 0
    for values in history:
        if x > 0:
            values = values.replace("History" + str(x) + "=" , "")
            values = values.replace("\n" , "")
            HISTORY_FILE.append(values)

        x = x + 1


else:
    history = open(os.path.join(AppPath, "history"),'w')
    history.write('[HISTORY]\n')
    x = 1
    while x <= 20:
        history.write('History' + str(x) + '=\n')
        x = x + 1

    history.close()


    history = open(os.path.join(AppPath, "history"),'r')
    x = 0
    for values in history:
        if x > 0:
            values = values.replace("History" + str(x) + "=" , "")
            values = values.replace("\n" , "")
            HISTORY_FILE.append(values)

        x = x + 1



history.close()






# ************************************************************************************
# *                                     LANGAGE PARAMETERS                           *
# ************************************************************************************


def LangageValues(langageUser, langageDict):

    #I open langage file:
    readValue = ""
    readValueList = ""
    categoryConfig = '[Panel]'
    saveCategoryConfig = ""
    section = ''
    sectionValue = ''
    value=""


    langageFile = open(os.path.join(AppPath, "lang", langageUser),'r')

    for readValue in langageFile:

        c = 0
        for value in readValue.split('=', 1):

            if c == 0:
                section = value

            else:
                sectionValue = value


            c = c + 1



        if readValue == '*!-*':
            saveCategoryConfig == ''

        section = section.replace('\n','')
        sectionValue = sectionValue.replace('\n','')

        #Panel Values :
        if section == '[Panel]' or saveCategoryConfig == '[Panel]':

            if section == 'Name':
                langageDict['PanelName'] = sectionValue

            saveCategoryConfig = '[Panel]'


        #Find Image Values :
        if section == '[FindImageMenu]' or saveCategoryConfig == '[FindImageMenu]':

            if section == 'Name':
                langageDict['FindImageMenuName'] = sectionValue

            saveCategoryConfig = '[FindImageMenu]'



        #Buttons Values :
        if section == '[Buttons]' or saveCategoryConfig == '[Buttons]':

            if section == 'Open':
                langageDict['ButtonsOpen'] = sectionValue

            if section == 'Save':
                langageDict['ButtonsSave'] = sectionValue

            if section == 'Configuration':
                langageDict['ButtonsConfiguration'] = sectionValue

            if section == 'Export':
                langageDict['ButtonsExport'] = sectionValue

            if section == 'Import':
                langageDict['ButtonsImport'] = sectionValue

            if section == 'Help':
                langageDict['ButtonsHelp'] = sectionValue

            if section == 'Informations':
                langageDict['ButtonsInformations'] = sectionValue


            if section == 'Create':
                langageDict['ButtonsCreate'] = sectionValue



            saveCategoryConfig = '[Buttons]'



        #OpenMenu Values :
        if section == '[OpenMenu]' or saveCategoryConfig == '[OpenMenu]':

            if section == 'Title':
                langageDict['OpenMenuTitle'] = sectionValue

            if section == 'Label01':
                langageDict['OpenMenuLabel01'] = sectionValue

            if section == 'Label02':
                langageDict['OpenMenuLabel02'] = sectionValue

            if section == 'Label03':
                langageDict['OpenMenuLabel03'] = sectionValue

            if section == 'Label04':
                langageDict['OpenMenuLabel04'] = sectionValue

            if section == 'Label05':
                langageDict['OpenMenuLabel05'] = sectionValue

            if section == 'Label06':
                langageDict['OpenMenuLabel06'] = sectionValue

            if section == 'Label07':
                langageDict['OpenMenuLabel07'] = sectionValue

            if section == 'Label08':
                langageDict['OpenMenuLabel08'] = sectionValue


            if section == 'Label09':
                langageDict['OpenMenuLabel09'] = sectionValue




            saveCategoryConfig = '[OpenMenu]'



        #BookmarksMenu Values :
        if section == '[BookmarksMenu]' or saveCategoryConfig == '[BookmarksMenu]':

            if section == 'Name':
                langageDict['BookmarksMenuName'] = sectionValue

            saveCategoryConfig = '[BookmarksMenu]'



        #BookmarksMenu Values :
        if section == '[ErrorsMenu]' or saveCategoryConfig == '[ErrorsMenu]':

            if section == 'Error001':
                langageDict['ErrorsMenuError001'] = sectionValue

            if section == 'Error002':
                langageDict['ErrorsMenuError002'] = sectionValue

            if section == 'Error003':
                langageDict['ErrorsMenuError003'] = sectionValue

            if section == 'Error004':
                langageDict['ErrorsMenuError004'] = sectionValue

            if section == 'Error005':
                langageDict['ErrorsMenuError005'] = sectionValue

            if section == 'Error006':
                langageDict['ErrorsMenuError006'] = sectionValue

            if section == 'Error007':
                langageDict['ErrorsMenuError007'] = sectionValue

            if section == 'Error008':
                langageDict['ErrorsMenuError008'] = sectionValue

            if section == 'Error009':
                langageDict['ErrorsMenuError009'] = sectionValue

            if section == 'Error010':
                langageDict['ErrorsMenuError010'] = sectionValue

            if section == 'Error011':
                langageDict['ErrorsMenuError011'] = sectionValue

            if section == 'Error012':
                langageDict['ErrorsMenuError012'] = sectionValue

            if section == 'Error013':
                langageDict['ErrorsMenuError013'] = sectionValue


            if section == 'Error014':
                langageDict['ErrorsMenuError014'] = sectionValue

            if section == 'Error015':
                langageDict['ErrorsMenuError015'] = sectionValue

            if section == 'Error016':
                langageDict['ErrorsMenuError016'] = sectionValue

            if section == 'Error017':
                langageDict['ErrorsMenuError017'] = sectionValue

            if section == 'Error018':
                langageDict['ErrorsMenuError018'] = sectionValue

            if section == 'Error019':
                langageDict['ErrorsMenuError019'] = sectionValue

            if section == 'Error020':
                langageDict['ErrorsMenuError020'] = sectionValue



            saveCategoryConfig = '[ErrorsMenu]'



        #InformationsMenu Values :
        if section == '[InformationsMenu]' or saveCategoryConfig == '[InformationsMenu]':

            if section == 'Title':
                langageDict['InformationsMenuTitle'] = sectionValue


            if section == 'LabelName':
                langageDict['InformationsMenuLabelName'] = sectionValue


            if section == 'Name':
                langageDict['InformationsMenuName'] = sectionValue


            if section == 'LabelCreator':
                langageDict['InformationsMenuLabelCreator'] = sectionValue


            if section == 'Creator':
                langageDict['InformationsMenuCreator'] = sectionValue


            if section == 'LabelCategory':
                langageDict['InformationsMenuLabelCategory'] = sectionValue


            if section == 'Category':
                langageDict['InformationsMenuCategory'] = sectionValue


            if section == 'LabelDescription':
                langageDict['InformationsMenuLabelDescription'] = sectionValue


            if section == 'Description':
                langageDict['InformationsMenuDescription'] = sectionValue


            if section == 'LabelWebLink':
                langageDict['InformationsMenuLabelWebLink'] = sectionValue


            if section == 'WebLink':
                langageDict['InformationsMenuWebLink'] = sectionValue


            if section == 'LabelEmail':
                langageDict['InformationsMenuLabelEmail'] = sectionValue


            if section == 'Email':
                langageDict['InformationsMenuEmail'] = sectionValue


            saveCategoryConfig = '[InformationsMenu]'






        #WarningWin Values :
        if section == '[WarningWin]' or saveCategoryConfig == '[WarningWin]':

            if section == 'Title':
                langageDict['WarningWinTitle'] = sectionValue


            if section == 'Label01':
                langageDict['WarningWinLabel01'] = sectionValue

            if section == 'Label02':
                langageDict['WarningWinLabel02'] = sectionValue

            if section == 'Label03':
                langageDict['WarningWinLabel03'] = sectionValue

            if section == 'Label04':
                langageDict['WarningWinLabel04'] = sectionValue

            if section == 'Label05':
                langageDict['WarningWinLabel05'] = sectionValue

            if section == 'Label06':
                langageDict['WarningWinLabel06'] = sectionValue

            if section == 'Label07':
                langageDict['WarningWinLabel07'] = sectionValue

            if section == 'Label08':
                langageDict['WarningWinLabel08'] = sectionValue

            if section == 'Label09':
                langageDict['WarningWinLabel09'] = sectionValue

            if section == 'Label10':
                langageDict['WarningWinLabel10'] = sectionValue


            saveCategoryConfig = '[WarningWin]'




        #SaveMenu Values :
        if section == '[SaveMenu]' or saveCategoryConfig == '[SaveMenu]':

            if section == 'Title':
                langageDict['SaveMenuTitle'] = sectionValue


            if section == 'Label01':
                langageDict['SaveMenuLabel01'] = sectionValue

            if section == 'Name':
                langageDict['SaveMenuName'] = sectionValue

            if section == 'Creator':
                langageDict['SaveMenuCreator'] = sectionValue

            if section == 'CreatorValue':
                langageDict['SaveMenuCreatorValue'] = sectionValue

            if section == 'CategoryDefault':
                langageDict['SaveMenuCategoryDefault'] = sectionValue

            if section == 'DescriptionLabel':
                langageDict['SaveMenuDescriptionLabel'] = sectionValue


            if section == 'Description':
                langageDict['SaveMenuDescription'] = sectionValue

            if section == 'WebLinkLabel':
                langageDict['SaveMenuWebLinkLabel'] = sectionValue

            if section == 'WebLink':
                langageDict['SaveMenuWebLink'] = sectionValue

            if section == 'EmailLabel':
                langageDict['SaveMenuEmailLabel'] = sectionValue

            if section == 'Email':
                langageDict['SaveMenuEmail'] = sectionValue

            if section == 'Warning01':
                langageDict['SaveMenuWarning01'] = sectionValue

            if section == 'Warning02':
                langageDict['SaveMenuWarning02'] = sectionValue

            if section == 'Warning03':
                langageDict['SaveMenuWarning03'] = sectionValue

            if section == 'Warning04':
                langageDict['SaveMenuWarning04'] = sectionValue

            if section == 'Warning05':
                langageDict['SaveMenuWarning05'] = sectionValue


            saveCategoryConfig = '[SaveMenu]'


        #SaveCategory Values :
        if section == '[SaveCategory]' or saveCategoryConfig == '[SaveCategory]':

            if section == 'Title':
                langageDict['SaveCategoryTitle'] = sectionValue

            if section == 'CategoryTitle':
                langageDict['SaveCategoryCategoryTitle'] = sectionValue

            if section == 'CarPaint':
                langageDict['SaveCategoryCarPaint'] = sectionValue

            if section == 'Dirt':
                langageDict['SaveCategoryDirt'] = sectionValue

            if section == 'FabricClothes':
                langageDict['SaveCategoryFabricClothes'] = sectionValue

            if section == 'Fancy':
                langageDict['SaveCategoryFancy'] = sectionValue

            if section == 'FibreFur':
                langageDict['SaveCategoryFibreFur'] = sectionValue

            if section == 'Glass':
                langageDict['SaveCategoryGlass'] = sectionValue

            if section == 'Halo':
                langageDict['SaveCategoryHalo'] = sectionValue

            if section == 'Liquids':
                langageDict['SaveCategoryLiquids'] = sectionValue

            if section == 'Metal':
                langageDict['SaveCategoryMetal'] = sectionValue

            if section == 'Misc':
                langageDict['SaveCategoryMisc'] = sectionValue

            if section == 'Nature':
                langageDict['SaveCategoryNature'] = sectionValue

            if section == 'Organic':
                langageDict['SaveCategoryOrganic'] = sectionValue

            if section == 'Personal':
                langageDict['SaveCategoryPersonal'] = sectionValue

            if section == 'Plastic':
                langageDict['SaveCategoryPlastic'] = sectionValue

            if section == 'Sky':
                langageDict['SaveCategorySky'] = sectionValue

            if section == 'Space':
                langageDict['SaveCategorySpace'] = sectionValue

            if section == 'Stone':
                langageDict['SaveCategoryStone'] = sectionValue

            if section == 'Toon':
                langageDict['SaveCategoryToon'] = sectionValue

            if section == 'Wall':
                langageDict['SaveCategoryWall'] = sectionValue

            if section == 'Water':
                langageDict['SaveCategoryWater'] = sectionValue

            if section == 'Wood':
                langageDict['SaveCategoryWood'] = sectionValue

            saveCategoryConfig = '[SaveCategory]'


        #ConfigurationMenu Values :
        if section == '[ConfigurationMenu]' or saveCategoryConfig == '[ConfigurationMenu]':

            if section == 'Title':
                langageDict['ConfigurationMenuTitle'] = sectionValue

            if section == 'Label01':
                langageDict['ConfigurationMenuLabel01'] = sectionValue

            if section == 'ExportPath':
                langageDict['ConfigurationMenuExportPath'] = sectionValue

            if section == 'Label02':
                langageDict['ConfigurationMenuLabel02'] = sectionValue

            if section == 'Label03':
                langageDict['ConfigurationMenuLabel03'] = sectionValue

            if section == 'ResolutionPreviewX':
                langageDict['ConfigurationMenuResolutionPreviewX'] = sectionValue

            if section == 'ResolutionPreviewY':
                langageDict['ConfigurationMenuResolutionPreviewY'] = sectionValue

            if section == 'DataBasePath':
                langageDict['ConfigurationMenuDataBasePath'] = sectionValue

            if section == 'Warning01':
                langageDict['ConfigurationMenuWarning01'] = sectionValue

            if section == 'Warning02':
                langageDict['ConfigurationMenuWarning02'] = sectionValue

            if section == 'Warning03':
                langageDict['ConfigurationMenuWarning03'] = sectionValue

            if section == 'Warning04':
                langageDict['ConfigurationMenuWarning04'] = sectionValue

            if section == 'Warning05':
                langageDict['ConfigurationMenuWarning05'] = sectionValue

            saveCategoryConfig = '[ConfigurationMenu]'


        #ExportMenu Values :
        if section == '[ExportMenu]' or saveCategoryConfig == '[ExportMenu]':

            if section == 'Title':
                langageDict['ExportMenuTitle'] = sectionValue

            if section == 'Label01':
                langageDict['ExportMenuLabel01'] = sectionValue

            if section == 'Name':
                langageDict['ExportMenuName'] = sectionValue

            if section == 'Creator':
                langageDict['ExportMenuCreator'] = sectionValue

            if section == 'CreatorDefault':
                langageDict['ExportMenuCreatorDefault'] = sectionValue

            if section == 'TakePreview':
                langageDict['ExportMenuTakePreview'] = sectionValue

            saveCategoryConfig = '[ExportMenu]'


        #ImportMenu Values :
        if section == '[ImportMenu]' or saveCategoryConfig == '[ImportMenu]':

            if section == 'Title':
                langageDict['ImportMenuTitle'] = sectionValue


            saveCategoryConfig = '[ImportMenu]'





        #HelpMenu Values :
        if section == '[HelpMenu]' or saveCategoryConfig == '[HelpMenu]':

            if section == 'Title':
                langageDict['HelpMenuTitle'] = sectionValue

            if section == 'Label01':
                langageDict['HelpMenuLabel01'] = sectionValue

            if section == 'Label02':
                langageDict['HelpMenuLabel02'] = sectionValue

            if section == 'Label03':
                langageDict['HelpMenuLabel03'] = sectionValue

            if section == 'Label04':
                langageDict['HelpMenuLabel04'] = sectionValue

            if section == 'Label05':
                langageDict['HelpMenuLabel05'] = sectionValue

            if section == 'Label06':
                langageDict['HelpMenuLabel06'] = sectionValue

            if section == 'Label07':
                langageDict['HelpMenuLabel07'] = sectionValue

            if section == 'Label08':
                langageDict['HelpMenuLabel08'] = sectionValue

            if section == 'Label09':
                langageDict['HelpMenuLabel09'] = sectionValue

            if section == 'Label10':
                langageDict['HelpMenuLabel10'] = sectionValue

            if section == 'Label11':
                langageDict['HelpMenuLabel11'] = sectionValue

            if section == 'Label12':
                langageDict['HelpMenuLabel12'] = sectionValue

            if section == 'Label13':
                langageDict['HelpMenuLabel13'] = sectionValue

            if section == 'Label14':
                langageDict['HelpMenuLabel14'] = sectionValue

            if section == 'Label15':
                langageDict['HelpMenuLabel15'] = sectionValue

            if section == 'Label16':
                langageDict['HelpMenuLabel16'] = sectionValue

            if section == 'Label17':
                langageDict['HelpMenuLabel17'] = sectionValue

            if section == 'Label18':
                langageDict['HelpMenuLabel18'] = sectionValue

            if section == 'Label19':
                langageDict['HelpMenuLabel19'] = sectionValue

            if section == 'Label20':
                langageDict['HelpMenuLabel20'] = sectionValue

            if section == 'Label21':
                langageDict['HelpMenuLabel21'] = sectionValue

            if section == 'Label22':
                langageDict['HelpMenuLabel22'] = sectionValue

            if section == 'Label23':
                langageDict['HelpMenuLabel23'] = sectionValue

            if section == 'Label24':
                langageDict['HelpMenuLabel24'] = sectionValue

            if section == 'Label25':
                langageDict['HelpMenuLabel25'] = sectionValue

            if section == 'Label26':
                langageDict['HelpMenuLabel26'] = sectionValue

            if section == 'Label27':
                langageDict['HelpMenuLabel27'] = sectionValue

            if section == 'Label28':
                langageDict['HelpMenuLabel28'] = sectionValue

            if section == 'Label29':
                langageDict['HelpMenuLabel29'] = sectionValue


            if section == 'Label30':
                langageDict['HelpMenuLabel30'] = sectionValue

            if section == 'Label31':
                langageDict['HelpMenuLabel31'] = sectionValue

            if section == 'Label32':
                langageDict['HelpMenuLabel32'] = sectionValue

            if section == 'Label33':
                langageDict['HelpMenuLabel33'] = sectionValue

            if section == 'Label34':
                langageDict['HelpMenuLabel34'] = sectionValue

            if section == 'Label35':
                langageDict['HelpMenuLabel35'] = sectionValue

            if section == 'Label36':
                langageDict['HelpMenuLabel36'] = sectionValue

            if section == 'Label37':
                langageDict['HelpMenuLabel37'] = sectionValue

            if section == 'Label38':
                langageDict['HelpMenuLabel38'] = sectionValue

            if section == 'Label39':
                langageDict['HelpMenuLabel39'] = sectionValue

            if section == 'Label40':
                langageDict['HelpMenuLabel40'] = sectionValue

            saveCategoryConfig = '[HelpMenu]'


    langageFile.close()
    return langageDict








#Open langage file:
c = 0
value =""
langage = ""
LangageValuesDict = {'PanelName':'',

    'ButtonsOpen':'',
    'ButtonsSave':'',
    'ButtonsConfiguration':'',
    'ButtonsExport':'',
    'ButtonsImport':'',
    'ButtonsHelp':'',
    'ButtonsInformations':'',
    'ButtonsCreate':'',

    'OpenMenuTitle':'',
    'OpenMenuLabel01':'',
    'OpenMenuLabel02':'',
    'OpenMenuLabel03':'',
    'OpenMenuLabel04':'',
    'OpenMenuLabel05':'',
    'OpenMenuLabel06':'',
    'OpenMenuLabel07':'',
    'OpenMenuLabel08':'',
    'OpenMenuLabel09':'',

    'BookmarksMenuName':'',

    'WarningWinTitle':'',
    'WarningWinLabel01':'',
    'WarningWinLabel02':'',
    'WarningWinLabel03':'',
    'WarningWinLabel04':'',
    'WarningWinLabel05':'',
    'WarningWinLabel06':'',
    'WarningWinLabel07':'',
    'WarningWinLabel08':'',
    'WarningWinLabel09':'',
    'WarningWinLabel10':'',

    'SaveMenuTitle':'',
    'SaveMenuLabel01':'',
    'SaveMenuName':'',
    'SaveMenuCreator':'',
    'SaveMenuCreatorValue':'',
    'SaveMenuCategoryDefault':'',
    'SaveMenuDescriptionLabel':'',
    'SaveMenuDescription':'',
    'SaveMenuWebLinkLabel':'',
    'SaveMenuWebLink':'',
    'SaveMenuEmail':'',
    'SaveMenuEmailLabel':'',
    'SaveMenuWarning01':'',
    'SaveMenuWarning02':'',
    'SaveMenuWarning03':'',
    'SaveMenuWarning04':'',
    'SaveMenuWarning05':'',

    'SaveCategoryTitle':'',
    'SaveCategoryCategoryTitle':'',
    'SaveCategoryCarPaint':'',
    'SaveCategoryDirt':'',
    'SaveCategoryFabricClothes':'',
    'SaveCategoryFancy':'',
    'SaveCategoryFibreFur':'',
    'SaveCategoryGlass':'',
    'SaveCategoryHalo':'',
    'SaveCategoryLiquids':'',
    'SaveCategoryMetal':'',
    'SaveCategoryMisc':'',
    'SaveCategoryNature':'',
    'SaveCategoryOrganic':'',
    'SaveCategoryPersonal':'',
    'SaveCategoryPlastic':'',
    'SaveCategorySky':'',
    'SaveCategorySpace':'',
    'SaveCategoryStone':'',
    'SaveCategoryToon':'',
    'SaveCategoryWall':'',
    'SaveCategoryWater':'',
    'SaveCategoryWood':'',

    'ConfigurationMenuTitle':'',
    'ConfigurationMenuLabel01':'',
    'ConfigurationMenuExportPath':'',
    'ConfigurationMenuLabel02':'',
    'ConfigurationMenuLabel03':'',
    'ConfigurationMenuResolutionPreviewX':'',
    'ConfigurationMenuResolutionPreviewY':'',
    'ConfigurationMenuDataBasePath':'',
    'ConfigurationMenuWarning01':'',
    'ConfigurationMenuWarning02':'',
    'ConfigurationMenuWarning03':'',
    'ConfigurationMenuWarning04':'',
    'ConfigurationMenuWarning05':'',

    'ExportMenuTitle':'',
    'ExportMenuLabel01':'',
    'ExportMenuName':'',
    'ExportMenuCreator':'',
    'ExportMenuCreatorDefault':'',
    'ExportMenuTakePreview':'',


    'ImportMenuTitle':'',

    'FindImageMenuName':'',

    'InformationsMenuTitle':'',
    'InformationsMenuLabelName':'',
    'InformationsMenuName':'',
    'InformationsMenuLabelCreator':'',
    'InformationsMenuCreator':'',
    'InformationsMenuLabelCategory':'',
    'InformationsMenuCategory':'',
    'InformationsMenuLabelDescription':'',
    'InformationsMenuDescription':'',
    'InformationsMenuLabelWebLink':'',
    'InformationsMenuWebLink':'',
    'InformationsMenuLabelEmail':'',
    'InformationsMenuEmail':'',

    'HelpMenuTitle':'',
    'HelpMenuLabel01':'',
    'HelpMenuLabel02':'',
    'HelpMenuLabel03':'',
    'HelpMenuLabel04':'',
    'HelpMenuLabel05':'',
    'HelpMenuLabel06':'',
    'HelpMenuLabel07':'',
    'HelpMenuLabel08':'',
    'HelpMenuLabel09':'',
    'HelpMenuLabel10':'',
    'HelpMenuLabel11':'',
    'HelpMenuLabel12':'',
    'HelpMenuLabel13':'',
    'HelpMenuLabel14':'',
    'HelpMenuLabel15':'',
    'HelpMenuLabel16':'',
    'HelpMenuLabel17':'',
    'HelpMenuLabel18':'',
    'HelpMenuLabel19':'',
    'HelpMenuLabel20':'',
    'HelpMenuLabel21':'',
    'HelpMenuLabel22':'',
    'HelpMenuLabel23':'',
    'HelpMenuLabel24':'',
    'HelpMenuLabel25':'',
    'HelpMenuLabel26':'',
    'HelpMenuLabel27':'',
    'HelpMenuLabel28':'',
    'HelpMenuLabel29':'',
    'HelpMenuLabel30':'',
    'HelpMenuLabel31':'',
    'HelpMenuLabel32':'',
    'HelpMenuLabel33':'',
    'HelpMenuLabel34':'',
    'HelpMenuLabel35':'',
    'HelpMenuLabel36':'',
    'HelpMenuLabel37':'',
    'HelpMenuLabel38':'',
    'HelpMenuLabel39':'',
    'HelpMenuLabel40':'',

    'ErrorsMenuError001':'',
    'ErrorsMenuError002':'',
    'ErrorsMenuError003':'',
    'ErrorsMenuError004':'',
    'ErrorsMenuError005':'',
    'ErrorsMenuError006':'',
    'ErrorsMenuError007':'',
    'ErrorsMenuError008':'',
    'ErrorsMenuError009':'',
    'ErrorsMenuError010':'',
    'ErrorsMenuError011':'',
    'ErrorsMenuError012':'',
    'ErrorsMenuError013':'',
    'ErrorsMenuError014':'',
    'ErrorsMenuError015':'',
    'ErrorsMenuError016':'',
    'ErrorsMenuError017':'',
    'ErrorsMenuError018':'',
    'ErrorsMenuError019':'',
    'ErrorsMenuError020':''
    }

for value in locale.getdefaultlocale():
    if c == 0:
        langage = value

    c = c +1


if os.path.exists(os.path.join(AppPath, "lang", langage)) :
    LangageValuesDict = LangageValues(langage, LangageValuesDict)

else:
    LangageValuesDict = LangageValues('en_US', LangageValuesDict)




# ************************************************************************************
# *                                    IMPORTER SQL                                  *
# ************************************************************************************
def ImporterSQL(Mat_Name):

    print()
    print("                                        *****                         ")
    print()
    print("*******************************************************************************")
    print("*                                IMPORT BASE MATERIAL                         *")
    print("*******************************************************************************")



    SearchName = Mat_Name

    #My default values:
    MY_IMPORT_INFORMATIONS = []

    Mat_Index = ""
    Mat_Name = ""
    Mat_Type = ""
    Mat_Preview_render_type = ""
    Mat_diffuse_color_r = ""
    Mat_diffuse_color_g = ""
    Mat_diffuse_color_b = ""
    Mat_diffuse_color_a = ""
    Mat_diffuse_shader = ""
    Mat_diffuse_intensity = ""
    Mat_use_diffuse_ramp = ""
    Mat_diffuse_roughness = ""
    Mat_diffuse_toon_size = ""
    Mat_diffuse_toon_smooth = ""
    Mat_diffuse_darkness = ""
    Mat_diffuse_fresnel = ""
    Mat_diffuse_fresnel_factor = ""
    Mat_specular_color_r = ""
    Mat_specular_color_g = ""
    Mat_specular_color_b = ""
    Mat_specular_color_a = ""
    Mat_specular_shader = ""
    Mat_specular_intensity = ""
    Mat_specular_ramp = ""
    Mat_specular_hardness = ""
    Mat_specular_ior = ""
    Mat_specular_toon_size = ""
    Mat_specular_toon_smooth = ""
    Mat_shading_emit = ""
    Mat_shading_ambient = ""
    Mat_shading_translucency = ""
    Mat_shading_use_shadeless = ""
    Mat_shading_use_tangent_shading = ""
    Mat_shading_use_cubic = ""
    Mat_transparency_use_transparency = ""
    Mat_transparency_method = ""
    Mat_transparency_alpha = ""
    Mat_transparency_fresnel = ""
    Mat_transparency_specular_alpha = ""
    Mat_transparency_fresnel_factor = ""
    Mat_transparency_ior = ""
    Mat_transparency_filter = ""
    Mat_transparency_falloff = ""
    Mat_transparency_depth_max = ""
    Mat_transparency_depth = ""
    Mat_transparency_gloss_factor = ""
    Mat_transparency_gloss_threshold = ""
    Mat_transparency_gloss_samples = ""
    Mat_raytracemirror_use = ""
    Mat_raytracemirror_reflect_factor = ""
    Mat_raytracemirror_fresnel = ""
    Mat_raytracemirror_color_r = ""
    Mat_raytracemirror_color_g = ""
    Mat_raytracemirror_color_b = ""
    Mat_raytracemirror_color_a = ""
    Mat_raytracemirror_fresnel_factor = ""
    Mat_raytracemirror_depth = ""
    Mat_raytracemirror_distance = ""
    Mat_raytracemirror_fade_to = ""
    Mat_raytracemirror_gloss_factor = ""
    Mat_raytracemirror_gloss_threshold = ""
    Mat_raytracemirror_gloss_samples = ""
    Mat_raytracemirror_gloss_anisotropic = ""
    Mat_subsurfacescattering_use = ""
    Mat_subsurfacescattering_presets = ""
    Mat_subsurfacescattering_ior = ""
    Mat_subsurfacescattering_scale = ""
    Mat_subsurfacescattering_color_r = ""
    Mat_subsurfacescattering_color_g = ""
    Mat_subsurfacescattering_color_b = ""
    Mat_subsurfacescattering_color_a = ""
    Mat_subsurfacescattering_color_factor = ""
    Mat_subsurfacescattering_texture_factor = ""
    Mat_subsurfacescattering_radius_one  = ""
    Mat_subsurfacescattering_radius_two  = ""
    Mat_subsurfacescattering_radius_three = ""
    Mat_subsurfacescattering_front  = ""
    Mat_subsurfacescattering_back  = ""
    Mat_subsurfacescattering_error_threshold = ""
    Mat_strand_root_size = ""
    Mat_strand_tip_size = ""
    Mat_strand_size_min = ""
    Mat_strand_blender_units = ""
    Mat_strand_use_tangent_shading = ""
    Mat_strand_shape = ""
    Mat_strand_width_fade = ""
    Mat_strand_blend_distance = ""
    Mat_options_use_raytrace = ""
    Mat_options_use_full_oversampling = ""
    Mat_options_use_sky = ""
    Mat_options_use_mist = ""
    Mat_options_invert_z = ""
    Mat_options_offset_z = ""
    Mat_options_use_face_texture = ""
    Mat_options_use_texture_alpha = ""
    Mat_options_use_vertex_color_paint = ""
    Mat_options_use_vertex_color_light = ""
    Mat_options_use_object_color = ""
    Mat_options_pass_index = ""
    Mat_shadow_use_shadows = ""
    Mat_shadow_use_transparent_shadows = ""
    Mat_shadow_use_cast_shadows_only = ""
    Mat_shadow_shadow_cast_alpha = ""
    Mat_shadow_use_only_shadow = ""
    Mat_shadow_shadow_only_type = ""
    Mat_shadow_use_cast_buffer_shadows = ""
    Mat_shadow_shadow_buffer_bias = ""
    Mat_shadow_use_ray_shadow_bias = ""
    Mat_shadow_shadow_ray_bias = ""
    Mat_shadow_use_cast_approximate = ""
    Idx_ramp_diffuse = ""
    Idx_ramp_specular = ""
    Idx_textures = ""

    Ima_Index = ""
    Idx_Texture = ""
    Tex_ima_name = ""
    Tex_ima_source = ""
    Tex_ima_filepath = ""
    Tex_ima_fileformat = ""
    Tex_ima_fields = ""
    Tex_ima_premultiply = ""
    Tex_ima_field_order = ""
    Tex_ima_generated_type = ""
    Tex_ima_generated_width = ""
    Tex_ima_generated_height = ""
    Tex_ima_float_buffer = ""
    Tex_ima_blob = ""

    Tex_Index = ""
    Tex_Name = ""
    Tex_Type = ""
    Tex_Preview_type = ""
    Tex_use_preview_alpha  = ""
    Tex_type_blend_progression = ""
    Tex_type_blend_use_flip_axis = ""
    Tex_type_clouds_cloud_type = ""
    Tex_type_clouds_noise_type = ""
    Tex_type_clouds_noise_basis = ""
    Tex_type_noise_distortion = ""
    Tex_type_env_map_source = ""
    Tex_type_env_map_mapping = ""
    Tex_type_env_map_clip_start = ""
    Tex_type_env_map_clip_end = ""
    Tex_type_env_map_resolution = ""
    Tex_type_env_map_depth = ""
    Tex_type_env_map_image_file = ""
    Tex_type_env_map_zoom  = ""
    Tex_type_magic_depth = ""
    Tex_type_magic_turbulence = ""
    Tex_type_marble_marble_type = ""
    Tex_type_marble_noise_basis_2 = ""
    Tex_type_marble_noise_type = ""
    Tex_type_marble_noise_basis = ""
    Tex_type_marble_noise_scale = ""
    Tex_type_marble_noise_depth = ""
    Tex_type_marble_turbulence = ""
    Tex_type_marble_nabla = ""
    Tex_type_musgrave_type = ""
    Tex_type_musgrave_dimension_max = ""
    Tex_type_musgrave_lacunarity = ""
    Tex_type_musgrave_octaves = ""
    Tex_type_musgrave_noise_intensity = ""
    Tex_type_musgrave_noise_basis = ""
    Tex_type_musgrave_noise_scale = ""
    Tex_type_musgrave_nabla = ""
    Tex_type_musgrave_offset = ""
    Tex_type_musgrave_gain = ""
    Tex_type_clouds_noise_scale = ""
    Tex_type_clouds_nabla = ""
    Tex_type_clouds_noise_depth = ""
    Tex_type_noise_distortion_distortion = ""
    Tex_type_noise_distortion_texture_distortion = ""
    Tex_type_noise_distortion_nabla = ""
    Tex_type_noise_distortion_noise_scale = ""
    Tex_type_point_density_point_source = ""
    Tex_type_point_density_radius = ""
    Tex_type_point_density_particule_cache_space = ""
    Tex_type_point_density_falloff = ""
    Tex_type_point_density_use_falloff_curve = ""
    Tex_type_point_density_falloff_soft = ""
    Tex_type_point_density_falloff_speed_scale = ""
    Tex_type_point_density_speed_scale = ""
    Tex_type_point_density_color_source = ""
    Tex_type_stucci_type = ""
    Tex_type_stucci_noise_type = ""
    Tex_type_stucci_basis = ""
    Tex_type_stucci_noise_scale = ""
    Tex_type_stucci_turbulence = ""
    Tex_type_voronoi_distance_metric = ""
    Tex_type_voronoi_minkovsky_exponent = ""
    Tex_type_voronoi_color_mode = ""
    Tex_type_voronoi_noise_scale = ""
    Tex_type_voronoi_nabla = ""
    Tex_type_voronoi_weight_1 = ""
    Tex_type_voronoi_weight_2 = ""
    Tex_type_voronoi_weight_3 = ""
    Tex_type_voronoi_weight_4 = ""
    Tex_type_voxel_data_file_format = ""
    Tex_type_voxel_data_source_path = ""
    Tex_type_voxel_data_use_still_frame = ""
    Tex_type_voxel_data_still_frame = ""
    Tex_type_voxel_data_interpolation  = ""
    Tex_type_voxel_data_extension = ""
    Tex_type_voxel_data_intensity  = ""
    Tex_type_voxel_data_resolution_1 = ""
    Tex_type_voxel_data_resolution_2 = ""
    Tex_type_voxel_data_resoltion_3 = ""
    Tex_type_voxel_data_smoke_data_type = ""
    Tex_type_wood_noise_basis_2 = ""
    Tex_type_wood_wood_type = ""
    Tex_type_wood_noise_type = ""
    Tex_type_wood_basis = ""
    Tex_type_wood_noise_scale = ""
    Tex_type_wood_nabla = ""
    Tex_type_wood_turbulence = ""
    Tex_influence_use_map_diffuse = ""
    Tex_influence_use_map_color_diffuse = ""
    Tex_influence_use_map_alpha = ""
    Tex_influence_use_map_translucency = ""
    Tex_influence_use_map_specular = ""
    Tex_influence_use_map_color_spec = ""
    Tex_influence_use_map_map_hardness = ""
    Tex_influence_use_map_ambient = ""
    Tex_influence_use_map_emit = ""
    Tex_influence_use_map_mirror = ""
    Tex_influence_use_map_raymir = ""
    Tex_influence_use_map_normal = ""
    Tex_influence_use_map_warp = ""
    Tex_influence_use_map_displacement = ""
    Tex_influence_use_map_rgb_to_intensity = ""
    Tex_influence_map_invert  = ""
    Tex_influence_use_stencil = ""
    Tex_influence_diffuse_factor = ""
    Tex_influence_color_factor = ""
    Tex_influence_alpha_factor = ""
    Tex_influence_translucency_factor  = ""
    Tex_influence_specular_factor = ""
    Tex_influence_specular_color_factor = ""
    Tex_influence_hardness_factor = ""
    Tex_influence_ambiant_factor = ""
    Tex_influence_emit_factor = ""
    Tex_influence_mirror_factor = ""
    Tex_influence_raymir_factor = ""
    Tex_influence_normal_factor = ""
    Tex_influence_warp_factor = ""
    Tex_influence_displacement_factor = ""
    Tex_influence_default_value = ""
    Tex_influence_blend_type = ""
    Tex_influence_color_r = ""
    Tex_influence_color_g = ""
    Tex_influence_color_b = ""
    Tex_influence_color_a = ""
    Tex_influence_bump_method = ""
    Tex_influence_objectspace = ""
    Tex_mapping_texture_coords = ""
    Tex_mapping_mapping = ""
    Tex_mapping_use_from_dupli = ""
    Tex_mapping_mapping_x  = ""
    Tex_mapping_mapping_y = ""
    Tex_mapping_mapping_z = ""
    Tex_mapping_offset_x = ""
    Tex_mapping_offset_y = ""
    Tex_mapping_offset_z = ""
    Tex_mapping_scale_x = ""
    Tex_mapping_scale_y  = ""
    Tex_mapping_scale_z = ""
    Tex_colors_use_color_ramp = ""
    Tex_colors_factor_r = ""
    Tex_colors_factor_g = ""
    Tex_colors_factor_b = ""
    Tex_colors_intensity = ""
    Tex_colors_contrast = ""
    Tex_colors_saturation = ""
    Mat_Idx = ""
    Poi_Idx = ""
    Col_Idx = ""
    Tex_type_voronoi_intensity = ""
    Tex_mapping_use_from_original = ""
    Tex_type_noise_distortion_noise_distortion = ""
    Tex_type_noise_distortion_basis = ""

    Col_Index = ""
    Col_Num_Material = ""
    Col_Num_Texture = ""
    Col_Flip = ""
    Col_Active_color_stop = ""
    Col_Between_color_stop = ""
    Col_Interpolation = ""
    Col_Position = ""
    Col_Color_stop_one_r = ""
    Col_Color_stop_one_g = ""
    Col_Color_stop_one_b = ""
    Col_Color_stop_one_a = ""
    Col_Color_stop_two_r = ""
    Col_Color_stop_two_g = ""
    Col_Color_stop_two_b = ""
    Col_Color_stop_two_a = ""

    Poi_Index = ""
    Poi_Num_Material = ""
    Poi_Num_Texture = ""
    Poi_Flip = ""
    Poi_Active_color_stop = ""
    Poi_Between_color_stop = ""
    Poi_Interpolation = ""
    Poi_Position = ""
    Poi_Color_stop_one_r = ""
    Poi_Color_stop_one_g = ""
    Poi_Color_stop_one_b = ""
    Poi_Color_stop_one_a = ""
    Poi_Color_stop_two_r = ""
    Poi_Color_stop_two_g = ""
    Poi_Color_stop_two_b = ""
    Poi_Color_stop_two_a = ""

    Dif_Index = ""
    Dif_Num_Material = ""
    Dif_Flip = ""
    Dif_Active_color_stop = ""
    Dif_Between_color_stop = ""
    Dif_Interpolation = ""
    Dif_Position = ""
    Dif_Color_stop_one_r = ""
    Dif_Color_stop_one_g = ""
    Dif_Color_stop_one_b = ""
    Dif_Color_stop_one_a = ""
    Dif_Color_stop_two_r = ""
    Dif_Color_stop_two_g = ""
    Dif_Color_stop_two_b = ""
    Dif_Color_stop_two_a = ""
    Dif_Ramp_input = ""
    Dif_Ramp_blend = ""
    Dif_Ramp_factor = ""

    Spe_Index = ""
    Spe_Num_Material = ""
    Spe_Flip = ""
    Spe_Active_color_stop = ""
    Spe_Between_color_stop = ""
    Spe_Interpolation = ""
    Spe_Position = ""
    Spe_Color_stop_one_r = ""
    Spe_Color_stop_one_g = ""
    Spe_Color_stop_one_b = ""
    Spe_Color_stop_one_a = ""
    Spe_Color_stop_two_r = ""
    Spe_Color_stop_two_g = ""
    Spe_Color_stop_two_b = ""
    Spe_Color_stop_two_a = ""
    Spe_Ramp_input = ""
    Spe_Ramp_blend = ""
    Spe_Ramp_factor = ""




    #************************************************************************************************************
    MyMaterialIndex = 2 #First valid value in the Base.
    MyTextureIndex = 2 #First valid value in the Base.
    MyMaterialRequest = ""
    MyColorRamplRequest = ""
    MyDiffuseRampRequest = ""
    MySpecularRampRequest = ""
    MyPointDensityRampRequest = ""
    MyImageUvRequest = ""
    MyTextureRequest = ""



    #I split material name and i return material index

    for value in SearchName.split('_Ind_', 255):
        if '.jpg' in value:
            MyMaterialIndex = value.replace('.jpg', '')


    #I must communicate with SQLite base and create lists :
    #Here i connect database :
    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
    Connexion = ShadersToolsDatabase.cursor()

    #My material:
    MyMaterialRequest = "SELECT * FROM MATERIALS WHERE Mat_Index=" + str(MyMaterialIndex)
    Connexion.execute(MyMaterialRequest)
    ShadersToolsDatabase.commit()
    MyMaterialResult = Connexion.fetchall()

    v = 0
    for values in MyMaterialResult:
      for val in values:

        #Debug
        if val == 'False':
            val = False

        if val == 'True':
            val = True


        #Affect values:
        if v == 0:
            Mat_Index = val

        if v == 1:
            Mat_Name = val

        if v == 2:
            Mat_Type = val

        if v == 3:
            Mat_Preview_render_type = val

        if v == 4:
            Mat_diffuse_color_r = val

        if v == 5:
            Mat_diffuse_color_g = val

        if v == 6:
            Mat_diffuse_color_b = val

        if v == 7:
            Mat_diffuse_color_a = val

        if v == 8:
            Mat_diffuse_shader = val

        if v == 9:
            Mat_diffuse_intensity = val

        if v == 10:

            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_use_diffuse_ramp = val

        if v == 11:
            Mat_diffuse_roughness = val

        if v == 12:
            Mat_diffuse_toon_size = val

        if v == 13:
            Mat_diffuse_toon_smooth = val

        if v == 14:
            Mat_diffuse_darkness = val

        if v == 15:
            Mat_diffuse_fresnel = val

        if v == 16:
            Mat_diffuse_fresnel_factor = val

        if v == 17:
            Mat_specular_color_r = val

        if v == 18:
            Mat_specular_color_g = val

        if v == 19:
            Mat_specular_color_b = val

        if v == 20:
            Mat_specular_color_a = val

        if v == 21:
            Mat_specular_shader = val

        if v == 22:
            Mat_specular_intensity = val

        if v == 23:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_specular_ramp = val

        if v == 24:
            Mat_specular_hardness = val

        if v == 25:
            Mat_specular_ior = val

        if v == 26:
            Mat_specular_toon_size = val

        if v == 27:
            Mat_specular_toon_smooth = val

        if v == 28:
            Mat_shading_emit = val

        if v == 29:
            Mat_shading_ambient = val

        if v == 30:
            Mat_shading_translucency = val

        if v == 31:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shading_use_shadeless = val

        if v == 32:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shading_use_tangent_shading = val

        if v == 33:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shading_use_cubic = val

        if v == 34:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_transparency_use_transparency = val

        if v == 35:
            Mat_transparency_method = val

        if v == 36:
            Mat_transparency_alpha = val

        if v == 37:
            Mat_transparency_fresnel = val

        if v == 38:
            Mat_transparency_specular_alpha = val

        if v == 39:
            Mat_transparency_fresnel_factor = val

        if v == 40:
            Mat_transparency_ior = val

        if v == 41:
            Mat_transparency_filter = val

        if v == 42:
            Mat_transparency_falloff = val

        if v == 43:
            Mat_transparency_depth_max = val

        if v == 44:
            Mat_transparency_depth = val

        if v == 45:
            Mat_transparency_gloss_factor = val

        if v == 46:
            Mat_transparency_gloss_threshold = val

        if v == 47:
            Mat_transparency_gloss_samples = val

        if v == 48:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_raytracemirror_use = val

        if v == 49:
            Mat_raytracemirror_reflect_factor = val

        if v == 50:
            Mat_raytracemirror_fresnel = val

        if v == 51:
            Mat_raytracemirror_color_r = val

        if v == 52:
            Mat_raytracemirror_color_g = val

        if v == 53:
            Mat_raytracemirror_color_b = val

        if v == 54:
            Mat_raytracemirror_color_a = val

        if v == 55:
            Mat_raytracemirror_fresnel_factor = val

        if v == 56:
            Mat_raytracemirror_depth = val

        if v == 57:
            Mat_raytracemirror_distance = val

        if v == 58:
            Mat_raytracemirror_fade_to = val

        if v == 59:
            Mat_raytracemirror_gloss_factor = val

        if v == 60:
            Mat_raytracemirror_gloss_threshold = val

        if v == 61:
            Mat_raytracemirror_gloss_samples = val

        if v == 62:
            Mat_raytracemirror_gloss_anisotropic = val

        if v == 63:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_subsurfacescattering_use = val

        if v == 64:
            Mat_subsurfacescattering_presets = val

        if v == 65:
            Mat_subsurfacescattering_ior = val

        if v == 66:
            Mat_subsurfacescattering_scale = val

        if v == 67:
            Mat_subsurfacescattering_color_r = val

        if v == 68:
            Mat_subsurfacescattering_color_g = val

        if v == 69:
            Mat_subsurfacescattering_color_b = val

        if v == 70:
            Mat_subsurfacescattering_color_a = val

        if v == 71:
            Mat_subsurfacescattering_color_factor = val

        if v == 72:
            Mat_subsurfacescattering_texture_factor = val

        if v == 73:
            Mat_subsurfacescattering_radius_one  = val

        if v == 74:
            Mat_subsurfacescattering_radius_two  = val

        if v == 75:
            Mat_subsurfacescattering_radius_three = val

        if v == 76:
            Mat_subsurfacescattering_front  = val

        if v == 77:
            Mat_subsurfacescattering_back  = val

        if v == 78:
            Mat_subsurfacescattering_error_threshold = val

        if v == 79:
            Mat_strand_root_size = val

        if v == 80:
            Mat_strand_tip_size = val

        if v == 81:
            Mat_strand_size_min = val

        if v == 82:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_strand_blender_units = val

        if v == 83:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_strand_use_tangent_shading = val

        if v == 84:
            Mat_strand_shape = val

        if v == 85:
            Mat_strand_width_fade = val

        if v == 86:
            Mat_strand_blend_distance = val

        if v == 87:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_raytrace = val

        if v == 88:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_full_oversampling = val

        if v == 89:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_sky = val

        if v == 90:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_mist = val

        if v == 91:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_invert_z = val

        if v == 92:
            Mat_options_offset_z = val

        if v == 93:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_face_texture = val

        if v == 94:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_texture_alpha = val

        if v == 95:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_vertex_color_paint = val

        if v == 96:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_vertex_color_light = val

        if v == 97:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_options_use_object_color = val

        if v == 98:
            Mat_options_pass_index = val

        if v == 99:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shadow_use_shadows = val

        if v == 100:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shadow_use_transparent_shadows = val

        if v == 101:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shadow_use_cast_shadows_only = val

        if v == 102:
            Mat_shadow_shadow_cast_alpha = val

        if v == 103:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shadow_use_only_shadow = val

        if v == 104:
            Mat_shadow_shadow_only_type = val

        if v == 105:
            #I convert SQlite Boolean to Blender Boolean:
            if val == 1:
                val = True

            else:
                val = False

            Mat_shadow_use_cast_buffer_shadows = val

        if v == 106:
            Mat_shadow_shadow_buffer_bias = val

        if v == 107:
            Mat_shadow_use_ray_shadow_bias = val

        if v == 108:
            Mat_shadow_shadow_ray_bias = val

        if v == 109:
            Mat_shadow_use_cast_approximate = val

        if v == 110:
            Idx_ramp_diffuse = val

        if v == 111:
            Idx_ramp_specular = val

        if v == 112:
            Idx_textures = val


        v = v + 1

    #Here I restore imported values in Blender:
    obj = bpy.context.object
    tex = bpy.context.active_object.active_material

    # Create Material :
    def CreateMaterial(Mat_Name):

        # Materials Values :
        mat = bpy.data.materials.new(Mat_Name)
        mat.diffuse_color[0] = Mat_diffuse_color_r
        mat.diffuse_color[1] = Mat_diffuse_color_g
        mat.diffuse_color[2] = Mat_diffuse_color_b
        mat.diffuse_shader = Mat_diffuse_shader
        mat.diffuse_intensity = Mat_diffuse_intensity
        mat.roughness = Mat_diffuse_roughness
        mat.diffuse_toon_size = Mat_diffuse_toon_size
        mat.diffuse_toon_smooth = Mat_diffuse_toon_smooth
        mat.darkness  = Mat_diffuse_darkness
        mat.diffuse_fresnel = Mat_diffuse_fresnel
        mat.diffuse_fresnel_factor  = Mat_diffuse_fresnel_factor
        mat.specular_shader  = Mat_specular_shader
        mat.specular_color[0] = Mat_specular_color_r
        mat.specular_color[1] = Mat_specular_color_g
        mat.specular_color[2] = Mat_specular_color_b
        mat.specular_intensity = Mat_specular_intensity
        mat.specular_hardness = Mat_specular_hardness
        mat.specular_ior = Mat_specular_ior
        mat.specular_toon_size = Mat_specular_toon_size
        mat.specular_toon_smooth = Mat_specular_toon_smooth
        mat.emit = Mat_shading_emit
        mat.ambient  = Mat_shading_ambient
        mat.translucency = Mat_shading_translucency
        mat.use_shadeless = Mat_shading_use_shadeless
        mat.use_tangent_shading = Mat_shading_use_tangent_shading
        mat.use_transparency = Mat_transparency_use_transparency
        mat.transparency_method = Mat_transparency_method
        mat.alpha = Mat_transparency_alpha
        mat.raytrace_transparency.fresnel = Mat_transparency_fresnel
        mat.specular_alpha = Mat_transparency_specular_alpha
        mat.raytrace_transparency.fresnel_factor = Mat_transparency_fresnel_factor
        mat.raytrace_transparency.ior = Mat_transparency_ior
        mat.raytrace_transparency.filter = Mat_transparency_filter
        mat.raytrace_transparency.falloff = Mat_transparency_falloff
        mat.raytrace_transparency.depth_max = Mat_transparency_depth_max
        mat.raytrace_transparency.depth = Mat_transparency_depth
        mat.raytrace_transparency.gloss_factor = Mat_transparency_gloss_factor
        mat.raytrace_transparency.gloss_threshold = Mat_transparency_gloss_threshold
        mat.raytrace_transparency.gloss_samples = Mat_transparency_gloss_samples
        mat.raytrace_mirror.use = Mat_raytracemirror_use
        mat.raytrace_mirror.reflect_factor = Mat_raytracemirror_reflect_factor
        mat.raytrace_mirror.fresnel = Mat_raytracemirror_fresnel
        mat.mirror_color[0] = Mat_raytracemirror_color_r
        mat.mirror_color[1] = Mat_raytracemirror_color_g
        mat.mirror_color[2] = Mat_raytracemirror_color_b
        mat.raytrace_mirror.fresnel_factor = Mat_raytracemirror_fresnel_factor
        mat.raytrace_mirror.depth = Mat_raytracemirror_depth
        mat.raytrace_mirror.distance = Mat_raytracemirror_distance
        mat.raytrace_mirror.fade_to = Mat_raytracemirror_fade_to
        mat.raytrace_mirror.gloss_factor = Mat_raytracemirror_gloss_factor
        mat.raytrace_mirror.gloss_threshold = Mat_raytracemirror_gloss_threshold
        mat.raytrace_mirror.gloss_samples = Mat_raytracemirror_gloss_samples
        mat.raytrace_mirror.gloss_anisotropic = Mat_raytracemirror_gloss_anisotropic
        mat.subsurface_scattering.use  = Mat_subsurfacescattering_use
        mat.subsurface_scattering.ior = Mat_subsurfacescattering_ior
        mat.subsurface_scattering.scale = Mat_subsurfacescattering_scale
        mat.subsurface_scattering.color[0] = Mat_subsurfacescattering_color_r
        mat.subsurface_scattering.color[1] = Mat_subsurfacescattering_color_g
        mat.subsurface_scattering.color[2] = Mat_subsurfacescattering_color_b
        mat.subsurface_scattering.color_factor = Mat_subsurfacescattering_color_factor
        mat.subsurface_scattering.texture_factor = Mat_subsurfacescattering_texture_factor
        mat.subsurface_scattering.radius[0] = Mat_subsurfacescattering_radius_one
        mat.subsurface_scattering.radius[1] = Mat_subsurfacescattering_radius_two
        mat.subsurface_scattering.radius[2] = Mat_subsurfacescattering_radius_three
        mat.subsurface_scattering.front = Mat_subsurfacescattering_front
        mat.subsurface_scattering.back = Mat_subsurfacescattering_back
        mat.subsurface_scattering.error_threshold = Mat_subsurfacescattering_error_threshold
        mat.strand.root_size = Mat_strand_root_size
        mat.strand.tip_size = Mat_strand_tip_size
        mat.strand.size_min = Mat_strand_size_min
        mat.strand.use_blender_units = Mat_strand_blender_units
        mat.strand.use_tangent_shading = Mat_strand_use_tangent_shading
        mat.strand.shape = Mat_strand_shape
        mat.strand.width_fade = Mat_strand_width_fade
        mat.strand.blend_distance = Mat_strand_blend_distance
        mat.use_raytrace = Mat_options_use_raytrace
        mat.use_full_oversampling = Mat_options_use_full_oversampling
        mat.use_sky = Mat_options_use_sky
        mat.use_mist = Mat_options_use_mist
        mat.invert_z = Mat_options_invert_z
        mat.offset_z = Mat_options_offset_z
        mat.use_face_texture = Mat_options_use_face_texture
        mat.use_face_texture_alpha = Mat_options_use_texture_alpha
        mat.use_vertex_color_paint = Mat_options_use_vertex_color_paint
        mat.use_vertex_color_light = Mat_options_use_vertex_color_light
        mat.use_object_color = Mat_options_use_object_color
        mat.pass_index = Mat_options_pass_index
        mat.use_shadows = Mat_shadow_use_shadows
        mat.use_transparent_shadows = Mat_shadow_use_transparent_shadows
        mat.use_cast_shadows_only = Mat_shadow_use_cast_shadows_only
        mat.shadow_cast_alpha = Mat_shadow_shadow_cast_alpha
        mat.use_only_shadow = Mat_shadow_use_only_shadow
        mat.shadow_only_type = Mat_shadow_shadow_only_type
        mat.use_cast_buffer_shadows = Mat_shadow_use_cast_buffer_shadows
        mat.shadow_buffer_bias = Mat_shadow_shadow_buffer_bias
        mat.use_ray_shadow_bias = Mat_shadow_use_ray_shadow_bias
        mat.shadow_ray_bias = Mat_shadow_shadow_ray_bias
        mat.use_cast_approximate = Mat_shadow_use_cast_approximate

        return mat

    bpy.ops.object.material_slot_add()
    obj.material_slots[obj.material_slots.__len__() - 1].material = CreateMaterial(Mat_Name)



    #My texture:
    MyTextureRequest = "SELECT * FROM TEXTURES WHERE Mat_Idx=" + str(MyMaterialIndex)
    Connexion = ShadersToolsDatabase.cursor()
    Connexion.execute(MyTextureRequest)
    ShadersToolsDatabase.commit()
    MyTextureResult = Connexion.fetchall()

    #I must extract IMAGES/UV before create Textures:
    MyTextureIdxRequest = "SELECT Tex_Index FROM TEXTURES WHERE Mat_Idx=" + str(MyMaterialIndex)
    Connexion = ShadersToolsDatabase.cursor()
    Connexion.execute(MyTextureIdxRequest)
    ShadersToolsDatabase.commit()
    MyTextureIdxResult = Connexion.fetchall()
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


    for values in MyTextureIdxResult:
        #I must find all textures in database:
        for val in values:
            if val != '' or val == None:
                MyImageUvRequest = "SELECT * FROM IMAGE_UV WHERE Idx_Texture=" + str(val)
                Connexion = ShadersToolsDatabase.cursor()
                Connexion.execute(MyImageUvRequest)
                ShadersToolsDatabase.commit()
                MyImageUvRequest = Connexion.fetchall()

                #I return values:
                c = 0
                for val2 in MyImageUvRequest:
                  for values2 in val2:

                    #Debug
                    if values2 == 'False':
                        values2 = False

                    if values2 == 'True':
                        values2 = True

                    if c == 2:
                        Tex_ima_name = values2

                    if c == 4:
                        Tex_ima_filepath = values2

                    if c == 5:
                        Tex_ima_fileformat = values2

                    if c == 6:
                        Tex_ima_fields = values2

                    if c == 7:
                        Tex_ima_premultiply = values2

                    if c == 8:
                        Tex_ima_field_order = values2


                    if c == 13:
                        Render = values2
                        Render_exists = True

                        #Now I generate image files:
                        if Tex_ima_name == '':
                            adresse = os.path.join(OutPath, "error_save.jpg")
                            test = shutil.copy2(os.path.join(ErrorsPath, "error_save.jpg"), adresse)
                            Tex_ima_filepath = os.path.join(AppPath, "error_save.jpg")

                        else:
                            format_image = [".png", ".jpg", ".jpeg", ".tiff", ".tga", ".raw", ".bmp", ".hdr", ".gif", ".svg", ".wmf", ".pst"]
                            c = 0
                            for format in format_image:
                                if c == 0:
                                    if format in Tex_ima_name:
                                        adresse = os.path.join(OutPath, Tex_ima_name)
                                        c = 1

                                    else:
                                        adresse = os.path.join(OutPath, Tex_ima_name + "." +  Tex_ima_fileformat)


                            generated_image = open(adresse,'wb')
                            generated_image.write(Render)
                            generated_image.close()


                    c = c + 1


    #I copy all images files in ShaderToolsImport folder:
    print("*******************************************************")
    print(LangageValuesDict['ErrorsMenuError001'])
    print(LangageValuesDict['ErrorsMenuError006'])

    if Render_exists : #I verify if an image exists
        CopyBlendFolder = os.path.join(BlendPath, "ShaderToolsImport", Mat_Name)

        if not os.path.exists(CopyBlendFolder) :
            os.makedirs(CopyBlendFolder)
        else:
            c = 1
            while os.path.exists(CopyBlendFolder) :
                CopyBlendFolder = os.path.join(BlendPath, "ShaderToolsImport", Mat_Name + "_" + str(c))
                c = c + 1

            os.makedirs(CopyBlendFolder)

        #Debug
        if not os.path.exists(CopyBlendFolder) :
            CopyBlendFolder = os.path.join(AppPath, "ShaderToolsImport")
            if not os.path.exists(CopyBlendFolder) :
                os.makedirs(CopyBlendFolder)

            CopyBlendFolder = os.path.join(AppPath, "ShaderToolsImport", Mat_Name)
            if not os.path.exists(CopyBlendFolder) :
                os.makedirs(CopyBlendFolder)


        #Here I copy all files in Out Folder to ShaderToolsImport folder:
        files = os.listdir(OutPath)

        for f in files:
            if not os.path.isdir(f):
                shutil.copy2(os.path.join(OutPath, f), os.path.join(CopyBlendFolder, f))



    #Now I treat textures informations
    textureNumberSlot = -1
    for values in MyTextureResult:
        v = 0
        textureNumberSlot = textureNumberSlot + 1
        for val in values:

            #Debug
            if val == 'False':
                val = False

            if val == 'True':
                val = True

            #Affect values:
            if v == 0:
                Tex_Index = val

            if v == 1:
                Tex_Name = val

            if v == 2:
                Tex_Type = val

            if v == 3:
                Tex_Preview_type = val

            if v == 4:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_use_preview_alpha  = val

            if v == 5:
                Tex_type_blend_progression = val

            if v == 6:
                Tex_type_blend_use_flip_axis = val

            if v == 7:
                Tex_type_clouds_cloud_type = val

            if v == 8:
                Tex_type_clouds_noise_type = val

            if v == 9:
                Tex_type_clouds_noise_basis = val

            if v == 10:
                Tex_type_noise_distortion = val

            if v == 11:
                Tex_type_env_map_source = val

            if v == 12:
                Tex_type_env_map_mapping = val

            if v == 13:
                Tex_type_env_map_clip_start = val

            if v == 14:
                Tex_type_env_map_clip_end = val

            if v == 15:
                Tex_type_env_map_resolution = val

            if v == 16:
                Tex_type_env_map_depth = val

            if v == 17:
                Tex_type_env_map_image_file = val

            if v == 18:
                Tex_type_env_map_zoom  = val

            if v == 19:
                Tex_type_magic_depth = val

            if v == 20:
                Tex_type_magic_turbulence = val

            if v == 21:
                Tex_type_marble_marble_type = val

            if v == 22:
                Tex_type_marble_noise_basis_2 = val

            if v == 23:
                Tex_type_marble_noise_type = val

            if v == 24:
                Tex_type_marble_noise_basis = val

            if v == 25:
                Tex_type_marble_noise_scale = val

            if v == 26:
                Tex_type_marble_noise_depth = val

            if v == 27:
                Tex_type_marble_turbulence = val

            if v == 28:
                Tex_type_marble_nabla = val

            if v == 29:
                Tex_type_musgrave_type = val

            if v == 30:
                Tex_type_musgrave_dimension_max = val

            if v == 31:
                Tex_type_musgrave_lacunarity = val

            if v == 32:
                Tex_type_musgrave_octaves = val

            if v == 33:
                Tex_type_musgrave_noise_intensity = val

            if v == 34:
                Tex_type_musgrave_noise_basis = val

            if v == 35:
                Tex_type_musgrave_noise_scale = val

            if v == 36:
                Tex_type_musgrave_nabla = val

            if v == 37:
                Tex_type_musgrave_offset = val

            if v == 38:
                Tex_type_musgrave_gain = val

            if v == 39:
                Tex_type_clouds_noise_scale = val

            if v == 40:
                Tex_type_clouds_nabla = val

            if v == 41:
                Tex_type_clouds_noise_depth = val

            if v == 42:
                Tex_type_noise_distortion_distortion = val

            if v == 43:
                Tex_type_noise_distortion_texture_distortion = val

            if v == 44:
                Tex_type_noise_distortion_nabla = val

            if v == 45:
                Tex_type_noise_distortion_noise_scale = val

            if v == 46:
                Tex_type_point_density_point_source = val

            if v == 47:
                Tex_type_point_density_radius = val

            if v == 48:
                Tex_type_point_density_particule_cache_space = val

            if v == 49:
                Tex_type_point_density_falloff = val

            if v == 50:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_type_point_density_use_falloff_curve = val

            if v == 51:
                Tex_type_point_density_falloff_soft = val

            if v == 52:
                Tex_type_point_density_falloff_speed_scale = val

            if v == 53:
                Tex_type_point_density_speed_scale = val

            if v == 54:
                Tex_type_point_density_color_source = val

            if v == 55:
                Tex_type_stucci_type = val

            if v == 56:
                Tex_type_stucci_noise_type = val

            if v == 57:
                Tex_type_stucci_basis = val

            if v == 58:
                Tex_type_stucci_noise_scale = val

            if v == 59:
                Tex_type_stucci_turbulence = val

            if v == 60:
                Tex_type_voronoi_distance_metric = val

            if v == 61:
                Tex_type_voronoi_minkovsky_exponent = val

            if v == 62:
                Tex_type_voronoi_color_mode = val

            if v == 63:
                Tex_type_voronoi_noise_scale = val

            if v == 64:
                Tex_type_voronoi_nabla = val

            if v == 65:
                Tex_type_voronoi_weight_1 = val

            if v == 66:
                Tex_type_voronoi_weight_2 = val

            if v == 67:
                Tex_type_voronoi_weight_3 = val

            if v == 68:
                Tex_type_voronoi_weight_4 = val

            if v == 69:
                Tex_type_voxel_data_file_format = val

            if v == 70:
                Tex_type_voxel_data_source_path = val

            if v == 71:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_type_voxel_data_use_still_frame = val

            if v == 72:
                Tex_type_voxel_data_still_frame = val

            if v == 73:
                Tex_type_voxel_data_interpolation  = val

            if v == 74:
                Tex_type_voxel_data_extension = val

            if v == 75:
                Tex_type_voxel_data_intensity  = val

            if v == 76:
                Tex_type_voxel_data_resolution_1 = val

            if v == 77:
                Tex_type_voxel_data_resolution_2 = val

            if v == 78:
                Tex_type_voxel_data_resoltion_3 = val

            if v == 79:
                Tex_type_voxel_data_smoke_data_type = val

            if v == 80:
                Tex_type_wood_noise_basis_2 = val

            if v == 81:
                Tex_type_wood_wood_type = val

            if v == 82:
                Tex_type_wood_noise_type = val

            if v == 83:
                Tex_type_wood_basis = val

            if v == 84:
                Tex_type_wood_noise_scale = val

            if v == 85:
                Tex_type_wood_nabla = val

            if v == 86:
                Tex_type_wood_turbulence = val

            if v == 87:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_diffuse = val

            if v == 88:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_color_diffuse = val

            if v == 89:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_alpha = val

            if v == 90:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_translucency = val

            if v == 91:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_specular = val

            if v == 92:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_color_spec = val

            if v == 93:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_map_hardness = val

            if v == 94:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_ambient = val

            if v == 95:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_emit = val

            if v == 96:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_mirror = val

            if v == 97:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_raymir = val

            if v == 98:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_normal = val

            if v == 99:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_warp = val

            if v == 100:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_displacement = val

            if v == 101:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_map_rgb_to_intensity = val

            if v == 102:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_map_invert  = val

            if v == 103:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_influence_use_stencil = val

            if v == 104:
                Tex_influence_diffuse_factor = val

            if v == 105:
                Tex_influence_color_factor = val

            if v == 106:
                Tex_influence_alpha_factor = val

            if v == 107:
                Tex_influence_translucency_factor  = val

            if v == 108:
                Tex_influence_specular_factor = val

            if v == 109:
                Tex_influence_specular_color_factor = val

            if v == 110:
                Tex_influence_hardness_factor = val

            if v == 111:
                Tex_influence_ambiant_factor = val

            if v == 112:
                Tex_influence_emit_factor = val

            if v == 113:
                Tex_influence_mirror_factor = val

            if v == 114:
                Tex_influence_raymir_factor = val

            if v == 115:
                Tex_influence_normal_factor = val

            if v == 116:
                Tex_influence_warp_factor = val

            if v == 117:
                Tex_influence_displacement_factor = val

            if v == 118:
                Tex_influence_default_value = val

            if v == 119:
                Tex_influence_blend_type = val

            if v == 120:
                Tex_influence_color_r = val

            if v == 121:
                Tex_influence_color_g = val

            if v == 122:
                Tex_influence_color_b = val

            if v == 123:
                Tex_influence_color_a = val

            if v == 124:
                Tex_influence_bump_method = val

            if v == 125:
                Tex_influence_objectspace = val

            if v == 126:
                Tex_mapping_texture_coords = val

            if v == 127:
                Tex_mapping_mapping = val

            if v == 128:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_mapping_use_from_dupli = val

            if v == 129:
                Tex_mapping_mapping_x  = val

            if v == 130:
                Tex_mapping_mapping_y = val

            if v == 131:
                Tex_mapping_mapping_z = val

            if v == 132:
                Tex_mapping_offset_x = val

            if v == 133:
                Tex_mapping_offset_y = val

            if v == 134:
                Tex_mapping_offset_z = val

            if v == 135:
                Tex_mapping_scale_x = val

            if v == 136:
                Tex_mapping_scale_y  = val

            if v == 137:
                Tex_mapping_scale_z = val

            if v == 138:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_colors_use_color_ramp = val

            if v == 139:
                Tex_colors_factor_r = val

            if v == 140:
                Tex_colors_factor_g = val

            if v == 141:
                Tex_colors_factor_b = val

            if v == 142:
                Tex_colors_intensity = val

            if v == 143:
                Tex_colors_contrast = val

            if v == 144:
                Tex_colors_saturation = val

            if v == 145:
                Mat_Idx = val

            if v == 146:
                Poi_Idx = val

            if v == 147:
                Col_Idx = val

            if v == 148:
                Tex_type_voronoi_intensity = val

            if v == 149:
                #I convert SQlite Boolean to Blender Boolean:
                if val == 1:
                    val = True

                else:
                    val = False

                Tex_mapping_use_from_original = val

            if v == 150:
                Tex_type_noise_distortion_noise_distortion = val

            if v == 151:
                Tex_type_noise_distortion_basis = val


            v = v + 1


        #Create texture :
        mytex = ""
        mytex = bpy.data.textures.new(name =Tex_Name , type=Tex_Type)
        slot =  obj.active_material.texture_slots.add()
        slot.texture = mytex
        slot.texture.use_preview_alpha  = Tex_use_preview_alpha




        if Tex_Type ==  'CLOUDS' :
            slot.texture.cloud_type  = Tex_type_clouds_cloud_type
            slot.texture.noise_type  = Tex_type_clouds_noise_type
            slot.texture.noise_basis  = Tex_type_clouds_noise_basis
            slot.texture.noise_scale  = Tex_type_clouds_noise_scale
            slot.texture.nabla  = Tex_type_clouds_nabla
            slot.texture.noise_depth  = Tex_type_clouds_noise_depth


        if Tex_Type ==  'POINT_DENSITY' :
            slot.texture.point_density.point_source  = Tex_type_point_density_point_source
            slot.texture.point_density.radius  = Tex_type_point_density_radius
            slot.texture.point_density.particle_cache_space  = Tex_type_point_density_particule_cache_space
            slot.texture.point_density.falloff  = Tex_type_point_density_falloff
            slot.texture.point_density.use_falloff_curve  = Tex_type_point_density_use_falloff_curve
            slot.texture.point_density.falloff_soft  = Tex_type_point_density_falloff_soft
            slot.texture.point_density.falloff_speed_scale  = Tex_type_point_density_falloff_speed_scale
            slot.texture.point_density.speed_scale  = Tex_type_point_density_speed_scale
            slot.texture.point_density.color_source  = Tex_type_point_density_color_source

            #My point density ramp:
            MyPointDensityRampRequest = "SELECT * FROM POINTDENSITY_RAMP WHERE Poi_Num_Texture=" + str(Tex_Index)
            Connexion = ShadersToolsDatabase.cursor()
            Connexion.execute(MyPointDensityRampRequest)
            ShadersToolsDatabase.commit()
            MyPointDensityRampResult = Connexion.fetchall()

            RAMP_MIN_POSITION = 0.0
            RAMP_MAX_POSITION = 1.0

            if MyPointDensityRampResult != []:
                v = 0
                counter = -1
                loop = -1
                #I must count numbers of ramps:
                for values in MyPointDensityRampResult:
                    loop = loop + 1

                #Now I create ramps:
                for values in MyPointDensityRampResult:
                    v = 0
                    counter = counter + 1
                    for val in values:

                        #Debug
                        if val == 'False':
                            val = False

                        if val == 'True':
                            val = True


                        #Affect values:
                        if v == 0:
                            Poi_Index = val

                        if v == 1:
                            Poi_Num_Material = val

                        if v == 2:
                            Poi_Num_Texture = val

                        if v == 3:
                            #I convert SQlite Boolean to Blender Boolean:
                            if val == 1:
                                val = True

                            else:
                                val = False

                            Poi_Flip = val

                        if v == 4:
                            Poi_Active_color_stop = val

                        if v == 5:
                            Poi_Between_color_stop = val

                        if v == 6:
                            Poi_Interpolation = val

                        if v == 7:
                            Poi_Position = val

                        if v == 8:
                            Poi_Color_stop_one_r = val

                        if v == 9:
                            Poi_Color_stop_one_g = val

                        if v == 10:
                            Poi_Color_stop_one_b = val

                        if v == 11:
                            Poi_Color_stop_one_a = val

                        if v == 12:
                            Poi_Color_stop_two_r = val

                        if v == 13:
                            Poi_Color_stop_two_g = val

                        if v == 14:
                            Poi_Color_stop_two_b = val

                        if v == 15:
                            Poi_Color_stop_two_a = val

                        v = v + 1


                    #Here my specular ramp :
                    ramp = bpy.context.object.active_material.texture_slots[textureNumberSlot].texture


                    if ramp.point_density.color_source == 'PARTICLE_SPEED' or ramp.point_density.color_source == 'PARTICLE_AGE':
                        if counter == 0:
                            #Here i get differentes color bands:
                            RAMP_MIN_POSITION = Poi_Position
                            ramp.point_density.color_ramp.elements[0].position = Poi_Position
                            ramp.point_density.color_ramp.interpolation  = Poi_Interpolation
                            ramp.point_density.color_ramp.elements[counter].color[0]  =  Poi_Color_stop_one_r
                            ramp.point_density.color_ramp.elements[counter].color[1]  =  Poi_Color_stop_one_g
                            ramp.point_density.color_ramp.elements[counter].color[2]  =  Poi_Color_stop_one_b
                            ramp.point_density.color_ramp.elements[counter].color[3]  =  Poi_Color_stop_one_a

                        if counter > 0 and counter < loop:
                            #Here i get differentes color bands:
                            ramp.point_density.color_ramp.elements.new(position = Poi_Position)
                            ramp.point_density.color_ramp.interpolation  = Poi_Interpolation
                            ramp.point_density.color_ramp.elements[counter].color[0]  =  Poi_Color_stop_one_r
                            ramp.point_density.color_ramp.elements[counter].color[1]  =  Poi_Color_stop_one_g
                            ramp.point_density.color_ramp.elements[counter].color[2]  =  Poi_Color_stop_one_b
                            ramp.point_density.color_ramp.elements[counter].color[3]  =  Poi_Color_stop_one_a

                        if counter == loop:
                            RAMP_MAX_POSITION = Poi_Position
                            ramp.point_density.color_ramp.elements[counter].position=1.0
                            ramp.point_density.color_ramp.interpolation  = Poi_Interpolation
                            ramp.point_density.color_ramp.elements[counter].color[0]  =  Poi_Color_stop_one_r
                            ramp.point_density.color_ramp.elements[counter].color[1]  =  Poi_Color_stop_one_g
                            ramp.point_density.color_ramp.elements[counter].color[2]  =  Poi_Color_stop_one_b
                            ramp.point_density.color_ramp.elements[counter].color[3]  =  Poi_Color_stop_one_a

                            #Debug first ramp and last ramp positions:
                            ramp.point_density.color_ramp.elements[0].position = RAMP_MIN_POSITION
                            ramp.point_density.color_ramp.elements[counter].position = RAMP_MAX_POSITION




        #**************************************************************************************************************************



        if Tex_Type ==  'ENVIRONMENT_MAP' :
            slot.texture.environment_map.source  = Tex_type_env_map_source
            slot.texture.environment_map.mapping  = Tex_type_env_map_mapping
            slot.texture.environment_map.clip_start  = Tex_type_env_map_clip_start
            slot.texture.environment_map.clip_end  = Tex_type_env_map_clip_end
            slot.texture.environment_map.resolution  = Tex_type_env_map_resolution
            slot.texture.environment_map.depth  = Tex_type_env_map_depth
            slot.texture.environment_map.zoom  = Tex_type_env_map_zoom


        if Tex_Type ==  'MAGIC':
            slot.texture.noise_depth  = Tex_type_magic_depth
            slot.texture.turbulence  = Tex_type_magic_turbulence


        if Tex_Type == 'MARBLE':
            slot.texture.marble_type  = Tex_type_marble_marble_type
            slot.texture.noise_basis_2  = Tex_type_marble_noise_basis_2
            slot.texture.noise_type  = Tex_type_marble_noise_type
            slot.texture.noise_basis  = Tex_type_marble_noise_basis
            slot.texture.noise_scale  = Tex_type_marble_noise_scale
            slot.texture.noise_depth  = Tex_type_marble_noise_depth
            slot.texture.turbulence  = Tex_type_marble_turbulence
            slot.texture.nabla  = Tex_type_marble_nabla


        if Tex_Type == 'MUSGRAVE':
            slot.texture.musgrave_type  = Tex_type_musgrave_type
            slot.texture.dimension_max  = Tex_type_musgrave_dimension_max
            slot.texture.lacunarity  = Tex_type_musgrave_lacunarity
            slot.texture.octaves  = Tex_type_musgrave_octaves
            slot.texture.noise_intensity  = Tex_type_musgrave_noise_intensity
            slot.texture.noise_basis  = Tex_type_musgrave_noise_basis
            slot.texture.noise_scale  = Tex_type_musgrave_noise_scale
            slot.texture.nabla  = Tex_type_musgrave_nabla
            slot.texture.offset  = Tex_type_musgrave_offset
            slot.texture.gain  = Tex_type_musgrave_gain


        if Tex_Type == 'DISTORTED_NOISE':
            slot.texture.distortion  = Tex_type_noise_distortion_distortion
            slot.texture.noise_distortion  = Tex_type_noise_distortion_noise_distortion
            slot.texture.noise_basis  = Tex_type_noise_distortion_basis
            slot.texture.nabla  = Tex_type_noise_distortion_nabla
            slot.texture.noise_scale  = Tex_type_noise_distortion_noise_scale


        if Tex_Type == 'STUCCI':
            slot.texture.stucci_type  = Tex_type_stucci_type
            slot.texture.noise_type  = Tex_type_stucci_noise_type
            slot.texture.noise_basis  = Tex_type_stucci_basis
            slot.texture.noise_scale  = Tex_type_stucci_noise_scale
            slot.texture.turbulence  = Tex_type_stucci_turbulence


        if Tex_Type == 'VORONOI':
            slot.texture.noise_intensity  = Tex_type_voronoi_intensity
            slot.texture.distance_metric  = Tex_type_voronoi_distance_metric
            slot.texture.minkovsky_exponent  = Tex_type_voronoi_minkovsky_exponent
            slot.texture.color_mode  = Tex_type_voronoi_color_mode
            slot.texture.noise_scale  = Tex_type_voronoi_noise_scale
            slot.texture.nabla  = Tex_type_voronoi_nabla
            slot.texture.weight_1  = Tex_type_voronoi_weight_1
            slot.texture.weight_2  = Tex_type_voronoi_weight_2
            slot.texture.weight_3  = Tex_type_voronoi_weight_3
            slot.texture.weight_4  = Tex_type_voronoi_weight_4


        if Tex_Type == 'VOXEL_DATA':
            slot.texture.voxel_data.file_format  = Tex_type_voxel_data_file_format
            slot.texture.voxel_data.filepath  = Tex_type_voxel_data_source_path
            slot.texture.voxel_data.use_still_frame  = Tex_type_voxel_data_use_still_frame
            slot.texture.voxel_data.still_frame  = Tex_type_voxel_data_still_frame
            slot.texture.voxel_data.interpolation  = Tex_type_voxel_data_interpolation
            slot.texture.voxel_data.extension  = Tex_type_voxel_data_extension
            slot.texture.voxel_data.intensity  = Tex_type_voxel_data_intensity
            slot.texture.voxel_data.resolution[0]  = Tex_type_voxel_data_resolution_1
            slot.texture.voxel_data.resolution[1]  = Tex_type_voxel_data_resolution_2
            slot.texture.voxel_data.resolution[2]  = Tex_type_voxel_data_resoltion_3
            slot.texture.voxel_data.smoke_data_type  = Tex_type_voxel_data_smoke_data_type


        if Tex_Type == 'WOOD':
            slot.texture.noise_basis_2  = Tex_type_wood_noise_basis_2
            slot.texture.wood_type  = Tex_type_wood_wood_type
            slot.texture.noise_type  = Tex_type_wood_noise_type
            slot.texture.noise_basis  = Tex_type_wood_basis
            slot.texture.noise_scale  = Tex_type_wood_noise_scale
            slot.texture.nabla  = float(Tex_type_wood_nabla)
            slot.texture.turbulence  = Tex_type_wood_turbulence



        if Tex_Type == 'BLEND':
            slot.texture.progression  = Tex_type_blend_progression
            slot.texture.use_flip_axis  = Tex_type_blend_use_flip_axis


        if Tex_Type ==  'IMAGE' :
            #I create image texture environnement:
            imagePath = os.path.join(CopyBlendFolder, Tex_ima_name)
            img=bpy.data.images.load(filepath=imagePath )

            #Now I create file:
            slot.texture.image  = img
            slot.texture.image.use_fields  = Tex_ima_fields
            slot.texture.image.use_premultiply  = Tex_ima_premultiply
            if Tex_ima_field_order != '': #Debug
                slot.texture.image.field_order  = Tex_ima_field_order


        slot.texture.factor_red  = Tex_colors_factor_r
        slot.texture.factor_green  = Tex_colors_factor_g
        slot.texture.factor_blue  = Tex_colors_factor_b
        slot.texture.intensity  = Tex_colors_intensity
        slot.texture.contrast  = Tex_colors_contrast
        slot.texture.saturation  = Tex_colors_saturation
        slot.texture_coords  = Tex_mapping_texture_coords
        slot.mapping  = Tex_mapping_mapping

        if slot.texture_coords == 'UV' or slot.texture_coords == 'ORCO':
            slot.use_from_dupli  = Tex_mapping_use_from_dupli

        if slot.texture_coords == 'OBJECT':
            slot.use_from_original  =  Tex_mapping_use_from_original

        slot.mapping_x  = Tex_mapping_mapping_x
        slot.mapping_y  = Tex_mapping_mapping_y
        slot.mapping_z  = Tex_mapping_mapping_z
        slot.offset[0]  = Tex_mapping_offset_x
        slot.offset[1]  = Tex_mapping_offset_y
        slot.offset[2]  = Tex_mapping_offset_z
        slot.scale[0]  = Tex_mapping_scale_x
        slot.scale[1]  = Tex_mapping_scale_y
        slot.scale[2]  = Tex_mapping_scale_z
        slot.use_map_diffuse  = Tex_influence_use_map_diffuse
        slot.use_map_color_diffuse  = Tex_influence_use_map_color_diffuse
        slot.use_map_alpha  = Tex_influence_use_map_alpha
        slot.use_map_translucency  = Tex_influence_use_map_translucency
        slot.use_map_specular  = Tex_influence_use_map_specular
        slot.use_map_color_spec  = Tex_influence_use_map_color_spec
        slot.use_map_hardness  = Tex_influence_use_map_map_hardness
        slot.use_map_ambient  = Tex_influence_use_map_ambient
        slot.use_map_emit  = Tex_influence_use_map_emit
        slot.use_map_mirror  = Tex_influence_use_map_mirror
        slot.use_map_raymir  = Tex_influence_use_map_raymir
        slot.use_map_normal  = Tex_influence_use_map_normal
        slot.use_map_warp  = Tex_influence_use_map_warp
        slot.use_map_displacement  = Tex_influence_use_map_displacement
        slot.use_rgb_to_intensity  = Tex_influence_use_map_rgb_to_intensity
        slot.invert = Tex_influence_map_invert
        slot.use_stencil = Tex_influence_use_stencil
        slot.diffuse_factor = Tex_influence_diffuse_factor
        slot.diffuse_color_factor  = Tex_influence_color_factor
        slot.alpha_factor  = Tex_influence_alpha_factor
        slot.translucency_factor  = Tex_influence_translucency_factor
        slot.specular_factor  = Tex_influence_specular_factor
        slot.specular_color_factor  = Tex_influence_specular_color_factor
        slot.hardness_factor  = Tex_influence_hardness_factor
        slot.ambient_factor  = Tex_influence_ambiant_factor
        slot.emit_factor  = Tex_influence_emit_factor
        slot.mirror_factor  = Tex_influence_mirror_factor
        slot.raymir_factor  = Tex_influence_raymir_factor
        slot.normal_factor  = Tex_influence_normal_factor
        slot.warp_factor  = Tex_influence_warp_factor
        slot.displacement_factor  = Tex_influence_displacement_factor
        slot.default_value  = Tex_influence_default_value
        slot.blend_type  = Tex_influence_blend_type
        slot.color[0]  = Tex_influence_color_r
        slot.color[1]  = Tex_influence_color_g
        slot.color[2]  = Tex_influence_color_b
        slot.bump_method  =  Tex_influence_bump_method
        slot.bump_objectspace  = Tex_influence_objectspace



        #**********************************************************************************************************
        #My colors ramp:
        MyColorRampRequest = "SELECT * FROM COLORS_RAMP WHERE Col_Num_Texture=" + str(Tex_Index)
        Connexion = ShadersToolsDatabase.cursor()
        Connexion.execute(MyColorRampRequest)
        ShadersToolsDatabase.commit()
        MyColorRampResult = Connexion.fetchall()

        if MyColorRampResult != []:
            v = 0
            counter = -1
            loop = -1
            #I must count numbers of ramps:
            for values in MyColorRampResult:
                loop = loop + 1

            #Now I create ramps:
            for values in MyColorRampResult:
                v = 0
                counter = counter + 1
                for val in values:
                    #Debug
                    if val == 'False':
                        val = False

                    if val == 'True':
                        val = True


                    #Affect values:
                    if v == 0:
                        Col_Index = val

                    if v == 1:
                        Col_Num_Material = val

                    if v == 2:
                        Col_Num_Texture = val

                    if v == 3:
                        #I convert SQlite Boolean to Blender Boolean:
                        if val == 1:
                            val = True

                        else:
                            val = False

                        Col_Flip = val

                    if v == 4:
                        Col_Active_color_stop = val

                    if v == 5:
                        Col_Between_color_stop = val

                    if v == 6:
                        Col_Interpolation = val

                    if v == 7:
                        Col_Position = val

                    if v == 8:
                        Col_Color_stop_one_r = val

                    if v == 9:
                        Col_Color_stop_one_g = val

                    if v == 10:
                        Col_Color_stop_one_b = val

                    if v == 11:
                        Col_Color_stop_one_a = val

                    if v == 12:
                        Col_Color_stop_two_r = val

                    if v == 13:
                        Col_Color_stop_two_g = val

                    if v == 14:
                        Col_Color_stop_two_b = val

                    if v == 15:
                        Col_Color_stop_two_a = val

                    v = v + 1


                #Here my specular ramp :
                ramp = bpy.context.object.active_material.texture_slots[textureNumberSlot].texture

                #Here my specular ramp :
                ramp.use_color_ramp = True

                if counter == 0:
                    #Here i get differentes color bands:
                    RAMP_MIN_POSITION = Col_Position
                    ramp.color_ramp.elements[0].position = Col_Position
                    ramp.color_ramp.interpolation  = Col_Interpolation
                    ramp.color_ramp.elements[counter].color[0]  =  Col_Color_stop_one_r
                    ramp.color_ramp.elements[counter].color[1]  =  Col_Color_stop_one_g
                    ramp.color_ramp.elements[counter].color[2]  =  Col_Color_stop_one_b
                    ramp.color_ramp.elements[counter].color[3]  =  Col_Color_stop_one_a

                if counter > 0 and counter < loop:
                    #Here i get differentes color bands:
                    ramp.color_ramp.elements.new(position = Col_Position)
                    ramp.color_ramp.interpolation  = Col_Interpolation
                    ramp.color_ramp.elements[counter].color[0]  =  Col_Color_stop_one_r
                    ramp.color_ramp.elements[counter].color[1]  =  Col_Color_stop_one_g
                    ramp.color_ramp.elements[counter].color[2]  =  Col_Color_stop_one_b
                    ramp.color_ramp.elements[counter].color[3]  =  Col_Color_stop_one_a

                if counter == loop:
                    RAMP_MAX_POSITION = Col_Position
                    ramp.color_ramp.elements[counter].position=1.0
                    ramp.color_ramp.interpolation  = Col_Interpolation
                    ramp.color_ramp.elements[counter].color[0]  =  Col_Color_stop_one_r
                    ramp.color_ramp.elements[counter].color[1]  =  Col_Color_stop_one_g
                    ramp.color_ramp.elements[counter].color[2]  =  Col_Color_stop_one_b
                    ramp.color_ramp.elements[counter].color[3]  =  Col_Color_stop_one_a

                    #Debug first ramp and last ramp positions:
                    ramp.color_ramp.elements[0].position = RAMP_MIN_POSITION
                    ramp.color_ramp.elements[counter].position = RAMP_MAX_POSITION


    #**************************************************************************************************************************

    #My diffuse ramp:
    MyDiffuseRampRequest = "SELECT * FROM DIFFUSE_RAMP WHERE Dif_Num_material=" + str(MyMaterialIndex)
    Connexion = ShadersToolsDatabase.cursor()
    Connexion.execute(MyDiffuseRampRequest)
    ShadersToolsDatabase.commit()
    MyDiffuseRampResult = Connexion.fetchall()

    if MyDiffuseRampResult != []:
        v = 0
        counter = -1
        loop = -1
        #I must count numbers of ramps:
        for values in MyDiffuseRampResult:
            loop = loop + 1

        #Now I create ramps:
        for values in MyDiffuseRampResult:
            v = 0
            counter = counter + 1
            for val in values:

                #Debug
                if val == 'False':
                    val = False

                if val == 'True':
                    val = True


                #Affect values:
                if v == 0:
                    Dif_Index = val

                if v == 1:
                    Dif_Num_Material = val

                if v == 2:
                    #I convert SQlite Boolean to Blender Boolean:
                    if val == 1:
                        val = True

                    else:
                        val = False

                    Dif_Flip = val

                if v == 3:
                    Dif_Active_color_stop = val

                if v == 4:
                    Dif_Between_color_stop = val

                if v == 5:
                    Dif_Interpolation = val

                if v == 6:
                    Dif_Position = val

                if v == 7:
                    Dif_Color_stop_one_r = val

                if v == 8:
                    Dif_Color_stop_one_g = val

                if v == 9:
                    Dif_Color_stop_one_b = val

                if v == 10:
                    Dif_Color_stop_one_a = val

                if v == 11:
                    Dif_Color_stop_two_r = val

                if v == 12:
                    Dif_Color_stop_two_g = val

                if v == 13:
                    Dif_Color_stop_two_b = val

                if v == 14:
                    Dif_Color_stop_two_a = val

                if v == 15:
                    Dif_Ramp_input = val

                if v == 16:
                    Dif_Ramp_blend = val

                if v == 17:
                    Dif_Ramp_factor = val

                v = v + 1


            #Here my diffuse ramp :
            ramp = bpy.context.object.active_material

            #Here my diffuse ramp :
            ramp.use_diffuse_ramp = True

            if counter == 0:
                #Here i get differentes color bands:
                RAMP_MIN_POSITION = Dif_Position
                ramp.diffuse_ramp.elements[0].position = Dif_Position
                ramp.diffuse_ramp_blend  = Dif_Ramp_blend
                ramp.diffuse_ramp_input  = Dif_Ramp_input
                ramp.diffuse_ramp_factor  = Dif_Ramp_factor
                ramp.diffuse_ramp.interpolation  = Dif_Interpolation
                ramp.diffuse_ramp.elements[counter].color[0]  =  Dif_Color_stop_one_r
                ramp.diffuse_ramp.elements[counter].color[1]  =  Dif_Color_stop_one_g
                ramp.diffuse_ramp.elements[counter].color[2]  =  Dif_Color_stop_one_b
                ramp.diffuse_ramp.elements[counter].color[3]  =  Dif_Color_stop_one_a

            if counter > 0 and counter < loop:
                #Here i get differentes color bands:
                ramp.diffuse_ramp.elements.new(position = Dif_Position)
                ramp.diffuse_ramp_blend  = Dif_Ramp_blend
                ramp.diffuse_ramp_input  = Dif_Ramp_input
                ramp.diffuse_ramp_factor  = Dif_Ramp_factor
                ramp.diffuse_ramp.interpolation  = Dif_Interpolation
                ramp.diffuse_ramp.elements[counter].color[0]  =  Dif_Color_stop_one_r
                ramp.diffuse_ramp.elements[counter].color[1]  =  Dif_Color_stop_one_g
                ramp.diffuse_ramp.elements[counter].color[2]  =  Dif_Color_stop_one_b
                ramp.diffuse_ramp.elements[counter].color[3]  =  Dif_Color_stop_one_a

            if counter == loop:
                RAMP_MAX_POSITION = Dif_Position
                ramp.diffuse_ramp.elements[counter].position=1.0
                ramp.diffuse_ramp_blend  = Dif_Ramp_blend
                ramp.diffuse_ramp_input  = Dif_Ramp_input
                ramp.diffuse_ramp_factor  = Dif_Ramp_factor
                ramp.diffuse_ramp.interpolation  = Dif_Interpolation
                ramp.diffuse_ramp.elements[counter].color[0]  =  Dif_Color_stop_one_r
                ramp.diffuse_ramp.elements[counter].color[1]  =  Dif_Color_stop_one_g
                ramp.diffuse_ramp.elements[counter].color[2]  =  Dif_Color_stop_one_b
                ramp.diffuse_ramp.elements[counter].color[3]  =  Dif_Color_stop_one_a


                #Debug first ramp and last ramp positions:
                ramp.diffuse_ramp.elements[0].position = RAMP_MIN_POSITION
                ramp.diffuse_ramp.elements[counter].position = RAMP_MAX_POSITION


    #**********************************************************************************************************

    #My specular ramp:
    MySpecularRampRequest = "SELECT * FROM SPECULAR_RAMP WHERE Spe_Num_Material=" + str(MyMaterialIndex)
    Connexion = ShadersToolsDatabase.cursor()
    Connexion.execute(MySpecularRampRequest)
    ShadersToolsDatabase.commit()
    MySpecularRampResult = Connexion.fetchall()

    if MySpecularRampResult != []:
        v = 0
        counter = -1
        loop = -1
        #I must count numbers of ramps:
        for values in MySpecularRampResult:
            loop = loop + 1

        #Now I create ramps:
        for values in MySpecularRampResult:
            v = 0
            counter = counter + 1
            for val in values:

                #Debug
                if val == 'False':
                    val = False

                if val == 'True':
                    val = True


                #Affect values:
                if v == 0:
                    Spe_Index = val

                if v == 1:
                    Spe_Num_Material = val

                if v == 2:
                    #I convert SQlite Boolean to Blender Boolean:
                    if val == 1:
                        val = True

                    else:
                        val = False

                    Spe_Flip = val

                if v == 3:
                    Spe_Active_color_stop = val

                if v == 4:
                    Spe_Between_color_stop = val

                if v == 5:
                    Spe_Interpolation = val

                if v == 6:
                    Spe_Position = val

                if v == 7:
                    Spe_Color_stop_one_r = val

                if v == 8:
                    Spe_Color_stop_one_g = val

                if v == 9:
                    Spe_Color_stop_one_b = val

                if v == 10:
                    Spe_Color_stop_one_a = val

                if v == 11:
                    Spe_Color_stop_two_r = val

                if v == 12:
                    Spe_Color_stop_two_g = val

                if v == 13:
                    Spe_Color_stop_two_b = val

                if v == 14:
                    Spe_Color_stop_two_a = val

                if v == 15:
                    Spe_Ramp_input = val

                if v == 16:
                    Spe_Ramp_blend = val

                if v == 17:
                    Spe_Ramp_factor = val

                v = v + 1


            #Here my specular ramp :
            ramp = bpy.context.object.active_material

            #Here my specular ramp :
            ramp.use_specular_ramp = True

            if counter == 0:
                #Here i get differentes color bands:
                RAMP_MIN_POSITION = Spe_Position
                ramp.specular_ramp.elements[0].position = Spe_Position
                ramp.specular_ramp_blend  = Spe_Ramp_blend
                ramp.specular_ramp_input  = Spe_Ramp_input
                ramp.specular_ramp_factor  = Spe_Ramp_factor
                ramp.specular_ramp.interpolation  = Spe_Interpolation
                ramp.specular_ramp.elements[counter].color[0]  =  Spe_Color_stop_one_r
                ramp.specular_ramp.elements[counter].color[1]  =  Spe_Color_stop_one_g
                ramp.specular_ramp.elements[counter].color[2]  =  Spe_Color_stop_one_b
                ramp.specular_ramp.elements[counter].color[3]  =  Spe_Color_stop_one_a

            if counter > 0 and counter < loop:
                #Here i get differentes color bands:
                ramp.specular_ramp.elements.new(position = Spe_Position)
                ramp.specular_ramp_blend  = Spe_Ramp_blend
                ramp.specular_ramp_input  = Spe_Ramp_input
                ramp.specular_ramp_factor  = Spe_Ramp_factor
                ramp.specular_ramp.interpolation  = Spe_Interpolation
                ramp.specular_ramp.elements[counter].color[0]  =  Spe_Color_stop_one_r
                ramp.specular_ramp.elements[counter].color[1]  =  Spe_Color_stop_one_g
                ramp.specular_ramp.elements[counter].color[2]  =  Spe_Color_stop_one_b
                ramp.specular_ramp.elements[counter].color[3]  =  Spe_Color_stop_one_a

            if counter == loop:
                RAMP_MAX_POSITION = Spe_Position
                ramp.specular_ramp.elements[counter].position=1.0
                ramp.specular_ramp_blend  = Spe_Ramp_blend
                ramp.specular_ramp_input  = Spe_Ramp_input
                ramp.specular_ramp_factor  = Spe_Ramp_factor
                ramp.specular_ramp.interpolation  = Spe_Interpolation
                ramp.specular_ramp.elements[counter].color[0]  =  Spe_Color_stop_one_r
                ramp.specular_ramp.elements[counter].color[1]  =  Spe_Color_stop_one_g
                ramp.specular_ramp.elements[counter].color[2]  =  Spe_Color_stop_one_b
                ramp.specular_ramp.elements[counter].color[3]  =  Spe_Color_stop_one_a


                #Debug first ramp and last ramp positions:
                ramp.specular_ramp.elements[0].position = RAMP_MIN_POSITION
                ramp.specular_ramp.elements[counter].position = RAMP_MAX_POSITION




    #I close base
    Connexion.close()



    #**********************************************************************************************************************************



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
        os.mkdir(ZipPath)

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
                              'obj.material_slots[obj.material_slots.__len__() - 1].material = CreateMaterial("MAT_EXP_' +  Mat_Name + '")\n\n\n']









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
                print(LangageValuesDict['ErrorsMenuError001'])
                print(LangageValuesDict['ErrorsMenuError002'])
                print(LangageValuesDict['ErrorsMenuError003'])


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
                        print(LangageValuesDict['ErrorsMenuError013'])
                        #print("*******************************************************************************")


                    #I treat informations:
                    MY_EXPORT_INFORMATIONS.append('imagePath = os.path.join(scriptPath, Mat_Name + "_" + "' + IMAGE_FILENAME +  '")\n')
                    MY_EXPORT_INFORMATIONS.append('img=bpy.data.images.load(filepath=imagePath)\n')

                    save_path = os.path.join(ZipPath, Mat_Name)


                    if '.py' in save_path:
                        save_path = save_path.replace('.py', '')

                    #Now I create file:
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image  = img\n')
                    MY_EXPORT_INFORMATIONS.append('#slot.texture.image.name  = "' + IMAGE_FILENAME +  '"\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_fields  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_fields) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.use_premultiply  = ' + str(obj.active_material.texture_slots[textureNumbers].texture.image.use_premultiply) +  '\n')
                    MY_EXPORT_INFORMATIONS.append('slot.texture.image.field_order  = "' + str(obj.active_material.texture_slots[textureNumbers].texture.image.field_order) +  '"\n')

                    #I copy images :
                    shutil.copy2(IMAGE_FILEPATH, save_path + "_" + IMAGE_FILENAME)
                    print(LangageValuesDict['ErrorsMenuError005'])

                    print("*******************************************************************************")



                if tex.texture_slots[textureNumbers].texture.image.source == 'GENERATED':
                    myImg = str(obj.active_material.texture_slots[textureNumbers].texture.image.name)
                    myImg = '"' + myImg
                    MY_EXPORT_INFORMATIONS.append('imagePath = os.path.join(scriptPath, Mat_Name + "_" + ' + myImg +  '.png")\n')
                    MY_EXPORT_INFORMATIONS.append('img=bpy.data.images.load(filepath=imagePath)\n')

                    save_path = os.path.join(ZipPath, Mat_Name)

                    if '.py' in save_path:
                        save_path = save_path.replace('.py', '')


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

                    print(LangageValuesDict['ErrorsMenuError005'])
                    print("*******************************************************************************")


                    #**********************************************************************************************************************


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
    if '.py' in File_Path:
        File_Path = File_Path.replace('.py', '')

    File_Path = File_Path.replace('.', '')

    if '.py' in Mat_Name:
        Mat_Name = Mat_Name.replace('.py', '')

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

    Image_Path = Image_Path.replace("'", "")
    SaveOriginalName = Image_Path

    #Relative/Absolute Paths:
    if '..' in Image_Path:
        Image_Path = Image_Path.replace('..', '')

    if './' in Image_Path:
        Image_Path = Image_Path.replace('./', '')


    while "//" in Image_Path:
        Image_Path = Image_Path.replace('//', '/')

    while "\\\\" in Image_Path:
        Image_Path = Image_Path.replace('\\\\', '\\')

    SaveOriginalPath = Image_Path

    if not os.path.exists(Image_Path) :
        Image_Path = os.path.join(BlendPath, Image_Path)

    if not os.path.exists(Image_Path) :
        Image_Path = '~' + SaveOriginalPath

    if not os.path.exists(Image_Path) :
        SaveOriginalName = SaveOriginalName.replace("'", "")
        print(LangageValuesDict['ErrorsMenuError009'] + '"' + SaveOriginalName + '"')
        print(LangageValuesDict['ErrorsMenuError010'])
        print(LangageValuesDict['ErrorsMenuError011'])
        print(LangageValuesDict['ErrorsMenuError012'])
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
def PrepareSqlUpdateSaveRequest(MyPrimaryKeys, Mat_Name):
    print()
    print("                                        *****                         ")
    print()
    print("*******************************************************************************")
    print("*                                   SAVE MATERIAL                             *")
    print("*******************************************************************************")


    obj = bpy.context.object
    SSS_Mat_Name = Mat_Name

    #Materials values :
    Mat_Index = MyPrimaryKeys[1]
    Idx_textures = MyPrimaryKeys[2]
    Idx_ramp_diffuse = MyPrimaryKeys[5]
    Idx_ramp_specular = MyPrimaryKeys[7]

    Mat_Name = "'MAT_PRE_" + Mat_Name + "'"
    Mat_Type = "'" + obj.active_material.type +"'"
    Mat_Preview_render_type = "'" + obj.active_material.preview_render_type + "'"

    Mat_diffuse_color_r = obj.active_material.diffuse_color[0]
    Mat_diffuse_color_g = obj.active_material.diffuse_color[1]
    Mat_diffuse_color_b = obj.active_material.diffuse_color[2]
    Mat_diffuse_color_a = 0
    Mat_diffuse_shader = "'" + obj.active_material.diffuse_shader + "'"
    Mat_diffuse_intensity = obj.active_material.diffuse_intensity
    Mat_use_diffuse_ramp = obj.active_material.use_diffuse_ramp
    Mat_diffuse_roughness = obj.active_material.roughness
    Mat_diffuse_toon_size = obj.active_material.diffuse_toon_size
    Mat_diffuse_toon_smooth = obj.active_material.diffuse_toon_smooth
    Mat_diffuse_darkness = obj.active_material.darkness
    Mat_diffuse_fresnel = obj.active_material.diffuse_fresnel
    Mat_diffuse_fresnel_factor = obj.active_material.diffuse_fresnel_factor

    Mat_specular_color_r = obj.active_material.specular_color[0]
    Mat_specular_color_g = obj.active_material.specular_color[1]
    Mat_specular_color_b = obj.active_material.specular_color[2]
    Mat_specular_color_a = 0
    Mat_specular_shader = "'" + obj.active_material.specular_shader + "'"
    Mat_specular_intensity = obj.active_material.specular_intensity
    Mat_specular_ramp = obj.active_material.specular_ramp
    Mat_specular_hardness = obj.active_material.specular_hardness
    Mat_specular_ior = obj.active_material.specular_ior
    Mat_specular_toon_size = obj.active_material.specular_toon_size
    Mat_specular_toon_smooth =  obj.active_material.specular_toon_smooth

    Mat_shading_emit = obj.active_material.emit
    Mat_shading_ambient = obj.active_material.ambient
    Mat_shading_translucency = obj.active_material.translucency
    Mat_shading_use_shadeless = obj.active_material.use_shadeless
    Mat_shading_use_tangent_shading = obj.active_material.use_tangent_shading
    Mat_shading_use_cubic = obj.active_material.use_cubic

    Mat_transparency_use_transparency = obj.active_material.use_transparency
    Mat_transparency_method = "'" + obj.active_material.transparency_method + "'"
    Mat_transparency_alpha = obj.active_material.alpha
    Mat_transparency_fresnel = obj.active_material.raytrace_transparency.fresnel
    Mat_transparency_specular_alpha = obj.active_material.specular_alpha
    Mat_transparency_fresnel_factor = obj.active_material.raytrace_transparency.fresnel_factor
    Mat_transparency_ior = obj.active_material.raytrace_transparency.ior
    Mat_transparency_filter = obj.active_material.raytrace_transparency.filter
    Mat_transparency_falloff = obj.active_material.raytrace_transparency.falloff
    Mat_transparency_depth_max = obj.active_material.raytrace_transparency.depth_max
    Mat_transparency_depth = obj.active_material.raytrace_transparency.depth
    Mat_transparency_gloss_factor = obj.active_material.raytrace_transparency.gloss_factor
    Mat_transparency_gloss_threshold = obj.active_material.raytrace_transparency.gloss_threshold
    Mat_transparency_gloss_samples = obj.active_material.raytrace_transparency.gloss_samples

    Mat_raytracemirror_use = obj.active_material.raytrace_mirror.use
    Mat_raytracemirror_reflect_factor = obj.active_material.raytrace_mirror.reflect_factor
    Mat_raytracemirror_fresnel =  obj.active_material.raytrace_mirror.fresnel
    Mat_raytracemirror_color_r =  obj.active_material.mirror_color[0]
    Mat_raytracemirror_color_g =  obj.active_material.mirror_color[1]
    Mat_raytracemirror_color_b =  obj.active_material.mirror_color[2]
    Mat_raytracemirror_color_a =  0
    Mat_raytracemirror_fresnel_factor = obj.active_material.raytrace_mirror.fresnel_factor
    Mat_raytracemirror_depth = obj.active_material.raytrace_mirror.depth
    Mat_raytracemirror_distance = obj.active_material.raytrace_mirror.distance
    Mat_raytracemirror_fade_to = "'" + obj.active_material.raytrace_mirror.fade_to + "'"
    Mat_raytracemirror_gloss_factor =  obj.active_material.raytrace_mirror.gloss_factor
    Mat_raytracemirror_gloss_threshold = obj.active_material.raytrace_mirror.gloss_threshold
    Mat_raytracemirror_gloss_samples = obj.active_material.raytrace_mirror.gloss_samples
    Mat_raytracemirror_gloss_anisotropic = obj.active_material.raytrace_mirror.gloss_anisotropic

    Mat_subsurfacescattering_use = obj.active_material.subsurface_scattering.use
    Mat_subsurfacescattering_presets = "'" + "SSS_PRE_" + SSS_Mat_Name + "'"
    Mat_subsurfacescattering_ior = obj.active_material.subsurface_scattering.ior
    Mat_subsurfacescattering_scale = obj.active_material.subsurface_scattering.scale
    Mat_subsurfacescattering_color_r = obj.active_material.subsurface_scattering.color[0]
    Mat_subsurfacescattering_color_g = obj.active_material.subsurface_scattering.color[1]
    Mat_subsurfacescattering_color_b = obj.active_material.subsurface_scattering.color[2]
    Mat_subsurfacescattering_color_a =  0
    Mat_subsurfacescattering_color_factor = obj.active_material.subsurface_scattering.color_factor
    Mat_subsurfacescattering_texture_factor = obj.active_material.subsurface_scattering.texture_factor
    Mat_subsurfacescattering_radius_one = obj.active_material.subsurface_scattering.radius[0]
    Mat_subsurfacescattering_radius_two = obj.active_material.subsurface_scattering.radius[1]
    Mat_subsurfacescattering_radius_three = obj.active_material.subsurface_scattering.radius[2]
    Mat_subsurfacescattering_front = obj.active_material.subsurface_scattering.front
    Mat_subsurfacescattering_back = obj.active_material.subsurface_scattering.back
    Mat_subsurfacescattering_error_threshold = obj.active_material.subsurface_scattering.error_threshold

    Mat_strand_root_size = obj.active_material.strand.root_size
    Mat_strand_tip_size = obj.active_material.strand.tip_size
    Mat_strand_size_min = obj.active_material.strand.size_min
    Mat_strand_blender_units =  obj.active_material.strand.use_blender_units
    Mat_strand_use_tangent_shading = obj.active_material.strand.use_tangent_shading
    Mat_strand_shape = obj.active_material.strand.shape
    Mat_strand_width_fade = obj.active_material.strand.width_fade
    Mat_strand_blend_distance = obj.active_material.strand.blend_distance

    Mat_options_use_raytrace = obj.active_material.use_raytrace
    Mat_options_use_full_oversampling = obj.active_material.use_full_oversampling
    Mat_options_use_sky =  obj.active_material.use_sky
    Mat_options_use_mist =  obj.active_material.use_mist
    Mat_options_invert_z = obj.active_material.invert_z
    Mat_options_offset_z = obj.active_material.offset_z
    Mat_options_use_face_texture = obj.active_material.use_face_texture
    Mat_options_use_texture_alpha =  obj.active_material.use_face_texture_alpha
    Mat_options_use_vertex_color_paint = obj.active_material.use_vertex_color_paint
    Mat_options_use_vertex_color_light = obj.active_material.use_vertex_color_light
    Mat_options_use_object_color = obj.active_material.use_object_color
    Mat_options_pass_index = obj.active_material.pass_index

    Mat_shadow_use_shadows = obj.active_material.use_shadows
    Mat_shadow_use_transparent_shadows = obj.active_material.use_transparent_shadows
    Mat_shadow_use_cast_shadows_only = obj.active_material.use_cast_shadows_only
    Mat_shadow_shadow_cast_alpha =  obj.active_material.shadow_cast_alpha
    Mat_shadow_use_only_shadow = obj.active_material.use_only_shadow
    Mat_shadow_shadow_only_type = "'" + obj.active_material.shadow_only_type + "'"
    Mat_shadow_use_cast_buffer_shadows = obj.active_material.use_cast_buffer_shadows
    Mat_shadow_shadow_buffer_bias = obj.active_material.shadow_buffer_bias
    Mat_shadow_use_ray_shadow_bias = obj.active_material.use_ray_shadow_bias
    Mat_shadow_shadow_ray_bias = obj.active_material.shadow_ray_bias
    Mat_shadow_use_cast_approximate = obj.active_material.use_cast_approximate



    #I create a material list :
    MY_MATERIAL = [Mat_Index,
                   Mat_Name,
                   Mat_Type,
                   Mat_Preview_render_type,
                   Mat_diffuse_color_r,
                   Mat_diffuse_color_g,
                   Mat_diffuse_color_b,
                   Mat_diffuse_color_a,
                   Mat_diffuse_shader,
                   Mat_diffuse_intensity,
                   Mat_use_diffuse_ramp,
                   Mat_diffuse_roughness,
                   Mat_diffuse_toon_size,
                   Mat_diffuse_toon_smooth,
                   Mat_diffuse_darkness,
                   Mat_diffuse_fresnel,
                   Mat_diffuse_fresnel_factor,
                   Mat_specular_color_r,
                   Mat_specular_color_g,
                   Mat_specular_color_b,
                   Mat_specular_color_a,
                   Mat_specular_shader,
                   Mat_specular_intensity,
                   Mat_specular_ramp,
                   Mat_specular_hardness,
                   Mat_specular_ior,
                   Mat_specular_toon_size,
                   Mat_specular_toon_smooth,
                   Mat_shading_emit,
                   Mat_shading_ambient,
                   Mat_shading_translucency,
                   Mat_shading_use_shadeless,
                   Mat_shading_use_tangent_shading,
                   Mat_shading_use_cubic,
                   Mat_transparency_use_transparency,
                   Mat_transparency_method,
                   Mat_transparency_alpha,
                   Mat_transparency_fresnel,
                   Mat_transparency_specular_alpha,
                   Mat_transparency_fresnel_factor,
                   Mat_transparency_ior,
                   Mat_transparency_filter,
                   Mat_transparency_falloff,
                   Mat_transparency_depth_max,
                   Mat_transparency_depth,
                   Mat_transparency_gloss_factor,
                   Mat_transparency_gloss_threshold,
                   Mat_transparency_gloss_samples,
                   Mat_raytracemirror_use,
                   Mat_raytracemirror_reflect_factor,
                   Mat_raytracemirror_fresnel,
                   Mat_raytracemirror_color_r,
                   Mat_raytracemirror_color_g,
                   Mat_raytracemirror_color_b,
                   Mat_raytracemirror_color_a,
                   Mat_raytracemirror_fresnel_factor,
                   Mat_raytracemirror_depth,
                   Mat_raytracemirror_distance,
                   Mat_raytracemirror_fade_to,
                   Mat_raytracemirror_gloss_factor,
                   Mat_raytracemirror_gloss_threshold,
                   Mat_raytracemirror_gloss_samples,
                   Mat_raytracemirror_gloss_anisotropic,
                   Mat_subsurfacescattering_use,
                   Mat_subsurfacescattering_presets,
                   Mat_subsurfacescattering_ior,
                   Mat_subsurfacescattering_scale,
                   Mat_subsurfacescattering_color_r,
                   Mat_subsurfacescattering_color_g,
                   Mat_subsurfacescattering_color_b,
                   Mat_subsurfacescattering_color_a,
                   Mat_subsurfacescattering_color_factor,
                   Mat_subsurfacescattering_texture_factor,
                   Mat_subsurfacescattering_radius_one ,
                   Mat_subsurfacescattering_radius_two ,
                   Mat_subsurfacescattering_radius_three,
                   Mat_subsurfacescattering_front ,
                   Mat_subsurfacescattering_back ,
                   Mat_subsurfacescattering_error_threshold,
                   Mat_strand_root_size,
                   Mat_strand_tip_size,
                   Mat_strand_size_min,
                   Mat_strand_blender_units,
                   Mat_strand_use_tangent_shading,
                   Mat_strand_shape,
                   Mat_strand_width_fade,
                   Mat_strand_blend_distance,
                   Mat_options_use_raytrace,
                   Mat_options_use_full_oversampling,
                   Mat_options_use_sky,
                   Mat_options_use_mist,
                   Mat_options_invert_z,
                   Mat_options_offset_z,
                   Mat_options_use_face_texture,
                   Mat_options_use_texture_alpha,
                   Mat_options_use_vertex_color_paint,
                   Mat_options_use_vertex_color_light,
                   Mat_options_use_object_color,
                   Mat_options_pass_index,
                   Mat_shadow_use_shadows,
                   Mat_shadow_use_transparent_shadows,
                   Mat_shadow_use_cast_shadows_only,
                   Mat_shadow_shadow_cast_alpha,
                   Mat_shadow_use_only_shadow,
                   Mat_shadow_shadow_only_type,
                   Mat_shadow_use_cast_buffer_shadows,
                   Mat_shadow_shadow_buffer_bias,
                   Mat_shadow_use_ray_shadow_bias,
                   Mat_shadow_shadow_ray_bias,
                   Mat_shadow_use_cast_approximate,
                   Idx_ramp_diffuse,
                   Idx_ramp_specular,
                   Idx_textures]



    #I create a material name data list :
    MY_MATERIAL_DATABASE_NAME = ['Mat_Index',
                                 'Mat_Name',
                                 'Mat_Type',
                                 'Mat_Preview_render_type',
                                 'Mat_diffuse_color_r',
                                 'Mat_diffuse_color_g',
                                 'Mat_diffuse_color_b',
                                 'Mat_diffuse_color_a',
                                 'Mat_diffuse_shader',
                                 'Mat_diffuse_intensity',
                                 'Mat_use_diffuse_ramp',
                                 'Mat_diffuse_roughness',
                                 'Mat_diffuse_toon_size',
                                 'Mat_diffuse_toon_smooth',
                                 'Mat_diffuse_darkness',
                                 'Mat_diffuse_fresnel',
                                 'Mat_diffuse_fresnel_factor',
                                 'Mat_specular_color_r',
                                 'Mat_specular_color_g',
                                 'Mat_specular_color_b',
                                 'Mat_specular_color_a',
                                 'Mat_specular_shader',
                                 'Mat_specular_intensity',
                                 'Mat_specular_ramp',
                                 'Mat_specular_hardness',
                                 'Mat_specular_ior',
                                 'Mat_specular_toon_size',
                                 'Mat_specular_toon_smooth',
                                 'Mat_shading_emit',
                                 'Mat_shading_ambient',
                                 'Mat_shading_translucency',
                                 'Mat_shading_use_shadeless',
                                 'Mat_shading_use_tangent_shading',
                                 'Mat_shading_use_cubic',
                                 'Mat_transparency_use_transparency',
                                 'Mat_transparency_method',
                                 'Mat_transparency_alpha',
                                 'Mat_transparency_fresnel',
                                 'Mat_transparency_specular_alpha',
                                 'Mat_transparency_fresnel_factor',
                                 'Mat_transparency_ior',
                                 'Mat_transparency_filter',
                                 'Mat_transparency_falloff',
                                 'Mat_transparency_depth_max',
                                 'Mat_transparency_depth',
                                 'Mat_transparency_gloss_factor',
                                 'Mat_transparency_gloss_threshold',
                                 'Mat_transparency_gloss_samples',
                                 'Mat_raytracemirror_use',
                                 'Mat_raytracemirror_reflect_factor',
                                 'Mat_raytracemirror_fresnel',
                                 'Mat_raytracemirror_color_r',
                                 'Mat_raytracemirror_color_g',
                                 'Mat_raytracemirror_color_b',
                                 'Mat_raytracemirror_color_a',
                                 'Mat_raytracemirror_fresnel_factor',
                                 'Mat_raytracemirror_depth',
                                 'Mat_raytracemirror_distance',
                                 'Mat_raytracemirror_fade_to',
                                 'Mat_raytracemirror_gloss_factor',
                                 'Mat_raytracemirror_gloss_threshold',
                                 'Mat_raytracemirror_gloss_samples',
                                 'Mat_raytracemirror_gloss_anisotropic',
                                 'Mat_subsurfacescattering_use',
                                 'Mat_subsurfacescattering_presets',
                                 'Mat_subsurfacescattering_ior',
                                 'Mat_subsurfacescattering_scale',
                                 'Mat_subsurfacescattering_color_r',
                                 'Mat_subsurfacescattering_color_g',
                                 'Mat_subsurfacescattering_color_b',
                                 'Mat_subsurfacescattering_color_a',
                                 'Mat_subsurfacescattering_color_factor',
                                 'Mat_subsurfacescattering_texture_factor',
                                 'Mat_subsurfacescattering_radius_one ',
                                 'Mat_subsurfacescattering_radius_two ',
                                 'Mat_subsurfacescattering_radius_three',
                                 'Mat_subsurfacescattering_front ',
                                 'Mat_subsurfacescattering_back ',
                                 'Mat_subsurfacescattering_error_threshold',
                                 'Mat_strand_root_size',
                                 'Mat_strand_tip_size',
                                 'Mat_strand_size_min',
                                 'Mat_strand_blender_units',
                                 'Mat_strand_use_tangent_shading',
                                 'Mat_strand_shape',
                                 'Mat_strand_width_fade',
                                 'Mat_strand_blend_distance',
                                 'Mat_options_use_raytrace',
                                 'Mat_options_use_full_oversampling',
                                 'Mat_options_use_sky',
                                 'Mat_options_use_mist',
                                 'Mat_options_invert_z',
                                 'Mat_options_offset_z',
                                 'Mat_options_use_face_texture',
                                 'Mat_options_use_texture_alpha',
                                 'Mat_options_use_vertex_color_paint',
                                 'Mat_options_use_vertex_color_light',
                                 'Mat_options_use_object_color',
                                 'Mat_options_pass_index',
                                 'Mat_shadow_use_shadows',
                                 'Mat_shadow_use_transparent_shadows',
                                 'Mat_shadow_use_cast_shadows_only',
                                 'Mat_shadow_shadow_cast_alpha',
                                 'Mat_shadow_use_only_shadow',
                                 'Mat_shadow_shadow_only_type',
                                 'Mat_shadow_use_cast_buffer_shadows',
                                 'Mat_shadow_shadow_buffer_bias',
                                 'Mat_shadow_use_ray_shadow_bias',
                                 'Mat_shadow_shadow_ray_bias',
                                 'Mat_shadow_use_cast_approximate',
                                 'Idx_ramp_diffuse',
                                 'Idx_ramp_specular',
                                 'Idx_textures']




    #I create my request here but in first time i debug list Materials values:
    MY_SQL_TABLE_MATERIAL = []
    values = ""
    counter = 0
    for values in MY_MATERIAL:
        if values == False or values == None:
            MY_MATERIAL[counter] = 0
        if values == True:
            MY_MATERIAL[counter] = 1

        bpy_struct_error = str(values)
        if '<bpy_struct' in bpy_struct_error: #Debug
            MY_MATERIAL[counter] = 0

        counter = counter + 1


    values = ""
    for values in MY_MATERIAL_DATABASE_NAME:
        MY_SQL_TABLE_MATERIAL.append(values)



    RequestValues = ""
    RequestValues = ",".join(str(c) for c in MY_SQL_TABLE_MATERIAL)

    RequestNewData = ""
    RequestNewData = ",".join(str(c) for c in MY_MATERIAL)


    #Here i connect database :
    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
    ShadersToolsDatabase.row_factory = sqlite3.Row
    Connexion = ShadersToolsDatabase.cursor()

    #ADD materials records in table:
    Request = "INSERT INTO MATERIALS (" + RequestValues + ") VALUES (" + RequestNewData + ")"
    #print(Request)

    Connexion.execute(Request)
    ShadersToolsDatabase.commit()

    #I close base
    Connexion.close()




    #************************** MY TEXTURES *****************************

    #Textures values :
    tex = bpy.context.active_object.active_material
    textureName = False
    textureNumbers = -1

    for textureName in tex.texture_slots.values():
        textureNumbers = textureNumbers + 1

        if textureName != None :
            MyPrimaryKeys = GetKeysDatabase()
            Tex_Index = MyPrimaryKeys[2]
            Mat_Idx = MyPrimaryKeys[1]-1
            Col_Idx = MyPrimaryKeys[4]-1
            Poi_Idx = MyPrimaryKeys[6]-1

            Tex_Name = "'" + tex.texture_slots[textureNumbers].name + "'"
            Tex_Type = "'" + tex.texture_slots[textureNumbers].texture.type + "'"
            Tex_Preview_type = "'" + tex.preview_render_type + "'"
            Tex_use_preview_alpha = "'" + str(bpy.context.active_object.active_material.texture_slots[textureNumbers].texture.use_preview_alpha )+ "'"
            Tex_Type = "'" + tex.texture_slots[textureNumbers].texture.type + "'"


            Tex_type_blend_progression = ""
            Tex_type_blend_use_flip_axis = ""
            if tex.texture_slots[textureNumbers].texture.type == 'BLEND':
                Tex_type_blend_progression = "'" + tex.texture_slots[textureNumbers].texture.progression + "'"
                Tex_type_blend_use_flip_axis = "'" + tex.texture_slots[textureNumbers].texture.use_flip_axis + "'"


            Tex_type_clouds_cloud_type = "''"
            Tex_type_clouds_noise_type = "''"
            Tex_type_clouds_noise_basis = "''"
            Tex_type_clouds_noise_scale = 0.0
            Tex_type_clouds_nabla = 0.0
            Tex_type_clouds_noise_depth = 0
            if tex.texture_slots[textureNumbers].texture.type == 'CLOUDS':
                Tex_type_clouds_cloud_type = "'" + tex.texture_slots[textureNumbers].texture.cloud_type + "'"
                Tex_type_clouds_noise_type = "'" + tex.texture_slots[textureNumbers].texture.noise_type + "'"
                Tex_type_clouds_noise_basis = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_clouds_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_clouds_nabla = tex.texture_slots[textureNumbers].texture.nabla
                Tex_type_clouds_noise_depth = tex.texture_slots[textureNumbers].texture.noise_depth

            Tex_type_point_density_point_source = "''"
            Tex_type_point_density_radius = 0.0
            Tex_type_point_density_particule_cache_space = "''"
            Tex_type_point_density_falloff = "''"
            Tex_type_point_density_use_falloff_curve = False
            Tex_type_point_density_falloff_soft = 0.0
            Tex_type_point_density_falloff_speed_scale = 0.0
            Tex_type_point_density_speed_scale = 0.0
            Tex_type_point_density_color_source = "''"
            if tex.texture_slots[textureNumbers].texture.type == 'POINT_DENSITY':
                Tex_type_point_density_point_source = "'" + tex.texture_slots[textureNumbers].texture.point_density.point_source + "'"
                Tex_type_point_density_radius = tex.texture_slots[textureNumbers].texture.point_density.radius
                Tex_type_point_density_particule_cache_space = "'" + tex.texture_slots[textureNumbers].texture.point_density.particle_cache_space + "'"
                Tex_type_point_density_falloff = "'" + tex.texture_slots[textureNumbers].texture.point_density.falloff + "'"
                Tex_type_point_density_use_falloff_curve = tex.texture_slots[textureNumbers].texture.point_density.use_falloff_curve
                Tex_type_point_density_falloff_soft = tex.texture_slots[textureNumbers].texture.point_density.falloff_soft
                Tex_type_point_density_falloff_speed_scale = tex.texture_slots[textureNumbers].texture.point_density.falloff_speed_scale
                Tex_type_point_density_speed_scale = tex.texture_slots[textureNumbers].texture.point_density.speed_scale
                Tex_type_point_density_color_source = "'" + tex.texture_slots[textureNumbers].texture.point_density.color_source + "'"


            Tex_type_env_map_source = "''"
            Tex_type_env_map_mapping = "''"
            Tex_type_env_map_clip_start = 0
            Tex_type_env_map_clip_end = 0
            Tex_type_env_map_resolution = 0
            Tex_type_env_map_depth = 0
            Tex_type_env_map_image_file = "'NOT SUPPORTED YET'"
            Tex_type_env_map_zoom = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'ENVIRONMENT_MAP':
                Tex_type_env_map_source = "'" + tex.texture_slots[textureNumbers].texture.environment_map.source + "'"
                Tex_type_env_map_mapping = "'" + tex.texture_slots[textureNumbers].texture.environment_map.mapping + "'"
                Tex_type_env_map_clip_start = tex.texture_slots[textureNumbers].texture.environment_map.clip_start
                Tex_type_env_map_clip_end = tex.texture_slots[textureNumbers].texture.environment_map.clip_end
                Tex_type_env_map_resolution = tex.texture_slots[textureNumbers].texture.environment_map.resolution
                Tex_type_env_map_depth = tex.texture_slots[textureNumbers].texture.environment_map.depth
                Tex_type_env_map_image_file = "'NOT SUPPORTED YET'"
                Tex_type_env_map_zoom = tex.texture_slots[textureNumbers].texture.environment_map.zoom

            Ima_Idx = GetKeysDatabase()
            Ima_Index = Ima_Idx[9]
            Idx_Texture = Ima_Idx[2]
            Tex_ima_name = "''"
            Tex_ima_source = "''"
            Tex_ima_filepath = "''"
            Tex_ima_fileformat = "''"
            Tex_ima_fields = False
            Tex_ima_premultiply = False
            Tex_ima_field_order = "''"
            Tex_ima_generated_type = "''"
            Tex_ima_generated_width = 0
            Tex_ima_generated_height = 0
            Tex_ima_float_buffer = False
            Tex_image_blob = "''"
            if tex.texture_slots[textureNumbers].texture.type == 'IMAGE':
                #CLASSIC IMAGE FILE :
                print(LangageValuesDict['ErrorsMenuError001'])
                print(LangageValuesDict['ErrorsMenuError002'])
                print(LangageValuesDict['ErrorsMenuError003'])
                if tex.texture_slots[textureNumbers].texture.image.source == 'FILE':
                    #I must found Image File Name
                    Tex_ima_filepath = "'" + tex.texture_slots[textureNumbers].texture.image.filepath + "'"
                    IMAGE_FILEPATH = Raw_Image_Path(Tex_ima_filepath)
                    IMAGE_FILENAME = Raw_Image_Name(IMAGE_FILEPATH)

                    if '*Error*' in IMAGE_FILEPATH:
                        ErrorsPathJpg = os.path.join(ErrorsPath, 'error_save.jpg')
                        shutil.copy2(ErrorsPathJpg, os.path.join(AppPath, 'error_save.jpg'))
                        IMAGE_FILEPATH = os.path.join(AppPath, 'error_save.jpg')
                        IMAGE_FILENAME = 'error_save.jpg'
                        print(LangageValuesDict['ErrorsMenuError013'])
                        #print("************************************************************")

                    else:

                        Tex_ima_name = "'" + IMAGE_FILENAME + "'"
                        Tex_ima_source = "'" + tex.texture_slots[textureNumbers].texture.image.source + "'"

                        Tex_ima_fileformat = "'" + tex.texture_slots[textureNumbers].texture.image.file_format + "'"
                        Tex_ima_fields = tex.texture_slots[textureNumbers].texture.image.use_fields
                        Tex_ima_premultiply = tex.texture_slots[textureNumbers].texture.image.use_premultiply
                        Tex_ima_fields_order = tex.texture_slots[textureNumbers].texture.image.field_order





                #GENERATED IMAGE FILE (UV FILE) :
                if tex.texture_slots[textureNumbers].texture.image.source == 'GENERATED':
                    Tex_ima_filepath = "'" + tex.texture_slots[textureNumbers].texture.image.filepath + "'"

                    Tex_ima_name = "'" + tex.texture_slots[textureNumbers].texture.image.name + "'"
                    Tex_ima_source = "'" + tex.texture_slots[textureNumbers].texture.image.source + "'"
                    Tex_ima_fileformat = "'PNG'"
                    Tex_ima_generated_type = "'" + tex.texture_slots[textureNumbers].texture.image.generated_type + "'"
                    Tex_ima_generated_width = tex.texture_slots[textureNumbers].texture.image.generated_width
                    Tex_ima_generated_height = tex.texture_slots[textureNumbers].texture.image.generated_height
                    Tex_ima_float_buffer = tex.texture_slots[textureNumbers].texture.image.use_generated_float


                    save_name = Tex_ima_name.replace("'", '')
                    save_path = os.path.join(AppPath, save_name.replace('.', '') + ".png")


                    if os.path.exists(save_path) :
                        os.remove(save_path)

                    bpy.data.images[save_name].save_render(filepath=save_path)
                    IMAGE_FILEPATH = save_path

                #HERE I CREATE BLOB IMAGE
                if "'" in IMAGE_FILEPATH:
                    IMAGE_FILEPATH = IMAGE_FILEPATH.replace("'", "")

                Source_path = IMAGE_FILEPATH
                if "'" in Source_path:
                    Source_path = Source_path.replace("'", "")

                file = open(Source_path, "rb")
                ImageBlobConversion = file.read()
                file.close()

                Tex_ima_filepath = '"' + IMAGE_FILEPATH + '"'


                #Now I must to update Database IMAGE_UV table:
                #MY  IMAGE UV LIST :
                MY_IMAGE_UV =  [Ima_Index,
                                Idx_Texture,
                                Tex_ima_name,
                                Tex_ima_source,
                                Tex_ima_filepath,
                                Tex_ima_fileformat,
                                Tex_ima_fields,
                                Tex_ima_premultiply,
                                Tex_ima_field_order,
                                Tex_ima_generated_type,
                                Tex_ima_generated_width,
                                Tex_ima_generated_height,
                                Tex_ima_float_buffer,
                                "?"
                               ]


                #MY IMAGE_UV DATA BASE NAME LIST :
                MY_IMAGE_UV_DATABASE_NAME =  ['Ima_Index',
                                          'Idx_Texture',
                                          'Ima_Name',
                                          'Ima_Source',
                                          'Ima_Filepath',
                                          'Ima_Fileformat',
                                          'Ima_Fields',
                                          'Ima_Premultiply',
                                          'Ima_Fields_order',
                                          'Ima_Generated_type',
                                          'Ima_Generated_width',
                                          'Ima_Generated_height',
                                          'Ima_Float_buffer',
                                          'Ima_Blob'
                                         ]



                #I create my request here but in first time i debug list IMAGES/UV values:
                MY_SQL_TABLE_IMAGE_UV = []
                values = ""
                counter = 0
                for values in MY_IMAGE_UV:
                    if values == False or values == None:
                        MY_IMAGE_UV[counter] = 0

                    if values == True:
                        MY_IMAGE_UV[counter] = 1


                    if values == "":
                        MY_IMAGE_UV[counter] = "' '"

                    counter = counter + 1


                values = ""
                for values in MY_IMAGE_UV_DATABASE_NAME:
                    MY_SQL_TABLE_IMAGE_UV.append(values)



                RequestValues = ""
                RequestValues = ",".join(str(c) for c in MY_SQL_TABLE_IMAGE_UV)

                RequestNewData = ""
                RequestNewData = ",".join(str(c) for c in MY_IMAGE_UV)



                #Here i connect database :
                ShadersToolsDatabase = sqlite3.connect(DataBasePath)
                #ShadersToolsDatabase.row_factory = sqlite3.Row
                Connexion = ShadersToolsDatabase.cursor()

                #ADD materials records in table:
                #binary = lite.Binary(Tex_image_blob)
                Request = "INSERT INTO IMAGE_UV (" + RequestValues + ") VALUES (" + RequestNewData + ")"
                #print("Request = " + Request)
                Connexion.execute(Request,(ImageBlobConversion,))
                ShadersToolsDatabase.commit()

                #I close base
                Connexion.close()

                Tex_ima_filepath = Tex_ima_filepath.replace("'", "")

                if os.path.exists(Tex_ima_filepath) :
                   os.remove(Tex_ima_filepath)

                print(LangageValuesDict['ErrorsMenuError004'])
                print("*******************************************************************************")
                # *****************************************************************************************





            Tex_type_magic_depth = 0
            Tex_type_magic_turbulence = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'MAGIC':
                Tex_type_magic_depth = tex.texture_slots[textureNumbers].texture.noise_depth
                Tex_type_magic_turbulence = tex.texture_slots[textureNumbers].texture.turbulence



            Tex_type_marble_marble_type = "''"
            Tex_type_marble_noise_basis_2 = "''"
            Tex_type_marble_noise_type = "''"
            Tex_type_marble_noise_basis = "''"
            Tex_type_marble_noise_scale = 0.0
            Tex_type_marble_noise_depth = 0
            Tex_type_marble_turbulence = 0.0
            Tex_type_marble_nabla = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'MARBLE':
                Tex_type_marble_marble_type = "'" + tex.texture_slots[textureNumbers].texture.marble_type + "'"
                Tex_type_marble_noise_basis_2 = "'" + tex.texture_slots[textureNumbers].texture.noise_basis_2 + "'"
                Tex_type_marble_noise_type = "'" + tex.texture_slots[textureNumbers].texture.noise_type + "'"
                Tex_type_marble_noise_basis = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_marble_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_marble_noise_depth = tex.texture_slots[textureNumbers].texture.noise_depth
                Tex_type_marble_turbulence = tex.texture_slots[textureNumbers].texture.turbulence
                Tex_type_marble_nabla = tex.texture_slots[textureNumbers].texture.nabla


            Tex_type_musgrave_type = "''"
            Tex_type_musgrave_dimension_max = 0.0
            Tex_type_musgrave_lacunarity = 0.0
            Tex_type_musgrave_octaves = 0.0
            Tex_type_musgrave_noise_intensity = 0.0
            Tex_type_musgrave_noise_basis = ""
            Tex_type_musgrave_noise_scale = 0.0
            Tex_type_musgrave_nabla = 0.0
            Tex_type_musgrave_offset = 0.0
            Tex_type_musgrave_gain = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'MUSGRAVE':
                Tex_type_musgrave_type = "'" + tex.texture_slots[textureNumbers].texture.musgrave_type + "'"
                Tex_type_musgrave_dimension_max = tex.texture_slots[textureNumbers].texture.dimension_max
                Tex_type_musgrave_lacunarity = tex.texture_slots[textureNumbers].texture.lacunarity
                Tex_type_musgrave_octaves = tex.texture_slots[textureNumbers].texture.octaves
                Tex_type_musgrave_noise_intensity = tex.texture_slots[textureNumbers].texture.noise_intensity
                Tex_type_musgrave_noise_basis = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_musgrave_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_musgrave_nabla = tex.texture_slots[textureNumbers].texture.nabla
                Tex_type_musgrave_offset = tex.texture_slots[textureNumbers].texture.offset
                Tex_type_musgrave_gain = tex.texture_slots[textureNumbers].texture.gain


            Tex_type_noise_distortion_distortion = "''"
            Tex_type_noise_distortion = "''"
            Tex_type_noise_distortion_texture_distortion = 0.0
            Tex_type_noise_distortion_nabla = 0.0
            Tex_type_noise_distortion_noise_scale = 0.0
            Tex_type_noise_distortion_noise_distortion = "''"
            Tex_type_noise_distortion_basis = "''"
            if tex.texture_slots[textureNumbers].texture.type == 'DISTORTED_NOISE':
                Tex_type_noise_distortion_distortion = tex.texture_slots[textureNumbers].texture.distortion
                Tex_type_noise_distortion = "'" + tex.texture_slots[textureNumbers].texture.noise_distortion + "'"
                Tex_type_noise_distortion_texture_distortion = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_noise_distortion_nabla = tex.texture_slots[textureNumbers].texture.nabla
                Tex_type_noise_distortion_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_noise_distortion_noise_distortion = "'" +  tex.texture_slots[textureNumbers].texture.noise_distortion + "'"
                Tex_type_noise_distortion_basis = "'" +  tex.texture_slots[textureNumbers].texture.noise_basis + "'"


            Tex_type_stucci_type = "''"
            Tex_type_stucci_noise_type = "''"
            Tex_type_stucci_basis = "''"
            Tex_type_stucci_noise_scale = 0.0
            Tex_type_stucci_turbulence = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'STUCCI':
                Tex_type_stucci_type = "'" + tex.texture_slots[textureNumbers].texture.stucci_type + "'"
                Tex_type_stucci_noise_type = "'" + tex.texture_slots[textureNumbers].texture.noise_type + "'"
                Tex_type_stucci_basis = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_stucci_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_stucci_turbulence = tex.texture_slots[textureNumbers].texture.turbulence


            Tex_type_voronoi_distance_metric = "''"
            Tex_type_voronoi_minkovsky_exponent = 0.0
            Tex_type_voronoi_color_mode = "''"
            Tex_type_voronoi_noise_scale = 0.0
            Tex_type_voronoi_nabla = 0.0
            Tex_type_voronoi_weight_1 = 0.0
            Tex_type_voronoi_weight_2 = 0.0
            Tex_type_voronoi_weight_3 = 0.0
            Tex_type_voronoi_weight_4 = 0.0
            Tex_type_voronoi_intensity = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'VORONOI':
                Tex_type_voronoi_distance_metric = "'" + tex.texture_slots[textureNumbers].texture.distance_metric + "'"
                Tex_type_voronoi_minkovsky_exponent = tex.texture_slots[textureNumbers].texture.minkovsky_exponent
                Tex_type_voronoi_color_mode = "'" + tex.texture_slots[textureNumbers].texture.color_mode + "'"
                Tex_type_voronoi_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_voronoi_nabla = tex.texture_slots[textureNumbers].texture.nabla
                Tex_type_voronoi_weight_1 = tex.texture_slots[textureNumbers].texture.weight_1
                Tex_type_voronoi_weight_2 = tex.texture_slots[textureNumbers].texture.weight_2
                Tex_type_voronoi_weight_3 = tex.texture_slots[textureNumbers].texture.weight_3
                Tex_type_voronoi_weight_4 = tex.texture_slots[textureNumbers].texture.weight_4
                Tex_type_voronoi_intensity = tex.texture_slots[textureNumbers].texture.noise_intensity


            Tex_type_voxel_data_file_format = "''"
            Tex_type_voxel_data_source_path = "''"
            Tex_type_voxel_data_use_still_frame = False
            Tex_type_voxel_data_still_frame = "''"
            Tex_type_voxel_data_interpolation = "''"
            Tex_type_voxel_data_extension = "''"
            Tex_type_voxel_data_intensity = 0.0
            Tex_type_voxel_data_resolution_1 = 0.0
            Tex_type_voxel_data_resolution_2 = 0.0
            Tex_type_voxel_data_resoltion_3 = 0.0
            Tex_type_voxel_data_smoke_data_type = "''"
            if tex.texture_slots[textureNumbers].texture.type == 'VOXEL_DATA':
                Tex_type_voxel_data_file_format = "'" + tex.texture_slots[textureNumbers].texture.voxel_data.file_format + "'"
                Tex_type_voxel_data_source_path = "'" + tex.texture_slots[textureNumbers].texture.voxel_data.filepath + "'"
                Tex_type_voxel_data_use_still_frame = tex.texture_slots[textureNumbers].texture.voxel_data.use_still_frame
                Tex_type_voxel_data_still_frame = tex.texture_slots[textureNumbers].texture.voxel_data.still_frame
                Tex_type_voxel_data_interpolation = "'" + tex.texture_slots[textureNumbers].texture.voxel_data.interpolation + "'"
                Tex_type_voxel_data_extension = "'" + tex.texture_slots[textureNumbers].texture.voxel_data.extension + "'"
                Tex_type_voxel_data_intensity = tex.texture_slots[textureNumbers].texture.voxel_data.intensity
                Tex_type_voxel_data_resolution_1 = tex.texture_slots[textureNumbers].texture.voxel_data.resolution[0]
                Tex_type_voxel_data_resolution_2 = tex.texture_slots[textureNumbers].texture.voxel_data.resolution[1]
                Tex_type_voxel_data_resoltion_3 = tex.texture_slots[textureNumbers].texture.voxel_data.resolution[2]
                Tex_type_voxel_data_smoke_data_type ="'" + tex.texture_slots[textureNumbers].texture.voxel_data.smoke_data_type + "'"


            Tex_type_wood_noise_basis_2 = "''"
            Tex_type_wood_wood_type = "''"
            Tex_type_wood_noise_type = "''"
            Tex_type_wood_basis = "''"
            Tex_type_wood_noise_scale = 0.0
            Tex_type_wood_nabla = 0.0
            Tex_type_wood_turbulence = 0.0
            if tex.texture_slots[textureNumbers].texture.type == 'WOOD':
                Tex_type_wood_noise_basis_2 = "'" + tex.texture_slots[textureNumbers].texture.noise_basis_2 + "'"
                Tex_type_wood_wood_type = "'" + tex.texture_slots[textureNumbers].texture.wood_type + "'"
                Tex_type_wood_noise_type = "'" + tex.texture_slots[textureNumbers].texture.noise_type + "'"
                Tex_type_wood_basis = "'" + tex.texture_slots[textureNumbers].texture.noise_basis + "'"
                Tex_type_wood_noise_scale = tex.texture_slots[textureNumbers].texture.noise_scale
                Tex_type_wood_nabla = tex.texture_slots[textureNumbers].texture.nabla
                Tex_type_wood_turbulence = tex.texture_slots[textureNumbers].texture.turbulence


            Tex_colors_use_color_ramp = tex.texture_slots[textureNumbers].texture.use_color_ramp
            Tex_colors_factor_r = tex.texture_slots[textureNumbers].texture.factor_red
            Tex_colors_factor_g = tex.texture_slots[textureNumbers].texture.factor_green
            Tex_colors_factor_b = tex.texture_slots[textureNumbers].texture.factor_blue
            Tex_colors_intensity = tex.texture_slots[textureNumbers].texture.intensity
            Tex_colors_contrast = tex.texture_slots[textureNumbers].texture.contrast
            Tex_colors_saturation = tex.texture_slots[textureNumbers].texture.saturation

            Tex_mapping_texture_coords = "'" + tex.texture_slots[textureNumbers].texture_coords + "'"
            Tex_mapping_mapping = "'" + tex.texture_slots[textureNumbers].mapping + "'"

            Tex_mapping_use_from_dupli = 0
            if tex.texture_slots[textureNumbers].texture_coords == 'ORCO' or tex.texture_slots[textureNumbers].texture_coords == 'UV':
                Tex_mapping_use_from_dupli = tex.texture_slots[textureNumbers].use_from_dupli

            Tex_mapping_use_from_original = 0
            if tex.texture_slots[textureNumbers].texture_coords == 'OBJECT':
                Tex_mapping_use_from_original = tex.texture_slots[textureNumbers].use_from_original

            Tex_mapping_mapping_x = "'" + tex.texture_slots[textureNumbers].mapping_x + "'"
            Tex_mapping_mapping_y = "'" + tex.texture_slots[textureNumbers].mapping_y + "'"
            Tex_mapping_mapping_z = "'" + tex.texture_slots[textureNumbers].mapping_z + "'"
            Tex_mapping_offset_x = tex.texture_slots[textureNumbers].offset[0]
            Tex_mapping_offset_y = tex.texture_slots[textureNumbers].offset[1]
            Tex_mapping_offset_z = tex.texture_slots[textureNumbers].offset[2]
            Tex_mapping_scale_x = tex.texture_slots[textureNumbers].scale[0]
            Tex_mapping_scale_y = tex.texture_slots[textureNumbers].scale[1]
            Tex_mapping_scale_z = tex.texture_slots[textureNumbers].scale[2]

            Tex_influence_use_map_diffuse = tex.texture_slots[textureNumbers].use_map_diffuse
            Tex_influence_use_map_color_diffuse = tex.texture_slots[textureNumbers].use_map_color_diffuse
            Tex_influence_use_map_alpha = tex.texture_slots[textureNumbers].use_map_alpha
            Tex_influence_use_map_translucency = tex.texture_slots[textureNumbers].use_map_translucency
            Tex_influence_use_map_specular = tex.texture_slots[textureNumbers].use_map_specular
            Tex_influence_use_map_color_spec = tex.texture_slots[textureNumbers].use_map_color_spec
            Tex_influence_use_map_map_hardness = tex.texture_slots[textureNumbers].use_map_hardness
            Tex_influence_use_map_ambient = tex.texture_slots[textureNumbers].use_map_ambient
            Tex_influence_use_map_emit = tex.texture_slots[textureNumbers].use_map_emit
            Tex_influence_use_map_mirror = tex.texture_slots[textureNumbers].use_map_mirror
            Tex_influence_use_map_raymir = tex.texture_slots[textureNumbers].use_map_raymir
            Tex_influence_use_map_normal = tex.texture_slots[textureNumbers].use_map_normal
            Tex_influence_use_map_warp = tex.texture_slots[textureNumbers].use_map_warp
            Tex_influence_use_map_displacement = tex.texture_slots[textureNumbers].use_map_displacement
            Tex_influence_use_map_rgb_to_intensity = tex.texture_slots[textureNumbers].use_rgb_to_intensity
            Tex_influence_map_invert = tex.texture_slots[textureNumbers].invert
            Tex_influence_use_stencil = tex.texture_slots[textureNumbers].use_stencil
            Tex_influence_diffuse_factor = tex.texture_slots[textureNumbers].diffuse_factor
            Tex_influence_color_factor = tex.texture_slots[textureNumbers].diffuse_color_factor
            Tex_influence_alpha_factor = tex.texture_slots[textureNumbers].alpha_factor
            Tex_influence_translucency_factor = tex.texture_slots[textureNumbers].translucency_factor
            Tex_influence_specular_factor = tex.texture_slots[textureNumbers].specular_factor
            Tex_influence_specular_color_factor = tex.texture_slots[textureNumbers].specular_color_factor
            Tex_influence_hardness_factor = tex.texture_slots[textureNumbers].hardness_factor
            Tex_influence_ambiant_factor = tex.texture_slots[textureNumbers].ambient_factor
            Tex_influence_emit_factor = tex.texture_slots[textureNumbers].emit_factor
            Tex_influence_mirror_factor = tex.texture_slots[textureNumbers].mirror_factor
            Tex_influence_raymir_factor = tex.texture_slots[textureNumbers].raymir_factor
            Tex_influence_normal_factor = tex.texture_slots[textureNumbers].normal_factor
            Tex_influence_warp_factor = tex.texture_slots[textureNumbers].warp_factor
            Tex_influence_displacement_factor = tex.texture_slots[textureNumbers].displacement_factor
            Tex_influence_default_value = tex.texture_slots[textureNumbers].default_value
            Tex_influence_blend_type = "'" + tex.texture_slots[textureNumbers].blend_type + "'"
            Tex_influence_color_r = tex.texture_slots[textureNumbers].color[0]
            Tex_influence_color_g = tex.texture_slots[textureNumbers].color[1]
            Tex_influence_color_b = tex.texture_slots[textureNumbers].color[2]
            Tex_influence_color_a = 0
            Tex_influence_bump_method = "'" + tex.texture_slots[textureNumbers].bump_method + "'"
            Tex_influence_objectspace = "'" + tex.texture_slots[textureNumbers].bump_objectspace + "'"



            #MY TEXTURE LIST :
            MY_TEXTURE =  [Tex_Index,
                           Tex_Name,
                           Tex_Type,
                           Tex_Preview_type,
                           Tex_use_preview_alpha ,
                           Tex_type_blend_progression,
                           Tex_type_blend_use_flip_axis,
                           Tex_type_clouds_cloud_type,
                           Tex_type_clouds_noise_type,
                           Tex_type_clouds_noise_basis,
                           Tex_type_noise_distortion,
                           Tex_type_env_map_source,
                           Tex_type_env_map_mapping,
                           Tex_type_env_map_clip_start,
                           Tex_type_env_map_clip_end,
                           Tex_type_env_map_resolution,
                           Tex_type_env_map_depth,
                           Tex_type_env_map_image_file,
                           Tex_type_env_map_zoom ,
                           Tex_type_magic_depth,
                           Tex_type_magic_turbulence,
                           Tex_type_marble_marble_type,
                           Tex_type_marble_noise_basis_2,
                           Tex_type_marble_noise_type,
                           Tex_type_marble_noise_basis,
                           Tex_type_marble_noise_scale,
                           Tex_type_marble_noise_depth,
                           Tex_type_marble_turbulence,
                           Tex_type_marble_nabla,
                           Tex_type_musgrave_type,
                           Tex_type_musgrave_dimension_max,
                           Tex_type_musgrave_lacunarity,
                           Tex_type_musgrave_octaves,
                           Tex_type_musgrave_noise_intensity,
                           Tex_type_musgrave_noise_basis,
                           Tex_type_musgrave_noise_scale,
                           Tex_type_musgrave_nabla,
                           Tex_type_musgrave_offset,
                           Tex_type_musgrave_gain,
                           Tex_type_clouds_noise_scale,
                           Tex_type_clouds_nabla,
                           Tex_type_clouds_noise_depth,
                           Tex_type_noise_distortion_distortion,
                           Tex_type_noise_distortion_texture_distortion,
                           Tex_type_noise_distortion_nabla,
                           Tex_type_noise_distortion_noise_scale,
                           Tex_type_point_density_point_source,
                           Tex_type_point_density_radius,
                           Tex_type_point_density_particule_cache_space,
                           Tex_type_point_density_falloff,
                           Tex_type_point_density_use_falloff_curve,
                           Tex_type_point_density_falloff_soft,
                           Tex_type_point_density_falloff_speed_scale,
                           Tex_type_point_density_speed_scale,
                           Tex_type_point_density_color_source,
                           Tex_type_stucci_type,
                           Tex_type_stucci_noise_type,
                           Tex_type_stucci_basis,
                           Tex_type_stucci_noise_scale,
                           Tex_type_stucci_turbulence,
                           Tex_type_voronoi_distance_metric,
                           Tex_type_voronoi_minkovsky_exponent,
                           Tex_type_voronoi_color_mode,
                           Tex_type_voronoi_noise_scale,
                           Tex_type_voronoi_nabla,
                           Tex_type_voronoi_weight_1,
                           Tex_type_voronoi_weight_2,
                           Tex_type_voronoi_weight_3,
                           Tex_type_voronoi_weight_4,
                           Tex_type_voxel_data_file_format,
                           Tex_type_voxel_data_source_path,
                           Tex_type_voxel_data_use_still_frame,
                           Tex_type_voxel_data_still_frame,
                           Tex_type_voxel_data_interpolation ,
                           Tex_type_voxel_data_extension,
                           Tex_type_voxel_data_intensity ,
                           Tex_type_voxel_data_resolution_1,
                           Tex_type_voxel_data_resolution_2,
                           Tex_type_voxel_data_resoltion_3,
                           Tex_type_voxel_data_smoke_data_type,
                           Tex_type_wood_noise_basis_2,
                           Tex_type_wood_wood_type,
                           Tex_type_wood_noise_type,
                           Tex_type_wood_basis,
                           Tex_type_wood_noise_scale,
                           Tex_type_wood_nabla,
                           Tex_type_wood_turbulence,
                           Tex_influence_use_map_diffuse,
                           Tex_influence_use_map_color_diffuse,
                           Tex_influence_use_map_alpha,
                           Tex_influence_use_map_translucency,
                           Tex_influence_use_map_specular,
                           Tex_influence_use_map_color_spec,
                           Tex_influence_use_map_map_hardness,
                           Tex_influence_use_map_ambient,
                           Tex_influence_use_map_emit,
                           Tex_influence_use_map_mirror,
                           Tex_influence_use_map_raymir,
                           Tex_influence_use_map_normal,
                           Tex_influence_use_map_warp,
                           Tex_influence_use_map_displacement,
                           Tex_influence_use_map_rgb_to_intensity,
                           Tex_influence_map_invert ,
                           Tex_influence_use_stencil,
                           Tex_influence_diffuse_factor,
                           Tex_influence_color_factor,
                           Tex_influence_alpha_factor,
                           Tex_influence_translucency_factor ,
                           Tex_influence_specular_factor,
                           Tex_influence_specular_color_factor,
                           Tex_influence_hardness_factor,
                           Tex_influence_ambiant_factor,
                           Tex_influence_emit_factor,
                           Tex_influence_mirror_factor,
                           Tex_influence_raymir_factor,
                           Tex_influence_normal_factor,
                           Tex_influence_warp_factor,
                           Tex_influence_displacement_factor,
                           Tex_influence_default_value,
                           Tex_influence_blend_type,
                           Tex_influence_color_r,
                           Tex_influence_color_g,
                           Tex_influence_color_b,
                           Tex_influence_color_a,
                           Tex_influence_bump_method,
                           Tex_influence_objectspace,
                           Tex_mapping_texture_coords,
                           Tex_mapping_mapping,
                           Tex_mapping_use_from_dupli,
                           Tex_mapping_mapping_x ,
                           Tex_mapping_mapping_y,
                           Tex_mapping_mapping_z,
                           Tex_mapping_offset_x,
                           Tex_mapping_offset_y,
                           Tex_mapping_offset_z,
                           Tex_mapping_scale_x,
                           Tex_mapping_scale_y ,
                           Tex_mapping_scale_z,
                           Tex_colors_use_color_ramp,
                           Tex_colors_factor_r,
                           Tex_colors_factor_g,
                           Tex_colors_factor_b,
                           Tex_colors_intensity,
                           Tex_colors_contrast,
                           Tex_colors_saturation,
                           Mat_Idx,
                           Poi_Idx,
                           Col_Idx,
                           Tex_type_voronoi_intensity,
                           Tex_mapping_use_from_original,
                           Tex_type_noise_distortion_noise_distortion,
                           Tex_type_noise_distortion_basis]





            #MY TEXTURE DATA BASE NAME LIST :
            MY_TEXTURE_DATABASE_NAME =  ['Tex_Index',
                                         'Tex_Name',
                                         'Tex_Type',
                                         'Tex_Preview_type',
                                         'Tex_use_preview_alpha',
                                         'Tex_type_blend_progression',
                                         'Tex_type_blend_use_flip_axis',
                                         'Tex_type_clouds_cloud_type',
                                         'Tex_type_clouds_noise_type',
                                         'Tex_type_clouds_noise_basis',
                                         'Tex_type_noise_distortion',
                                         'Tex_type_env_map_source',
                                         'Tex_type_env_map_mapping',
                                         'Tex_type_env_map_clip_start',
                                         'Tex_type_env_map_clip_end',
                                         'Tex_type_env_map_resolution',
                                         'Tex_type_env_map_depth',
                                         'Tex_type_env_map_image_file',
                                         'Tex_type_env_map_zoom ',
                                         'Tex_type_magic_depth',
                                         'Tex_type_magic_turbulence',
                                         'Tex_type_marble_marble_type',
                                         'Tex_type_marble_noise_basis_2',
                                         'Tex_type_marble_noise_type',
                                         'Tex_type_marble_noise_basis',
                                         'Tex_type_marble_noise_scale',
                                         'Tex_type_marble_noise_depth',
                                         'Tex_type_marble_turbulence',
                                         'Tex_type_marble_nabla',
                                         'Tex_type_musgrave_type',
                                         'Tex_type_musgrave_dimension_max',
                                         'Tex_type_musgrave_lacunarity',
                                         'Tex_type_musgrave_octaves',
                                         'Tex_type_musgrave_noise_intensity',
                                         'Tex_type_musgrave_noise_basis',
                                         'Tex_type_musgrave_noise_scale',
                                         'Tex_type_musgrave_nabla',
                                         'Tex_type_musgrave_offset',
                                         'Tex_type_musgrave_gain',
                                         'Tex_type_clouds_noise_scale',
                                         'Tex_type_clouds_nabla',
                                         'Tex_type_clouds_noise_depth',
                                         'Tex_type_noise_distortion_distortion',
                                         'Tex_type_noise_distortion_texture_distortion',
                                         'Tex_type_noise_distortion_nabla',
                                         'Tex_type_noise_distortion_noise_scale',
                                         'Tex_type_point_density_point_source',
                                         'Tex_type_point_density_radius',
                                         'Tex_type_point_density_particule_cache_space',
                                         'Tex_type_point_density_falloff',
                                         'Tex_type_point_density_use_falloff_curve',
                                         'Tex_type_point_density_falloff_soft',
                                         'Tex_type_point_density_falloff_speed_scale',
                                         'Tex_type_point_density_speed_scale',
                                         'Tex_type_point_density_color_source',
                                         'Tex_type_stucci_type',
                                         'Tex_type_stucci_noise_type',
                                         'Tex_type_stucci_basis',
                                         'Tex_type_stucci_noise_scale',
                                         'Tex_type_stucci_turbulence',
                                         'Tex_type_voronoi_distance_metric',
                                         'Tex_type_voronoi_minkovsky_exponent',
                                         'Tex_type_voronoi_color_mode',
                                         'Tex_type_voronoi_noise_scale',
                                         'Tex_type_voronoi_nabla',
                                         'Tex_type_voronoi_weight_1',
                                         'Tex_type_voronoi_weight_2',
                                         'Tex_type_voronoi_weight_3',
                                         'Tex_type_voronoi_weight_4',
                                         'Tex_type_voxel_data_file_format',
                                         'Tex_type_voxel_data_source_path',
                                         'Tex_type_voxel_data_use_still_frame',
                                         'Tex_type_voxel_data_still_frame',
                                         'Tex_type_voxel_data_interpolation ',
                                         'Tex_type_voxel_data_extension',
                                         'Tex_type_voxel_data_intensity ',
                                         'Tex_type_voxel_data_resolution_1',
                                         'Tex_type_voxel_data_resolution_2',
                                         'Tex_type_voxel_data_resoltion_3',
                                         'Tex_type_voxel_data_smoke_data_type',
                                         'Tex_type_wood_noise_basis_2',
                                         'Tex_type_wood_wood_type',
                                         'Tex_type_wood_noise_type',
                                         'Tex_type_wood_basis',
                                         'Tex_type_wood_noise_scale',
                                         'Tex_type_wood_nabla',
                                         'Tex_type_wood_turbulence',
                                         'Tex_influence_use_map_diffuse',
                                         'Tex_influence_use_map_color_diffuse',
                                         'Tex_influence_use_map_alpha',
                                         'Tex_influence_use_map_translucency',
                                         'Tex_influence_use_map_specular',
                                         'Tex_influence_use_map_color_spec',
                                         'Tex_influence_use_map_map_hardness',
                                         'Tex_influence_use_map_ambient',
                                         'Tex_influence_use_map_emit',
                                         'Tex_influence_use_map_mirror',
                                         'Tex_influence_use_map_raymir',
                                         'Tex_influence_use_map_normal',
                                         'Tex_influence_use_map_warp',
                                         'Tex_influence_use_map_displacement',
                                         'Tex_influence_use_map_rgb_to_intensity',
                                         'Tex_influence_map_invert ',
                                         'Tex_influence_use_stencil',
                                         'Tex_influence_diffuse_factor',
                                         'Tex_influence_color_factor',
                                         'Tex_influence_alpha_factor',
                                         'Tex_influence_translucency_factor ',
                                         'Tex_influence_specular_factor',
                                         'Tex_influence_specular_color_factor',
                                         'Tex_influence_hardness_factor',
                                         'Tex_influence_ambiant_factor',
                                         'Tex_influence_emit_factor',
                                         'Tex_influence_mirror_factor',
                                         'Tex_influence_raymir_factor',
                                         'Tex_influence_normal_factor',
                                         'Tex_influence_warp_factor',
                                         'Tex_influence_displacement_factor',
                                         'Tex_influence_default_value',
                                         'Tex_influence_blend_type',
                                         'Tex_influence_color_r',
                                         'Tex_influence_color_g',
                                         'Tex_influence_color_b',
                                         'Tex_influence_color_a',
                                         'Tex_influence_bump_method',
                                         'Tex_influence_objectspace',
                                         'Tex_mapping_texture_coords',
                                         'Tex_mapping_mapping',
                                         'Tex_mapping_use_from_dupli',
                                         'Tex_mapping_mapping_x ',
                                         'Tex_mapping_mapping_y',
                                         'Tex_mapping_mapping_z',
                                         'Tex_mapping_offset_x',
                                         'Tex_mapping_offset_y',
                                         'Tex_mapping_offset_z',
                                         'Tex_mapping_scale_x',
                                         'Tex_mapping_scale_y ',
                                         'Tex_mapping_scale_z',
                                         'Tex_colors_use_color_ramp',
                                         'Tex_colors_factor_r',
                                         'Tex_colors_factor_g',
                                         'Tex_colors_factor_b',
                                         'Tex_colors_intensity',
                                         'Tex_colors_contrast',
                                         'Tex_colors_saturation',
                                         'Mat_Idx',
                                         'Poi_Idx',
                                         'Col_Idx',
                                         'Tex_type_voronoi_intensity',
                                         'Tex_mapping_use_from_original',
                                         'Tex_type_noise_distortion_noise_distortion',
                                         'Tex_type_noise_distortion_basis']





            #I create my request here but in first time i debug list Textures values:
            MY_SQL_TABLE_TEXTURE = []
            values = ""
            counter = 0
            for values in MY_TEXTURE:
                if values == False or values == None:
                    MY_TEXTURE[counter] = 0

                if values == True:
                    MY_TEXTURE[counter] = 1


                if values == "":
                    MY_TEXTURE[counter] = "' '"

                counter = counter + 1


            values = ""
            for values in MY_TEXTURE_DATABASE_NAME:
                MY_SQL_TABLE_TEXTURE.append(values)



            RequestValues = ""
            RequestValues = ",".join(str(c) for c in MY_SQL_TABLE_TEXTURE)

            RequestNewData = ""
            RequestNewData = ",".join(str(c) for c in MY_TEXTURE)


            #Here i connect database :
            ShadersToolsDatabase = sqlite3.connect(DataBasePath)
            ShadersToolsDatabase.row_factory = sqlite3.Row
            Connexion = ShadersToolsDatabase.cursor()

            #ADD materials records in table:
            Request = "INSERT INTO TEXTURES (" + RequestValues + ") VALUES (" + RequestNewData + ")"
            Connexion.execute(Request)
            ShadersToolsDatabase.commit()

            #I close base
            Connexion.close()




            #************************** MY TEXTURES RAMPS *****************************

            #Here my diffuse ramp :
            ramp = bpy.context.object.active_material.texture_slots[textureNumbers].texture

            #My values:
            Col_Index = 0
            Col_Num_Material = 0
            Col_Num_Texture = 0
            Col_Flip = 0
            Col_Active_color_stop = 0
            Col_Between_color_stop = 0
            Col_Interpolation = ""
            Col_Position = 0.0
            Col_Color_stop_one_r = 0.0
            Col_Color_stop_one_g = 0.0
            Col_Color_stop_one_b = 0.0
            Col_Color_stop_one_a = 0.0
            Col_Color_stop_two_r = 0.0
            Col_Color_stop_two_g = 0.0
            Col_Color_stop_two_b = 0.0
            Col_Color_stop_two_a = 0.0



            #Here my color ramp :
            if ramp.use_color_ramp :

                counter = 0
                loop = 0
                values = ""

                for values in ramp.color_ramp.elements.items():
                    loop = loop + 1


                while counter <= loop-1:
                    Col_Idx = GetKeysDatabase()

                    if counter == 0:
                        #Here i get differentes color bands:
                        Col_Index = Col_Idx[4]
                        Col_Num_Material = Col_Idx[1] - 1
                        Col_Num_Texture = Col_Idx[2] - 1
                        Col_Flip = 0
                        Col_Active_color_stop = 0
                        Col_Between_color_stop = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Interpolation = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Position = ramp.color_ramp.elements[counter].position
                        Col_Color_stop_one_r = ramp.color_ramp.elements[counter].color[0]
                        Col_Color_stop_one_g = ramp.color_ramp.elements[counter].color[1]
                        Col_Color_stop_one_b = ramp.color_ramp.elements[counter].color[2]
                        Col_Color_stop_one_a = ramp.color_ramp.elements[counter].color[3]
                        Col_Color_stop_two_r = 0
                        Col_Color_stop_two_g = 0
                        Col_Color_stop_two_b = 0
                        Col_Color_stop_two_a = 0




                    if counter > 0 and counter < loop - 1 :
                        #Here i get differentes color bands:
                        Col_Index = Col_Idx[4]
                        Col_Num_Material = Col_Idx[1] - 1
                        Col_Num_Texture = Col_Idx[2] - 1
                        Col_Flip = 0
                        Col_Active_color_stop = 0
                        Col_Between_color_stop = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Interpolation = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Position = ramp.color_ramp.elements[counter].position
                        Col_Color_stop_one_r = ramp.color_ramp.elements[counter].color[0]
                        Col_Color_stop_one_g = ramp.color_ramp.elements[counter].color[1]
                        Col_Color_stop_one_b = ramp.color_ramp.elements[counter].color[2]
                        Col_Color_stop_one_a = ramp.color_ramp.elements[counter].color[3]
                        Col_Color_stop_two_r = 0
                        Col_Color_stop_two_g = 0
                        Col_Color_stop_two_b = 0
                        Col_Color_stop_two_a = 0



                    if counter == loop - 1:
                        Col_Index = Col_Idx[4]
                        Col_Num_Material = Col_Idx[1] - 1
                        Col_Num_Texture = Col_Idx[2] - 1
                        Col_Flip = 0
                        Col_Active_color_stop = 0
                        Col_Between_color_stop = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Interpolation = "'" + ramp.color_ramp.interpolation + "'"
                        Col_Position = ramp.color_ramp.elements[counter].position
                        Col_Color_stop_one_r = ramp.color_ramp.elements[counter].color[0]
                        Col_Color_stop_one_g = ramp.color_ramp.elements[counter].color[1]
                        Col_Color_stop_one_b = ramp.color_ramp.elements[counter].color[2]
                        Col_Color_stop_one_a = ramp.color_ramp.elements[counter].color[3]
                        Col_Color_stop_two_r = 0
                        Col_Color_stop_two_g = 0
                        Col_Color_stop_two_b = 0
                        Col_Color_stop_two_a = 0




                    #MY COLOR RAMP LIST :
                    MY_COLOR_RAMP =  [Col_Index,
                                    Col_Num_Material,
                                    Col_Num_Texture,
                                    Col_Flip,
                                    Col_Active_color_stop,
                                    Col_Between_color_stop,
                                    Col_Interpolation,
                                    Col_Position,
                                    Col_Color_stop_one_r,
                                    Col_Color_stop_one_g,
                                    Col_Color_stop_one_b,
                                    Col_Color_stop_one_a,
                                    Col_Color_stop_two_r,
                                    Col_Color_stop_two_g,
                                    Col_Color_stop_two_b,
                                    Col_Color_stop_two_a,
                                   ]


                    #MY COLOR RAMP DATA BASE NAME LIST :
                    MY_COLOR_RAMP_DATABASE_NAME =  ['Col_Index',
                                            'Col_Num_Material',
                                            'Col_Num_Texture',
                                            'Col_Flip',
                                            'Col_Active_color_stop',
                                            'Col_Between_color_stop',
                                            'Col_Interpolation',
                                            'Col_Position',
                                            'Col_Color_stop_one_r',
                                            'Col_Color_stop_one_g',
                                            'Col_Color_stop_one_b',
                                            'Col_Color_stop_one_a',
                                            'Col_Color_stop_two_r',
                                            'Col_Color_stop_two_g',
                                            'Col_Color_stop_two_b',
                                            'Col_Color_stop_two_a',
                                            ]




                    #I create my request here but in first time i debug list Textures values:
                    MY_SQL_RAMP_LIST = []
                    val = ""
                    count = 0
                    for val in MY_COLOR_RAMP:
                        if val == False or val == None:
                            MY_COLOR_RAMP[count] = 0

                        if val == True:
                            MY_COLOR_RAMP[count] = 1


                        if val == "":
                            MY_COLOR_RAMP[count] = "' '"

                        count = count + 1


                    val = ""
                    for val in MY_COLOR_RAMP_DATABASE_NAME:
                        MY_SQL_RAMP_LIST.append(val)



                    RequestValues = ""
                    RequestValues = ",".join(str(c) for c in  MY_SQL_RAMP_LIST)

                    RequestNewData = ""
                    RequestNewData = ",".join(str(c) for c in MY_COLOR_RAMP)


                    #Here i connect database :
                    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
                    ShadersToolsDatabase.row_factory = sqlite3.Row
                    Connexion = ShadersToolsDatabase.cursor()

                    #ADD materials records in table:
                    Request = "INSERT INTO COLORS_RAMP (" + RequestValues + ") VALUES (" + RequestNewData + ")"

                    Connexion.execute(Request)
                    ShadersToolsDatabase.commit()

                    #I close base
                    Connexion.close()

                    counter = counter + 1




            #************************** MY TEXTURES RAMPS *****************************

            #Here my point density ramp :
            ramp = bpy.context.object.active_material.texture_slots[textureNumbers].texture

            #My values:
            Poi_Index = 0
            Poi_Num_Material = 0
            Poi_Num_Texture = 0
            Poi_Flip = 0
            Poi_Active_color_stop = 0
            Poi_Between_color_stop = 0
            Poi_Interpolation = ""
            Poi_Position = 0.0
            Poi_Color_stop_one_r = 0.0
            Poi_Color_stop_one_g = 0.0
            Poi_Color_stop_one_b = 0.0
            Poi_Color_stop_one_a = 0.0
            Poi_Color_stop_two_r = 0.0
            Poi_Color_stop_two_g = 0.0
            Poi_Color_stop_two_b = 0.0
            Poi_Color_stop_two_a = 0.0



            #Here my point density ramp :
            if ramp.type == 'POINT_DENSITY':
              if ramp.point_density.color_source == 'PARTICLE_SPEED' or ramp.point_density.color_source == 'PARTICLE_AGE':

                counter = 0
                loop = 0
                values = ""

                for values in ramp.point_density.color_ramp.elements.items():
                    loop = loop + 1


                while counter <= loop-1:
                    Poi_Idx = GetKeysDatabase()

                    if counter == 0:
                        #Here i get differentes color bands:
                        Poi_Index = Poi_Idx[6]
                        Poi_Num_Material = Poi_Idx[1] - 1
                        Poi_Num_Texture = Poi_Idx[2] - 1
                        Poi_Flip = 0
                        Poi_Active_color_stop = 0
                        Poi_Between_color_stop = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Interpolation = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Position = ramp.point_density.color_ramp.elements[counter].position
                        Poi_Color_stop_one_r = ramp.point_density.color_ramp.elements[counter].color[0]
                        Poi_Color_stop_one_g = ramp.point_density.color_ramp.elements[counter].color[1]
                        Poi_Color_stop_one_b = ramp.point_density.color_ramp.elements[counter].color[2]
                        Poi_Color_stop_one_a = ramp.point_density.color_ramp.elements[counter].color[3]
                        Poi_Color_stop_two_r = 0
                        Poi_Color_stop_two_g = 0
                        Poi_Color_stop_two_b = 0
                        Poi_Color_stop_two_a = 0




                    if counter > 0 and counter < loop - 1 :
                        #Here i get differentes color bands:
                        Poi_Index = Poi_Idx[6]
                        Poi_Num_Material = Poi_Idx[1] - 1
                        Poi_Num_Texture = Poi_Idx[2] - 1
                        Poi_Flip = 0
                        Poi_Active_color_stop = 0
                        Poi_Between_color_stop = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Interpolation = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Position = ramp.point_density.color_ramp.elements[counter].position
                        Poi_Color_stop_one_r = ramp.point_density.color_ramp.elements[counter].color[0]
                        Poi_Color_stop_one_g = ramp.point_density.color_ramp.elements[counter].color[1]
                        Poi_Color_stop_one_b = ramp.point_density.color_ramp.elements[counter].color[2]
                        Poi_Color_stop_one_a = ramp.point_density.color_ramp.elements[counter].color[3]
                        Poi_Color_stop_two_r = 0
                        Poi_Color_stop_two_g = 0
                        Poi_Color_stop_two_b = 0
                        Poi_Color_stop_two_a = 0



                    if counter == loop - 1:
                        Poi_Index = Poi_Idx[6]
                        Poi_Num_Material = Poi_Idx[1] - 1
                        Poi_Num_Texture = Poi_Idx[2] - 1
                        Poi_Flip = 0
                        Poi_Active_color_stop = 0
                        Poi_Between_color_stop = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Interpolation = "'" + ramp.point_density.color_ramp.interpolation + "'"
                        Poi_Position = ramp.point_density.color_ramp.elements[counter].position
                        Poi_Color_stop_one_r = ramp.point_density.color_ramp.elements[counter].color[0]
                        Poi_Color_stop_one_g = ramp.point_density.color_ramp.elements[counter].color[1]
                        Poi_Color_stop_one_b = ramp.point_density.color_ramp.elements[counter].color[2]
                        Poi_Color_stop_one_a = ramp.point_density.color_ramp.elements[counter].color[3]
                        Poi_Color_stop_two_r = 0
                        Poi_Color_stop_two_g = 0
                        Poi_Color_stop_two_b = 0
                        Poi_Color_stop_two_a = 0




                    #MY COLOR RAMP LIST :
                    MY_POINTDENSITY_RAMP =  [Poi_Index,
                                    Poi_Num_Material,
                                    Poi_Num_Texture,
                                    Poi_Flip,
                                    Poi_Active_color_stop,
                                    Poi_Between_color_stop,
                                    Poi_Interpolation,
                                    Poi_Position,
                                    Poi_Color_stop_one_r,
                                    Poi_Color_stop_one_g,
                                    Poi_Color_stop_one_b,
                                    Poi_Color_stop_one_a,
                                    Poi_Color_stop_two_r,
                                    Poi_Color_stop_two_g,
                                    Poi_Color_stop_two_b,
                                    Poi_Color_stop_two_a,
                                   ]


                    #MY DIFFUSE RAMP DATA BASE NAME LIST :
                    MY_POINTDENSITY_RAMP_DATABASE_NAME =  ['Poi_Index',
                                            'Poi_Num_Material',
                                            'Poi_Num_Texture',
                                            'Poi_Flip',
                                            'Poi_Active_color_stop',
                                            'Poi_Between_color_stop',
                                            'Poi_Interpolation',
                                            'Poi_Position',
                                            'Poi_Color_stop_one_r',
                                            'Poi_Color_stop_one_g',
                                            'Poi_Color_stop_one_b',
                                            'Poi_Color_stop_one_a',
                                            'Poi_Color_stop_two_r',
                                            'Poi_Color_stop_two_g',
                                            'Poi_Color_stop_two_b',
                                            'Poi_Color_stop_two_a',
                                            ]




                    #I create my request here but in first time i debug list Textures values:
                    MY_SQL_RAMP_LIST = []
                    val = ""
                    count = 0
                    for val in MY_POINTDENSITY_RAMP:
                        if val == False or val == None:
                            MY_POINTDENSITY_RAMP[count] = 0

                        if val == True:
                            MY_POINTDENSITY_RAMP[count] = 1


                        if val == "":
                            MY_POINTDENSITY_RAMP[count] = "' '"

                        count = count + 1


                    val = ""
                    for val in MY_POINTDENSITY_RAMP_DATABASE_NAME:
                        MY_SQL_RAMP_LIST.append(val)



                    RequestValues = ""
                    RequestValues = ",".join(str(c) for c in  MY_SQL_RAMP_LIST)

                    RequestNewData = ""
                    RequestNewData = ",".join(str(c) for c in MY_POINTDENSITY_RAMP)


                    #Here i connect database :
                    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
                    ShadersToolsDatabase.row_factory = sqlite3.Row
                    Connexion = ShadersToolsDatabase.cursor()

                    #ADD materials records in table:
                    Request = "INSERT INTO POINTDENSITY_RAMP (" + RequestValues + ") VALUES (" + RequestNewData + ")"

                    Connexion.execute(Request)
                    ShadersToolsDatabase.commit()

                    #I close base
                    Connexion.close()

                    counter = counter + 1





            # ***************************************************************************************************************************




















    #************************** MY RAMPS *****************************

    #Here my diffuse ramp :
    ramp = bpy.context.object.active_material

    #My values:
    Dif_Index = 0
    Dif_Num_Material = 0
    Dif_Flip = 0
    Dif_Active_color_stop = 0
    Dif_Between_color_stop = 0
    Dif_Interpolation = ""
    Dif_Position = 0.0
    Dif_Color_stop_one_r = 0.0
    Dif_Color_stop_one_g = 0.0
    Dif_Color_stop_one_b = 0.0
    Dif_Color_stop_one_a = 0.0
    Dif_Color_stop_two_r = 0.0
    Dif_Color_stop_two_g = 0.0
    Dif_Color_stop_two_b = 0.0
    Dif_Color_stop_two_a = 0.0
    Dif_Ramp_input = ""
    Dif_Ramp_blend = ""
    Dif_Ramp_factor = 0.0



    #Here my diffuse ramp :
    if ramp.use_diffuse_ramp :

        counter = 0
        loop = 0
        values = ""

        for values in ramp.diffuse_ramp.elements.items():
            loop = loop + 1


        while counter <= loop-1:
            Dif_Idx = GetKeysDatabase()

            if counter == 0:
                #Here i get differentes color bands:
                Dif_Index = Dif_Idx[5]
                Dif_Num_Material = Dif_Idx[1] -1
                Dif_Flip = 0
                Dif_Active_color_stop = 0
                Dif_Between_color_stop = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Interpolation = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Position = ramp.diffuse_ramp.elements[counter].position
                Dif_Color_stop_one_r = ramp.diffuse_ramp.elements[counter].color[0]
                Dif_Color_stop_one_g = ramp.diffuse_ramp.elements[counter].color[1]
                Dif_Color_stop_one_b = ramp.diffuse_ramp.elements[counter].color[2]
                Dif_Color_stop_one_a = ramp.diffuse_ramp.elements[counter].color[3]
                Dif_Color_stop_two_r = 0
                Dif_Color_stop_two_g = 0
                Dif_Color_stop_two_b = 0
                Dif_Color_stop_two_a = 0
                Dif_Ramp_input = "'" + ramp.diffuse_ramp_input + "'"
                Dif_Ramp_blend = "'" + ramp.diffuse_ramp_blend + "'"
                Dif_Ramp_factor = ramp.diffuse_ramp_factor




            if counter > 0 and counter < loop - 1 :
                #Here i get differentes color bands:
                Dif_Index = Dif_Idx[5]
                Dif_Num_Material = Dif_Idx[1] - 1
                Dif_Flip = 0
                Dif_Active_color_stop = 0
                Dif_Between_color_stop = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Interpolation = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Position = ramp.diffuse_ramp.elements[counter].position
                Dif_Color_stop_one_r = ramp.diffuse_ramp.elements[counter].color[0]
                Dif_Color_stop_one_g = ramp.diffuse_ramp.elements[counter].color[1]
                Dif_Color_stop_one_b = ramp.diffuse_ramp.elements[counter].color[2]
                Dif_Color_stop_one_a = ramp.diffuse_ramp.elements[counter].color[3]
                Dif_Color_stop_two_r = 0
                Dif_Color_stop_two_g = 0
                Dif_Color_stop_two_b = 0
                Dif_Color_stop_two_a = 0
                Dif_Ramp_input = "'" + ramp.diffuse_ramp_input + "'"
                Dif_Ramp_blend = "'" + ramp.diffuse_ramp_blend + "'"
                Dif_Ramp_factor = ramp.diffuse_ramp_factor



            if counter == loop - 1:
                Dif_Index = Dif_Idx[5]
                Dif_Num_Material = Dif_Idx[1] - 1
                Dif_Flip = 0
                Dif_Active_color_stop = 0
                Dif_Between_color_stop = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Interpolation = "'" + ramp.diffuse_ramp.interpolation + "'"
                Dif_Position = ramp.diffuse_ramp.elements[counter].position
                Dif_Color_stop_one_r = ramp.diffuse_ramp.elements[counter].color[0]
                Dif_Color_stop_one_g = ramp.diffuse_ramp.elements[counter].color[1]
                Dif_Color_stop_one_b = ramp.diffuse_ramp.elements[counter].color[2]
                Dif_Color_stop_one_a = ramp.diffuse_ramp.elements[counter].color[3]
                Dif_Color_stop_two_r = 0
                Dif_Color_stop_two_g = 0
                Dif_Color_stop_two_b = 0
                Dif_Color_stop_two_a = 0
                Dif_Ramp_input = "'" + ramp.diffuse_ramp_input + "'"
                Dif_Ramp_blend = "'" + ramp.diffuse_ramp_blend + "'"
                Dif_Ramp_factor = ramp.diffuse_ramp_factor







            #MY DIFFUSE RAMP LIST :
            MY_DIFFUSE_RAMP =  [Dif_Index,
                             Dif_Num_Material,
                             Dif_Flip,
                             Dif_Active_color_stop,
                             Dif_Between_color_stop,
                             Dif_Interpolation,
                             Dif_Position,
                             Dif_Color_stop_one_r,
                             Dif_Color_stop_one_g,
                             Dif_Color_stop_one_b,
                             Dif_Color_stop_one_a,
                             Dif_Color_stop_two_r,
                             Dif_Color_stop_two_g,
                             Dif_Color_stop_two_b,
                             Dif_Color_stop_two_a,
                             Dif_Ramp_input,
                             Dif_Ramp_blend,
                             Dif_Ramp_factor
                            ]


            #MY DIFFUSE RAMP DATA BASE NAME LIST :
            MY_DIFFUSE_RAMP_DATABASE_NAME =  ['Dif_Index',
                                      'Dif_Num_Material',
                                      'Dif_Flip',
                                      'Dif_Active_color_stop',
                                      'Dif_Between_color_stop',
                                      'Dif_Interpolation',
                                      'Dif_Position',
                                      'Dif_Color_stop_one_r',
                                      'Dif_Color_stop_one_g',
                                      'Dif_Color_stop_one_b',
                                      'Dif_Color_stop_one_a',
                                      'Dif_Color_stop_two_r',
                                      'Dif_Color_stop_two_g',
                                      'Dif_Color_stop_two_b',
                                      'Dif_Color_stop_two_a',
                                      'Dif_Ramp_input',
                                      'Dif_Ramp_blend',
                                      'Dif_Ramp_factor'
                                     ]




            #I create my request here but in first time i debug list Textures values:
            MY_SQL_RAMP_LIST = []
            val = ""
            count = 0
            for val in MY_DIFFUSE_RAMP:
                if val == False or val == None:
                    MY_DIFFUSE_RAMP[count] = 0

                if val == True:
                    MY_DIFFUSE_RAMP[count] = 1


                if val == "":
                    MY_DIFFUSE_RAMP[count] = "' '"

                count = count + 1


            val = ""
            for val in MY_DIFFUSE_RAMP_DATABASE_NAME:
                MY_SQL_RAMP_LIST.append(val)



            RequestValues = ""
            RequestValues = ",".join(str(c) for c in  MY_SQL_RAMP_LIST)

            RequestNewData = ""
            RequestNewData = ",".join(str(c) for c in MY_DIFFUSE_RAMP)


            #Here i connect database :
            ShadersToolsDatabase = sqlite3.connect(DataBasePath)
            ShadersToolsDatabase.row_factory = sqlite3.Row
            Connexion = ShadersToolsDatabase.cursor()

            #ADD materials records in table:
            Request = "INSERT INTO DIFFUSE_RAMP (" + RequestValues + ") VALUES (" + RequestNewData + ")"

            Connexion.execute(Request)
            ShadersToolsDatabase.commit()

            #I close base
            Connexion.close()

            counter = counter + 1





    # ***************************************************************************************************************************

    #My values:
    Spe_Index = 0
    Spe_Num_Material = 0
    Spe_Flip = 0
    Spe_Active_color_stop = 0
    Spe_Between_color_stop = 0
    Spe_Interpolation = ""
    Spe_Position = 0.0
    Spe_Color_stop_one_r = 0.0
    Spe_Color_stop_one_g = 0.0
    Spe_Color_stop_one_b = 0.0
    Spe_Color_stop_one_a = 0.0
    Spe_Color_stop_two_r = 0.0
    Spe_Color_stop_two_g = 0.0
    Spe_Color_stop_two_b = 0.0
    Spe_Color_stop_two_a = 0.0
    Spe_Ramp_input = ""
    Spe_Ramp_blend = ""
    Spe_Ramp_factor = 0.0



    #Here my specular ramp :
    if ramp.use_specular_ramp :

        counter = 0
        loop = 0
        values = ""

        for values in ramp.specular_ramp.elements.items():
            loop = loop + 1


        while counter <= loop-1:
            Spe_Idx = GetKeysDatabase()

            if counter == 0:
                #Here i get Speferentes color bands:
                Spe_Index = Spe_Idx[7]
                Spe_Num_Material = Spe_Idx[1] - 1
                Spe_Flip = 0
                Spe_Active_color_stop = 0
                Spe_Between_color_stop = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Interpolation = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Position = ramp.specular_ramp.elements[counter].position
                Spe_Color_stop_one_r = ramp.specular_ramp.elements[counter].color[0]
                Spe_Color_stop_one_g = ramp.specular_ramp.elements[counter].color[1]
                Spe_Color_stop_one_b = ramp.specular_ramp.elements[counter].color[2]
                Spe_Color_stop_one_a = ramp.specular_ramp.elements[counter].color[3]
                Spe_Color_stop_two_r = 0
                Spe_Color_stop_two_g = 0
                Spe_Color_stop_two_b = 0
                Spe_Color_stop_two_a = 0
                Spe_Ramp_input = "'" + ramp.specular_ramp_input + "'"
                Spe_Ramp_blend = "'" + ramp.specular_ramp_blend + "'"
                Spe_Ramp_factor = ramp.specular_ramp_factor




            if counter > 0 and counter < loop - 1 :
                #Here i get Speferentes color bands:
                Spe_Index = Spe_Idx[7]
                Spe_Num_Material = Spe_Idx[1] - 1
                Spe_Flip = 0
                Spe_Active_color_stop = 0
                Spe_Between_color_stop = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Interpolation = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Position = ramp.specular_ramp.elements[counter].position
                Spe_Color_stop_one_r = ramp.specular_ramp.elements[counter].color[0]
                Spe_Color_stop_one_g = ramp.specular_ramp.elements[counter].color[1]
                Spe_Color_stop_one_b = ramp.specular_ramp.elements[counter].color[2]
                Spe_Color_stop_one_a = ramp.specular_ramp.elements[counter].color[3]
                Spe_Color_stop_two_r = 0
                Spe_Color_stop_two_g = 0
                Spe_Color_stop_two_b = 0
                Spe_Color_stop_two_a = 0
                Spe_Ramp_input = "'" + ramp.specular_ramp_input + "'"
                Spe_Ramp_blend = "'" + ramp.specular_ramp_blend + "'"
                Spe_Ramp_factor = ramp.specular_ramp_factor



            if counter == loop - 1:
                Spe_Index = Spe_Idx[7]
                Spe_Num_Material = Spe_Idx[1] - 1
                Spe_Flip = 0
                Spe_Active_color_stop = 0
                Spe_Between_color_stop = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Interpolation = "'" + ramp.specular_ramp.interpolation + "'"
                Spe_Position = ramp.specular_ramp.elements[counter].position
                Spe_Color_stop_one_r = ramp.specular_ramp.elements[counter].color[0]
                Spe_Color_stop_one_g = ramp.specular_ramp.elements[counter].color[1]
                Spe_Color_stop_one_b = ramp.specular_ramp.elements[counter].color[2]
                Spe_Color_stop_one_a = ramp.specular_ramp.elements[counter].color[3]
                Spe_Color_stop_two_r = 0
                Spe_Color_stop_two_g = 0
                Spe_Color_stop_two_b = 0
                Spe_Color_stop_two_a = 0
                Spe_Ramp_input = "'" + ramp.specular_ramp_input + "'"
                Spe_Ramp_blend = "'" + ramp.specular_ramp_blend + "'"
                Spe_Ramp_factor = ramp.specular_ramp_factor







            #MY specular RAMP LIST :
            MY_SPECULAR_RAMP =  [Spe_Index,
                             Spe_Num_Material,
                             Spe_Flip,
                             Spe_Active_color_stop,
                             Spe_Between_color_stop,
                             Spe_Interpolation,
                             Spe_Position,
                             Spe_Color_stop_one_r,
                             Spe_Color_stop_one_g,
                             Spe_Color_stop_one_b,
                             Spe_Color_stop_one_a,
                             Spe_Color_stop_two_r,
                             Spe_Color_stop_two_g,
                             Spe_Color_stop_two_b,
                             Spe_Color_stop_two_a,
                             Spe_Ramp_input,
                             Spe_Ramp_blend,
                             Spe_Ramp_factor
                            ]


            #MY specular RAMP DATA BASE NAME LIST :
            MY_SPECULAR_RAMP_DATABASE_NAME =  ['Spe_Index',
                                      'Spe_Num_Material',
                                      'Spe_Flip',
                                      'Spe_Active_color_stop',
                                      'Spe_Between_color_stop',
                                      'Spe_Interpolation',
                                      'Spe_Position',
                                      'Spe_Color_stop_one_r',
                                      'Spe_Color_stop_one_g',
                                      'Spe_Color_stop_one_b',
                                      'Spe_Color_stop_one_a',
                                      'Spe_Color_stop_two_r',
                                      'Spe_Color_stop_two_g',
                                      'Spe_Color_stop_two_b',
                                      'Spe_Color_stop_two_a',
                                      'Spe_Ramp_input',
                                      'Spe_Ramp_blend',
                                      'Spe_Ramp_factor'
                                     ]




            #I create my request here but in first time i debug list Textures values:
            MY_SQL_RAMP_LIST = []
            val = ""
            count = 0
            for val in MY_SPECULAR_RAMP:
                if val == False or val == None:
                    MY_SPECULAR_RAMP[count] = 0

                if val == True:
                    MY_SPECULAR_RAMP[count] = 1


                if val == "":
                    MY_SPECULAR_RAMP[count] = "' '"

                count = count + 1


            val = ""
            for val in MY_SPECULAR_RAMP_DATABASE_NAME:
                MY_SQL_RAMP_LIST.append(val)



            RequestValues = ""
            RequestValues = ",".join(str(c) for c in  MY_SQL_RAMP_LIST)

            RequestNewData = ""
            RequestNewData = ",".join(str(c) for c in MY_SPECULAR_RAMP)


            #Here i connect database :
            ShadersToolsDatabase = sqlite3.connect(DataBasePath)
            ShadersToolsDatabase.row_factory = sqlite3.Row
            Connexion = ShadersToolsDatabase.cursor()

            #ADD materials records in table:
            Request = "INSERT INTO SPECULAR_RAMP (" + RequestValues + ") VALUES (" + RequestNewData + ")"
            #print(Request)
            Connexion.execute(Request)
            ShadersToolsDatabase.commit()

            #I close base
            Connexion.close()

            counter = counter + 1








































# ************************************************************************************
# *                                     GET PRIMARY KEY                              *
# ************************************************************************************
def GetKeysDatabase():

    #My keys table :
    MY_KEYS = []


    #Here i connect database :
    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
    ShadersToolsDatabase.row_factory = sqlite3.Row
    Connexion = ShadersToolsDatabase.cursor()

    #INFORMATIONS SQLITE Primary Key :
    Connexion.execute("SELECT Inf_Index FROM INFORMATIONS WHERE Inf_Index = (select max(Inf_Index) from INFORMATIONS)")
    ShadersToolsDatabase.commit()


    for value in Connexion:
        MY_KEYS.append(value["Inf_Index"]+1)


    #MATERIALS SQLITE Primary Key :
    Connexion.execute("SELECT Mat_Index FROM MATERIALS WHERE Mat_Index = (select max(Mat_Index) from MATERIALS)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Mat_Index"]+1)


    #TEXTURES SQLITE Primary Key :
    Connexion.execute("SELECT Tex_Index FROM TEXTURES WHERE Tex_Index = (select max(Tex_Index) from TEXTURES)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Tex_Index"]+1)


    #ABOUT SQLITE Primary Key :
    Connexion.execute("SELECT Abo_Index FROM ABOUT WHERE Abo_Index = (select max(Abo_Index) from ABOUT)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Abo_Index"]+1)


    #COLORS_RAMP SQLITE Primary Key :
    Connexion.execute("SELECT Col_Index FROM COLORS_RAMP WHERE Col_Index = (select max(Col_Index) from COLORS_RAMP)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Col_Index"]+1)



    #DIFFUSE_RAMP SQLITE Primary Key :
    Connexion.execute("SELECT Dif_Index FROM DIFFUSE_RAMP WHERE Dif_Index = (select max(Dif_Index) from DIFFUSE_RAMP)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Dif_Index"]+1)


    #POINTDENSITY_RAMP SQLITE Primary Key :
    Connexion.execute("SELECT Poi_Index FROM POINTDENSITY_RAMP WHERE Poi_Index = (select max(Poi_Index) from POINTDENSITY_RAMP)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Poi_Index"]+1)



    #SPECULAR_RAMP SQLITE Primary Key :
    Connexion.execute("SELECT Spe_Index FROM SPECULAR_RAMP WHERE Spe_Index = (select max(Spe_Index) from SPECULAR_RAMP)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Spe_Index"]+1)


    #RENDER SQLITE Primary Key :
    Connexion.execute("SELECT Ren_Index FROM RENDER WHERE Ren_Index = (select max(Ren_Index) from RENDER)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Ren_Index"]+1)

    #IMAGE_UV SQLITE Primary Key :
    Connexion.execute("SELECT Ima_Index FROM IMAGE_UV WHERE Ima_Index = (select max(Ima_Index) from IMAGE_UV)")
    ShadersToolsDatabase.commit()

    for value in Connexion:
        MY_KEYS.append(value["Ima_Index"]+1)



    #I close base
    Connexion.close()



    return MY_KEYS





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
    os.remove( os.path.join(AppPath, Mat_Name + "_" + Inf_Creator + "_preview.jpg"))



    return PreviewFileImageInMemory








# ************************************************************************************
# *                                     UPDATE DATABASE                              *
# ************************************************************************************
def UpdateDatabase(Inf_Creator, Inf_Category, Inf_Description, Inf_Weblink, Inf_Email, Mat_Name):



    #Here i connect database :
    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
    ShadersToolsDatabase.row_factory = sqlite3.Row
    Connexion = ShadersToolsDatabase.cursor()

    #Here I must get primary keys from Database :
    MyPrimaryKeys = GetKeysDatabase()

    #I begin to insert informations NameCreator, Category ... :
    Connexion.execute("INSERT INTO INFORMATIONS VALUES (?, ?, ?, ?, ?, ?, ?)", (MyPrimaryKeys[0], Inf_Creator, Inf_Category, Inf_Description, Inf_Weblink, Inf_Email, MyPrimaryKeys[1]))
    ShadersToolsDatabase.commit()

    #I insert Render Preview in the base :
    value = 0
    if bpy.context.scene.render.use_color_management :
        value = 1

    PreviewImage = TakePreviewRender(Inf_Creator, Mat_Name)

    Connexion.execute("INSERT INTO RENDER VALUES (?, ?, ?, ?)", (MyPrimaryKeys[8], value, PreviewImage, MyPrimaryKeys[0]))
    ShadersToolsDatabase.commit()


    #Here I save all shaders/textures/materials parameters :
    PrepareSqlUpdateSaveRequest(MyPrimaryKeys, Mat_Name)




    Connexion.close()

    return {'FINISHED'}







# ************************************************************************************
# *                                     SEARCH SHADERS                               *
# ************************************************************************************
def SearchShaders(self, context):

    #I must verify if search file not exist :
    if not os.path.exists(os.path.join(TempPath, "searching")) :

        #I create file until user do not cancel or valid choice :
        searchFile = open(os.path.join(TempPath, "searching"), 'w')
        searchFile.close


        #Here I remove all files in the Tempory Folder:
        if os.path.exists(TempPath) :
            files = os.listdir(TempPath)
            for f in files:
                if not os.path.isdir(f) and ".jpg" in f:
                    os.remove(os.path.join(TempPath, f))

        else:
            os.mkdir(TempPath)


        #Here I copy all files in Base Preview Folder:
        files = os.listdir(shaderFolderPath)
        for f in files:
            if not os.path.isdir(f) and ".jpg" in f:
                shutil.copy2(os.path.join(shaderFolderPath, f), os.path.join(TempPath, f))


    #Here I remove all files in Base Preview Folder:
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
            os.remove(os.path.join(shaderFolderPath, f))




    #Now I must copy files corresponding search entry :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
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
        searchFile.close


        #Here I remove all files in the Tempory Folder:
        if os.path.exists(TempPath) :
            files = os.listdir(TempPath)
            for f in files:
                if not os.path.isdir(f) and ".jpg" in f:
                    os.remove(os.path.join(TempPath, f))
        else:
            os.makedirs(TempPath)


        #Here I copy all files in Base Preview Folder:
        files = os.listdir(shaderFolderPath)
        for f in files:
            if not os.path.isdir(f) and ".jpg" in f:
                shutil.copy2(os.path.join(shaderFolderPath, f), os.path.join(TempPath, f))


    #Here I remove all files in Base Preview Folder:
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
            os.remove(os.path.join(shaderFolderPath, f))




    #Now I must copy files corresponding search entry :
    files = os.listdir(TempPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
            if self.History.upper() in f.upper():
                shutil.copy2(os.path.join(TempPath, f), os.path.join(shaderFolderPath, f))




    bpy.ops.file.refresh()









# ************************************************************************************
# *                                        OPEN SHADERS                              *
# ************************************************************************************
class OpenShaders(bpy.types.Operator):
    bl_idname = "object.openshaders"
    bl_label = LangageValuesDict['OpenMenuTitle']
    bl_options = {'REGISTER', 'UNDO'}







    filename = bpy.props.StringProperty(subtype="FILENAME")

    Search = bpy.props.StringProperty(name='', update=SearchShaders)


    History = bpy.props.EnumProperty(

                                     name='',
                                     update=SearchShadersEnum,
                                     items=(('', "---- " +
                                             LangageValuesDict['OpenMenuLabel09'] + " ----", ""),
                                            (HISTORY_FILE[0], HISTORY_FILE[0], ""),
                                            (HISTORY_FILE[1], HISTORY_FILE[1], ""),
                                            (HISTORY_FILE[2], HISTORY_FILE[2], ""),
                                            (HISTORY_FILE[3], HISTORY_FILE[3], ""),
                                            (HISTORY_FILE[4], HISTORY_FILE[4], ""),
                                            (HISTORY_FILE[5], HISTORY_FILE[5], ""),
                                            (HISTORY_FILE[6], HISTORY_FILE[6], ""),
                                            (HISTORY_FILE[7], HISTORY_FILE[7], ""),
                                            (HISTORY_FILE[8], HISTORY_FILE[8], ""),
                                            (HISTORY_FILE[9], HISTORY_FILE[9], ""),
                                            (HISTORY_FILE[10], HISTORY_FILE[10], ""),
                                            (HISTORY_FILE[11], HISTORY_FILE[11], ""),
                                            (HISTORY_FILE[12], HISTORY_FILE[12], ""),
                                            (HISTORY_FILE[13], HISTORY_FILE[13], ""),
                                            (HISTORY_FILE[14], HISTORY_FILE[14], ""),
                                            (HISTORY_FILE[15], HISTORY_FILE[15], ""),
                                            (HISTORY_FILE[16], HISTORY_FILE[16], ""),
                                            (HISTORY_FILE[17], HISTORY_FILE[17], ""),
                                            (HISTORY_FILE[18], HISTORY_FILE[18], ""),
                                            (HISTORY_FILE[19], HISTORY_FILE[19], "")
                                            ),
                                     default= HISTORY_FILE[0]
                                     )









    def draw(self, context):
        layout = self.layout


        row = layout.row(align=True)
        row.label(icon ='NEWFOLDER' ,text=" " + LangageValuesDict['OpenMenuLabel08'] + " : ")
        row = layout.row(align=True)
        row.prop(self, 'Search')

        row = layout.row(align=True)
        row.label(text = 498 * "-")

        row = layout.row(align=True)

        row.label(icon ='MATERIAL', text=LangageValuesDict['OpenMenuLabel09'] + " :")
        row = layout.row(align=True)
        row.prop(self, 'History', text ='')
        row = layout.row(align=True)



    def execute(self, context):
        selectedFile = self.filename.replace('.jpg', '')

        if os.path.exists(os.path.join(TempPath, "searching")) :
            os.remove(os.path.join(TempPath, "searching"))


        #I update history file (in config file):
        #print(os.path.join(AppPath, "history"))
        History_save = []
        if os.path.exists(os.path.join(AppPath, "history")) and selectedFile is not '' and selectedFile is not '\n':
            history = open(os.path.join(AppPath, "history"),'r')
            for l in history:
                History_save.append(l)
            #I remove history path:
            history.close()
            os.remove(os.path.join(AppPath, "history"))

            #I create a new History File:
            history = open(os.path.join(AppPath, "history"),'w')
            history.write('[HISTORY]\n')
            history.write('History1=' + selectedFile + "\n")

            #Now I must to create new structure:
            c = 0
            x = 2
            for values in History_save:
                if c == 1 and values != '' and values != '\n':
                    if x <= 20:
                        values = values.replace('History' + str(x-1), 'History' + str(x))
                        history.write(values)
                        x =  x + 1

                if values == "[HISTORY]" or values == "[HISTORY]\n":
                    c = c + 1

            history.close()

        else:

            if selectedFile is not '' and selectedFile is not '\n':
                history = open(os.path.join(AppPath, "history"),'w')
                history.write('[HISTORY]\n')
                history.write('History1=' + selectedFile + '\n')
                x = 2
                while x <= 20:
                    history.write('History' + str(x) + '=\n')
                    x = x + 1

                history.close()


        ImporterSQL(self.filename)
        bpy.ops.script.python_file_run(filepath=os.path.join(AppPath, "__init__.py"))

        return {'FINISHED'}



    def invoke(self, context, event):


        # IN THIS PART I SEARCH CORRECT VALUES IN THE DATABASE:
        #Here i connect database :
        ShadersToolsDatabase = sqlite3.connect(DataBasePath)
        Connexion = ShadersToolsDatabase.cursor()

        #I begin to select Render Table informations :
        value = ""
        Connexion.execute("SELECT Mat_Index, Ren_Preview_Object FROM RENDER")
        for value in Connexion.fetchall():
            if value[0] is not None:
                if value[0] > 1 and value[1] is not '\n' and value[1] is not '':
                    MY_RENDER_TABLE.append(value)



        #I select Material Table informations :
        value = ""
        Connexion.execute("SELECT Mat_Index, Mat_Name FROM MATERIALS")
        for value in Connexion.fetchall():
            if value[0] > 1 and value[1] is not '\n' and value[1] is not '':
                MY_MATERIAL_TABLE.append(value)





        #I select Information Table informations :
        value = ""
        Connexion.execute("SELECT * FROM INFORMATIONS")
        for value in Connexion.fetchall():
            if value[6] > 1 and value[0] > 1 :
                MY_INFORMATION_TABLE.append(value)

        Connexion.close()


        # NOW I MUST CREATE THUMBNAILS IN THE SHADERS TEMPORY FOLDER:
        value = ""
        value2 = ""
        NameFileJPG = ""
        Name = ""
        Render = ""
        Indice = 0
        c = 0
        x = 0
        val = ""
        val2 = ""

        for value in MY_MATERIAL_TABLE:

            value2 = ""
            NameFileJPG = ""
            c = 0

            for value2 in value:
                if c == 0:
                    Indice = str(value2)
                    x = 0
                    #Search Blob Render image:
                    for val in MY_RENDER_TABLE:
                        for val2 in val:
                            if x == 1:
                                Render = val2
                                x = 0

                            if val2 == value2:
                                x = 1



                else:
                    Name = value2

                c = c + 1

            NameFileJPG = Name + "_Ind_" + Indice + ".jpg"
            NameFileJPG = NameFileJPG.replace('MAT_PRE_', '')
            NameFileJPG = os.path.join(shaderFolderPath, NameFileJPG)
            imageFileJPG = open(NameFileJPG,'wb')
            imageFileJPG.write(Render)
            imageFileJPG.close()




        if os.path.exists(os.path.join(AppPath, "first")) :
            bpy.ops.object.warning('INVOKE_DEFAULT')
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
    bl_idname = "object.credits"
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
    bl_idname = "object.help"
    bl_label = LangageValuesDict['HelpMenuTitle']


    @classmethod
    def poll(cls, context):
        return context.object is not None



    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel01'], icon='HELP')
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel02'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel03'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel04'], icon='NEWFOLDER')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel05'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel06'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel07'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel08'])
        row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel09'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel10'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel11'], icon='MATERIAL')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel12'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel13'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel14'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel15'], icon='SCRIPTWIN')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel16'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel17'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel18'])
        row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel19'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel20'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel21'], icon='BLENDER')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel22'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel23'])
        row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel24'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel25'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel26'], icon='TEXT')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel27'])
        row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel28'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel29'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel30'], icon='QUESTION')
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel31'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['HelpMenuLabel32'])
        row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel33'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel34'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel35'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel36'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel37'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel38'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel39'])
        #row = layout.row(align=True)
        #row.label(LangageValuesDict['HelpMenuLabel40'])
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
    print(LangageValuesDict['ErrorsMenuError001'])
    print(LangageValuesDict['ErrorsMenuError006'])

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

    CopyMatFolder = CopyMatFolder.replace('.blex', '')
    Mat_Name_folder = Mat_Name.replace('.blex', '')

    if not os.path.exists(CopyMatFolder) :
        os.makedirs(CopyMatFolder)

    else:
        c = 1
        while os.path.exists(CopyMatFolder) :
            CopyMatFolder = os.path.join(ImportPath, "ShaderToolsImport", Mat_Name_folder + '_' + str(c))
            c = c + 1

        os.makedirs(CopyMatFolder)

    #Now I can copy Zip Files in new Material Folder:
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f):
            shutil.copy2(os.path.join(ZipPath, f), os.path.join(CopyMatFolder, f))


    #Here I must find .py script:
    script_name = ''
    files = os.listdir(ZipPath)
    for f in files:
        if not os.path.isdir(f) and '.py' in f:
            script_name = f


    if script_name == '':
        print(LangageValuesDict['ErrorsMenuError008'])

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



    print(LangageValuesDict['ErrorsMenuError007'])
    print("*******************************************************")


# ************************************************************************************
# *                                       FIND IMAGE                                 *
# ************************************************************************************
class FindImage(bpy.types.Operator):
    bl_idname = "object.findimage"
    bl_label = LangageValuesDict['FindImageMenuName']


    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'FINISHED'}


    def execute(self, context):
        return {'FINISHED'}







# ************************************************************************************
# *                                           IMPORT                                 *
# ************************************************************************************
class Import(bpy.types.Operator):
    bl_idname = "object.import"
    bl_label = LangageValuesDict['ImportMenuTitle']


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
    bl_idname = "object.export"
    bl_label = LangageValuesDict['ExportMenuTitle']


    DefaultCreator = DefaultCreator.replace('\n', '')

    filename = bpy.props.StringProperty(subtype="FILENAME")
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    #I prepare the window :
    Inf_Creator = bpy.props.StringProperty(name=LangageValuesDict['ExportMenuCreator'], default=DefaultCreator)
    Take_a_preview = BoolProperty(name=LangageValuesDict['ExportMenuTakePreview'], default=False)




    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LangageValuesDict['ExportMenuLabel01'] + ":")
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
    bl_idname = "object.saveconfiguration"
    bl_label = LangageValuesDict['SaveMenuTitle']

    #I normalize values:
    DefaultCreator = DefaultCreator.replace('\n', '')
    DefaultDescription = DefaultDescription.replace('\n', '')
    DefaultWeblink = DefaultWeblink.replace('\n', '')
    DefaultMaterialName = DefaultMaterialName.replace('\n', '')
    DefaultCategory = DefaultCategory.replace('\n', '')
    DefaultEmail = DefaultEmail.replace('\n', '')

    #I prepare the window :
    Inf_Creator = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuCreator'], default=DefaultCreator)
    Inf_Category = bpy.props.EnumProperty(

                                          name=LangageValuesDict['SaveCategoryTitle'],
                                          items=(('', "---- " + LangageValuesDict['SaveCategoryCategoryTitle'] + " ----", ""),
                                                 ('CarPaint', LangageValuesDict['SaveCategoryCarPaint'], ""),
                                                 ('Dirt', LangageValuesDict['SaveCategoryDirt'], ""),
                                                 ('FabricClothes', LangageValuesDict['SaveCategoryFabricClothes'], ""),
                                                 ('Fancy', LangageValuesDict['SaveCategoryFancy'], ""),
                                                 ('FibreFur', LangageValuesDict['SaveCategoryFibreFur'], ""),
                                                 ('Glass', LangageValuesDict['SaveCategoryGlass'], ""),
                                                 ('Halo', LangageValuesDict['SaveCategoryHalo'], ""),
                                                 ('Liquids', LangageValuesDict['SaveCategoryLiquids'], ""),
                                                 ('Metal', LangageValuesDict['SaveCategoryMetal'], ""),
                                                 ('Misc', LangageValuesDict['SaveCategoryMisc'], ""),
                                                 ('Nature', LangageValuesDict['SaveCategoryNature'], ""),
                                                 ('Organic', LangageValuesDict['SaveCategoryOrganic'], ""),
                                                 ('Personal', LangageValuesDict['SaveCategoryPersonal'], ""),
                                                 ('Plastic', LangageValuesDict['SaveCategoryPlastic'], ""),
                                                 ('Sky', LangageValuesDict['SaveCategorySky'], ""),
                                                 ('Space', LangageValuesDict['SaveCategorySpace'], ""),
                                                 ('Stone', LangageValuesDict['SaveCategoryStone'], ""),
                                                 ('Toon', LangageValuesDict['SaveCategoryToon'], ""),
                                                 ('Wall', LangageValuesDict['SaveCategoryWall'], ""),
                                                 ('Water', LangageValuesDict['SaveCategoryWater'], ""),
                                                 ('Wood', LangageValuesDict['SaveCategoryWood'], ""),
                                                 ),
                                          default= DefaultCategory
                                          )


    Inf_Description = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuDescriptionLabel'], default=DefaultDescription)
    Inf_Weblink = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuWebLinkLabel'], default=DefaultWeblink)
    Inf_Email = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuEmailLabel'], default=DefaultEmail)

    if NAME_ACTIVE_MATERIAL :
        Mat_Name = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuName'], default=bpy.context.object.active_material.name)

    else:
        Mat_Name = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuName'], default=DefaultMaterialName)






    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LangageValuesDict['SaveMenuLabel01'] + ":")
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
# *                            UPDATE MATERIAL INFORMATIONS                          *
# ************************************************************************************
def InformationsUpdateInformations(info):

    #Here i connect database :
    ShadersToolsDatabase = sqlite3.connect(DataBasePath)
    Connexion = ShadersToolsDatabase.cursor()

    #I select Information Table informations :
    value = ""
    Connexion.execute("SELECT " + info + " FROM INFORMATIONS")
    for value in Connexion.fetchall():
        #print(value)
        w = 0

    Connexion.close()
    return info



# ************************************************************************************
# *                              UPDATE CONFIGURATION PATH                           *
# ************************************************************************************
def UpdateConfigurationsInformations(DataBasePathFile, Inf_Creator, Inf_Category, Inf_Description, Inf_Weblink, Inf_Email, Mat_Name, Inf_ResolutionX, Inf_ResolutionY):

    #Delete configuration file:
    os.remove(os.path.join(AppPath, "config"))


    #Create a new configuration file:
    config = open(os.path.join(AppPath, "config"),'w')
    config.write(ExportPath + '\n')
    config.write(DataBasePathFile + '\n')
    config.write(Inf_Creator + '\n')
    config.write(Inf_Description + '\n')
    config.write(Inf_Weblink + '\n')
    config.write(Inf_ResolutionX + '\n')
    config.write(Inf_ResolutionY + '\n')

    config.close()

    #bpy.ops.script.python_file_run(filepath=os.path.join(AppPath, "__init__.py"))


# ************************************************************************************
# *                                  UPDATE WARNING                                  *
# ************************************************************************************
class UpdateWarning(bpy.types.Operator):
    bl_idname = "object.warning"
    bl_label = LangageValuesDict['WarningWinTitle']




    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LangageValuesDict['WarningWinLabel01'], icon='RADIO')
        row = layout.row(align=True)
        row.label(LangageValuesDict['WarningWinLabel02'])
        row = layout.row(align=True)
        row.label(LangageValuesDict['WarningWinLabel03'])
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
    bl_idname = "object.configuration"
    bl_label = LangageValuesDict['ConfigurationMenuTitle']

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




    #I prepare the window :
    DataBasePathFile = bpy.props.StringProperty(name=LangageValuesDict['ConfigurationMenuDataBasePath'], default=DataBasePath)
    Inf_Creator = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuCreator'], default=DefaultCreator)

    Inf_Category = bpy.props.EnumProperty(

                                          name=LangageValuesDict['SaveCategoryTitle'],
                                          items=(('', "---- " + LangageValuesDict['SaveCategoryCategoryTitle'] + " ----", ""),
                                                 ('CarPaint', LangageValuesDict['SaveCategoryCarPaint'], ""),
                                                 ('Dirt', LangageValuesDict['SaveCategoryDirt'], ""),
                                                 ('FabricClothes', LangageValuesDict['SaveCategoryFabricClothes'], ""),
                                                 ('Fancy', LangageValuesDict['SaveCategoryFancy'], ""),
                                                 ('FibreFur', LangageValuesDict['SaveCategoryFibreFur'], ""),
                                                 ('Glass', LangageValuesDict['SaveCategoryGlass'], ""),
                                                 ('Halo', LangageValuesDict['SaveCategoryHalo'], ""),
                                                 ('Liquids', LangageValuesDict['SaveCategoryLiquids'], ""),
                                                 ('Metal', LangageValuesDict['SaveCategoryMetal'], ""),
                                                 ('Misc', LangageValuesDict['SaveCategoryMisc'], ""),
                                                 ('Nature', LangageValuesDict['SaveCategoryNature'], ""),
                                                 ('Organic', LangageValuesDict['SaveCategoryOrganic'], ""),
                                                 ('Personal', LangageValuesDict['SaveCategoryPersonal'], ""),
                                                 ('Plastic', LangageValuesDict['SaveCategoryPlastic'], ""),
                                                 ('Sky', LangageValuesDict['SaveCategorySky'], ""),
                                                 ('Space', LangageValuesDict['SaveCategorySpace'], ""),
                                                 ('Stone', LangageValuesDict['SaveCategoryStone'], ""),
                                                 ('Toon', LangageValuesDict['SaveCategoryToon'], ""),
                                                 ('Wall', LangageValuesDict['SaveCategoryWall'], ""),
                                                 ('Water', LangageValuesDict['SaveCategoryWater'], ""),
                                                 ('Wood', LangageValuesDict['SaveCategoryWood'], ""),
                                                 ),
                                          default= DefaultCategory
                                          )


    Inf_Description = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuDescriptionLabel'], default=DefaultDescription)
    Inf_Weblink = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuWebLinkLabel'], default=DefaultWeblink)
    Inf_Email = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuEmailLabel'], default=DefaultEmail)

    if NAME_ACTIVE_MATERIAL :
        Mat_Name = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuName'], default=bpy.context.object.active_material.name)

    else:
        Mat_Name = bpy.props.StringProperty(name=LangageValuesDict['SaveMenuName'], default=DefaultMaterialName)


    Inf_ResolutionX = bpy.props.StringProperty(name=LangageValuesDict['ConfigurationMenuResolutionPreviewX'], default=Resolution_X)
    Inf_ResolutionY = bpy.props.StringProperty(name=LangageValuesDict['ConfigurationMenuResolutionPreviewY'], default=Resolution_Y)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(LangageValuesDict['ConfigurationMenuLabel02'] + ":")
        row = layout.row(align=True)
        row.prop(self, "DataBasePathFile")
        row = layout.row(align=True)
        row = layout.row(align=True)
        row = layout.row(align=True)
        row.label(LangageValuesDict['SaveMenuLabel01'] + ":")
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
        row.label(LangageValuesDict['ConfigurationMenuLabel03'] + ":")
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
        os.remove(os.path.join(AppPath, "config"))

        #Create a new configuration file:
        config = open(os.path.join(AppPath, "config"),'w')
        config.write(AppPath + '\n')
        config.write(ExportPath + '\n')
        config.write(self.DataBasePathFile + '\n')
        config.write(self.Inf_Creator + '\n')
        config.write(self.Inf_Description + '\n')
        config.write(self.Inf_Weblink + '\n')
        config.write(self.Mat_Name + '\n')
        config.write(self.Inf_Category + '\n')
        config.write(self.Inf_Email + '\n')
        config.write(self.Inf_ResolutionX + '\n')
        config.write(self.Inf_ResolutionY + '\n')

        config.close()

        bpy.ops.script.python_file_run(filepath=os.path.join(AppPath, "__init__.py"))





        #UpdateConfigurationsInformations(self.DataBasePathFile, self.Inf_Creator, self.Inf_Category, self.Inf_Description, self.Inf_Weblink, self.Inf_Email, self.Mat_Name)
        #bpy.ops.object.warning('INVOKE_DEFAULT')
        return {'FINISHED'}





# ************************************************************************************
# *                                     CREATE NEW                                   *
# ************************************************************************************
class CreateNew(bpy.types.Operator):
    bl_idname = "object.createnew"
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
class PreconfiguredShadersPanel(bpy.types.Panel):
    bl_label = LangageValuesDict['PanelName']
    bl_idname = "OBJECT_PT_shaders"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"




    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.openshaders", text=LangageValuesDict['ButtonsOpen'], icon="NEWFOLDER" )
        row.operator("object.saveconfiguration", text=LangageValuesDict['ButtonsSave'], icon="MATERIAL" )
        row.operator("object.export", text=LangageValuesDict['ButtonsExport'], icon="SCRIPTWIN" )
        row.operator("object.import", text=LangageValuesDict['ButtonsImport'], icon="SCRIPTWIN" )

        row = layout.row()
        row.operator("object.createnew", text=LangageValuesDict['ButtonsCreate'], icon="BLENDER" )
        row.operator("object.configuration", text=LangageValuesDict['ButtonsConfiguration'], icon="TEXT" )
        row.operator("object.help", text=LangageValuesDict['ButtonsHelp'], icon="HELP")
        row.operator("object.credits", text="Credits", icon="QUESTION")
        row = layout.row()






def register():
    bpy.utils.register_class(SaveCurrentConfiguration)
    bpy.utils.register_class(PreconfiguredShadersPanel)
    bpy.utils.register_class(UpdateWarning)
    bpy.utils.register_class(OpenShaders)
    bpy.utils.register_class(Configuration)
    bpy.utils.register_class(Export)
    bpy.utils.register_class(FindImage)
    bpy.utils.register_class(Import)
    bpy.utils.register_class(Credits)
    bpy.utils.register_class(CreateNew)
    bpy.utils.register_class(Help)


def unregister():
    bpy.utils.unregister_class(SaveCurrentConfiguration)
    bpy.utils.unregister_class(PreconfiguredShadersPanel)
    bpy.utils.unregister_class(UpdateWarning)
    bpy.utils.unregister_class(OpenShaders)
    bpy.utils.unregister_class(Configuration)
    bpy.utils.unregister_class(FindImage)
    bpy.utils.unregister_class(Export)
    bpy.utils.unregister_class(Import)
    bpy.utils.unregister_class(Credits)
    bpy.utils.unregister_class(CreateNew)
    bpy.utils.unregister_class(Help)





# ************************************************************************************
# *                           UPDATE BOOKMARKS INFORMATIONS                          *
# ************************************************************************************

#Create a new configuration file:
#Bookmarks USER
if os.path.exists(BookmarksPathUser) :

    shutil.copy2(BookmarksPathUser, BookmarksPathUser+"_2")
    value = ""
    bookmarks_category = False
    updateInformation = True
    MY_BOOKMARKS_FILE = []


    shaderFolderPath = os.path.join(AppPath, LangageValuesDict['BookmarksMenuName'])
    #I verify Shader tempory File is correcly created:
    if not os.path.exists(shaderFolderPath) :
        os.mkdir(shaderFolderPath)




    #Here I copy bookmarks and i verify if Shader Tempory folder exist:
    bookmarkspathfile = open(BookmarksPathUser,'r')
    for value in bookmarkspathfile:
        MY_BOOKMARKS_FILE.append(value)



        if value=='[Bookmarks]' or value=='[Bookmarks]\n':
            bookmarks_category = True

        if value=='[Recent]' or value=='[Recent]\n':
            bookmarks_category = False


        if bookmarks_category :


            if value in shaderFolderPath or value == shaderFolderPath + "\n":
                #No Upade necessary
                updateInformation = False

    bookmarkspathfile.close()

    #I create new bookmarks file and I active windows warning:
    if updateInformation :
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
            firstFile.close()




#Bookmarks SYSTEM
if os.path.exists(BookmarksPathSystem) :

    shutil.copy2(BookmarksPathSystem, BookmarksPathSystem+"_2")
    value = ""
    bookmarks_category = False
    shaderFolderPath = ""
    updateInformation = True
    MY_BOOKMARKS_FILE = []


    shaderFolderPath = os.path.join(AppPath, LangageValuesDict['BookmarksMenuName'])
    #I verify Shader tempory File is correcly created:
    if not os.path.exists(shaderFolderPath) :
        os.mkdir(shaderFolderPath)



    #Here I copy bookmarks and i verify if Shader Tempory folder exist:
    bookmarkspathfile = open(BookmarksPathSystem,'r')
    for value in bookmarkspathfile:
        MY_BOOKMARKS_FILE.append(value)



        if value=='[Bookmarks]' or value=='[Bookmarks]\n':
            bookmarks_category = True

        if value=='[Recent]' or value=='[Recent]\n':
            bookmarks_category = False


        if bookmarks_category :


            if value in shaderFolderPath or value == shaderFolderPath + "\n":
                #No Upade necessary
                updateInformation = False

    bookmarkspathfile.close()

    #I create new bookmarks file and I active windows warning:
    if updateInformation :
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
            firstFile.close()





#Delete Bookmark Preview Jpg:
if os.path.exists(shaderFolderPath) :
    files = os.listdir(shaderFolderPath)
    for f in files:
        if not os.path.isdir(f) and ".jpg" in f:
            os.remove(os.path.join(shaderFolderPath, f))

        else:
            os.remove(os.path.join(shaderFolderPath, f))












if __name__ == "__main__":
    register()
