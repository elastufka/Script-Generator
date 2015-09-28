#######################################
# list_imparameters.py
# Erica Lastufka 08/20/2015 

#Description: Gets useful parameters for imaging from the OT XML files and writes them to imaging_parameters.txt. Places this file in the /calibrated/ directory of the current project.
#######################################

#######################################
# Usage:
#	execfile("list_parameters.py") 
#           or 
#       import list_parameters as li
#       li.main(project_dict, OT_dict)   
#       (if you already have the dictionaries)

#   In the first instance, the user will have to enter: 
#       Project type (Imaging/Manual)
#       lustre username or directory to create Reduce_XXXX directory in (ex. elastufk or /lustre/naasc/elastufk/Imaging)
#       Paragraph form the SCOPS ticket describing project 
#	ex:
#	Project: 2013.1.00099.S
#	GOUS: uid://A001/X122/X45
#	MOUS: uid://A001/X122/X46
#	SBName: NGC253_a_06_TE
#	SBuid: uid://A001/X122/X33
#	ASDMs: uid://A002/X98124f/X478d
#
# 	OPTIONAL pipeline version to source (ex. /lustre/naasc/pipeline/pipeline_env_r31667_casa422_30986.sh)
# 	location and name of the OT file (ex. /lustre/naasc/elastufk/2013.1.00099.S_v2.aot)
#########################################

#########################################
# functions: 

#	getnum_ms(project_path, alias)
#           returns the number of ms's in the folder

#       getListobs()
#	    gets information from listobs, etc by running casa_stuff.py in CASA

#	getNspw(lines, index)
#	    returns the number of spws and an integer array of their indexes

#	getCell(lines, index)
#	    returns cell size and image size recommended by au.pickCellSize

#	getScienceFields(lines, index)
#	    returns the first and last index of the science fields
    
#	getLines(index, numspws)
#	    returns lines from the listobs that have to do with the spws

#	getSpwInfo(science_root, namespaces, spws)
#	    returns a dictionary containing information on each spw's rest frequency, transition, and number of channels

#	getRestFreq(science_root, namespaces)
#	    returns the representative frequency in Hz 

#	getVelWidth(science_root,namespaces, rfreqHz=False)
#	    converts the bandwidth for sensitivity to velocity units. Returns velocity width, bandwidth for sensitivity and unit

#	getRefFrame(science_root, namespaces)
#	    returns the reference frame of the source

#	genPlotMS(spwinfo, rframe)
#	    returns plotms commands for velocity transformations in line spws

#	mosaicBool(namespaces, projroot, sg)
#	    returns a boolean telling whether the project is a mosaic or not

#	ismosaic(projroot, namespaces, sg, lastfield, firstfield)
#	    returns strings with information about whether a project is a mosaic and the number of pointings.

#	openFile()
#	    opens imaging_parameters.txt in /calibrated/ directory

#	fillInfo(p)
#	    puts the dictionary information in easy-to-use text

#	writeText(param, info)
#	    writes text to file

#	testmain()
#	    tests the program with a predefined dictionary
    
#	main()
#	   runs everything

######################################### 

import subprocess
import glob
import xml.etree.ElementTree as ET
import os
import scipy.constants
import OT_info 
import project_info 
import fill_README

#######################
# get the relevant parameters
#######################

# find if there are multiple ms's 
def getnum_ms(project_type,project_base,project_path, alias):
    if project_type == "Imaging":
        os.chdir(project_path + '/%s-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/calibrated' % alias)
    else:
        os.chdir(project_base + '/Imaging')
    vislist=glob.glob('*.ms.split.cal')
    nms = len(vislist)
    return nms;

def getListobs():
    variables=subprocess.Popen([ "casa"," -c", " /lustre/naasc/elastufk/Python/casa_stuff.py"], shell=False,         stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
    variables.wait()
    stuff = variables.communicate()
    lines = stuff[0].split('\n')
    index = len(lines)-4
    return lines, index

# get number of spws, science fields, and cell size while we're at it.
def getNspw(lines, index):
    nspws = lines[index-1] # stuff in [] one line up from sfields <--- FIX, that doesn't work...
    spws=[]
    for char in nspws:
       if (char !='[' and char !=' ' and char !=']'):
           spws.append(int(char))
    numspws = 1+len(spws)
    #print numspws
    #nspws = range(0,numspws-1)
    return numspws, spws

def getCell(lines, index):
    cell = lines[index+1]
    cellsize = cell[2:cell.find(",")-1]
    imsize = cell[cell.find(",")+2:-1] # what if it's a mosaic?
    return cellsize, imsize

def getScienceFields(lines, index):
    sfields = lines[index]
    while sfields[0] !='[':
        index = index-1
        sfields = lines[index] + sfields # search for starting [ and append until there.... 

    for field in sfields[0:8]:   
        if (field !='[' and field !=' '):
            firstfield=field
            break
    findex =  sfields.find(firstfield) +1
    if (sfields[findex] != ' ' and sfields[findex] != ']'):
        firstfield=firstfield+sfields[findex]

    lastfield = sfields[sfields.rfind(' ')+1:-1]
    if lastfield[0] == '[':
        lastfield=lastfield[1]
    return firstfield, lastfield


# get relevant lines from the text files
def getLines(index, numspws):
    specinfo = []
    listobs=glob.glob('*.listobs.txt')
    for obs in listobs:
        text = open(obs, 'rw+')
        listtext = text.readlines()
        for num, line in enumerate(listtext,0):
            if 'Spectral Windows' in line:
                print line 
                index = num
        specinfo.append(listtext[index:index+numspws+2])
        specinfo.append('\n')
        text.close()
    return specinfo

# spw info 
def getSpwInfo(science_root, namespaces, spws): # let's put stuff into an spw dictionary....
    spwprint = 'You have no continuum-dedicated spws. \n' # default
    spwtype = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:transition', namespaces) # won't work if it's ACA!!!!
    spwrfreq = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:restFrequency', namespaces)
    nchannels = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:effectiveNumberOfChannels', namespaces)
    #skyfreq = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:restFrequency', namespaces)
    spwdict=[]
    for n in spws:
        # get number of channels
        nchan = nchannels[n].text
        if spwtype[n].text == 'continuum': 
            transition = 'continuum'
        elif spwtype[n].text == 'Spec__Scan_': #panic
            spwprint = 'This is a spectral scan ... good luck' + '\n'
        else: 
            transition= spwtype[n].text # it's a line with this transition
        #print spwrfreq[n].text, spwtype[n].text
        spwdict.append({'index': n, 'type': spwtype[n].text, 'nchan': nchan, 'restfreq': spwrfreq[n].text, 'transition': transition})
    #if contspw != []:  
        #spwprint = 'Your continuum spw is/are spw' + contspw + '\n'
    #print spwdict
    return spwdict

# get rest frequency
def getRestFreq(science_root, namespaces):
    rfreq = science_root.find('.//sbl:SchedulingConstraints/sbl:representativeFrequency',namespaces)
    rfrequnit = rfreq.attrib
    if rfrequnit['unit'] == 'GHz':
        rfreqHz = float(rfreq.text)*1e9
    elif rfrequnit['unit'] == 'MHz':
        rfreqHz = float(rfreq.text)*1e6
    return rfreqHz

# get velocity width - restructure that if statement
def getVelWidth(science_root,namespaces, rfreqHz=False):
    rwidth = science_root.find('.//sbl:ScienceParameters/sbl:representativeBandwidth',namespaces)
    rwidthunit = rwidth.attrib
    if rwidthunit['unit'] == 'MHz':
        rwidthHz = float(rwidth.text)*1e6
    elif rwidthunit['unit'] == 'GHz':
        rwidthHz = float(rwidth.text)*1e9
    elif rwidthunit['unit'] == 'KHz':
        rwidthHz = float(rwidth.text)*1e3
    elif rwidthunit['unit'] == 'm/s':
        vwidth = rwidth.text
    elif rwidthunit['unit'] == 'km/s':
        vwidth = rwidth.text

    # convert bandwidth to sensitivity to velocity units if that hasn't already been done
    if (rwidthunit['unit'] != 'm/s' or rwidthunit['unit'] != 'km/s'):
        if rfreqHz !=False:
            vwidth = (scipy.constants.c/rfreqHz)*rwidthHz # m/s
        else: 
            print 'Please specify the rest frequency in Hz'
            vwidth = '1' #not 0 just in case
    return vwidth, rwidthHz, rwidthunit['unit']

# get reference frame
def getRefFrame(science_root, namespaces):
    rframe= science_root.find('.//sbl:FieldSource/sbl:sourceVelocity',namespaces)
    rframe = rframe.attrib['referenceSystem'] 
    return rframe

# generate plotms commands for each line spw to help with picking start and nchan
def genPlotMS(spwinfo, rframe):
    plotcmd = []
    print len(spwinfo)
    for n in range(0,len(spwinfo)):
        if spwinfo[n]['transition'] != 'continuum':
            plotcmd.append("plotms(vis=finalvis, xaxis='velocity', yaxis='amp', transform=T, freqframe='%s', restfreq='%s')" % (rframe, str(float(spwinfo[n]['restfreq'])*1e3)))
    return plotcmd
 
# mosaic? 
def mosaicBool(namespaces, projroot, sg):
    mosaicbool = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:isMosaic',namespaces)
    return mosaicbool[int(sg)].text

def ismosaic(projroot, namespaces, sg, lastfield, firstfield):
    mosaic = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:isMosaic',namespaces)

    if mosaic[int(sg)].text == 'true' :
        isMosaic = ''
        pointings = 'with ' + str(int(lastfield) - int(firstfield)) + ' pointings (fields ' + firstfield + '~' + lastfield + ' ). Use imagermode="mosaic".' # number of pointings - same as number of fields if it's a mosaic I guess
        #coords = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:Rectangle/prj:centre',namespaces) #! what if it's a custom mosaic??
        #! get nearest matching field ID ... from ze listobs?
    else:
        isMosaic = 'not'
        pointings = 'so use imagermode="csclean". \n The science field index is ' + firstfield
    return isMosaic, pointings

#######################
# write to image_parameters.txt
#######################
# go to directory
#if project_path[len(project_path)-1] != '/': 
#    project_path = project_path + '/'

#os.chdir(project_path + '%s-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/calibrated' % alias)
def openFile():
    if os.path.isfile('imaging_parameters.txt') != True:
        os.mknod('imaging_parameters.txt')
#    os.system('rm imaging_parameters.txt')
    param = open('imaging_parameters.txt','rw+')
    return param

def fillInfo(p): #pass the whole dictionary
    info = []
    info.append('Project code: ' + p['project_number'] + '\n')
    info.append('SB name: ' + p['SB_name'] + '\n')
    info.append('PI name: ' + p['PI_name'] + '\n')
    info.append('Project title: ' + p['title'] +'\n \n')

    info.append('You have ' + str(p['nms']) + ' ms with these frequency properties: \n')
    for line in p['specinfo']:
        for a in line:
            info.append(a)  # print the relevant lines from listobs

    #! print science field(s) somewhere
    info.append('This is ' + p['mosaic'] + ' a mosaic ' + p['pointings'] +'\n')
    #info.append('The science field indexes are: ' + sfields + '\n') # print science field(s) somewhere
    info.append('Recommended cell and image sizes are: \n' + p['cellsize'] + '	' + '[' + p['imsize'] + ',' + p['imsize'] + '] \n')

    info.append('\n')
    info.append('Velocity parameters are: '+ '\n')
    info.append('Rest frame: ' +p['rframe'] + '\n')
    info.append('Representative frequency: ' + p['rfreq']+ ' GHz \n')
    info.append('Width for sensitivity: ' + str(p['rwidth']) + ' ' + p['rwidthunit'] + ' or ' + str(p['vwidth']) + ' m/s'+ '\n')  

    info.append('Transitions, number of channels, and rest frequencies (GHz) for spws: '+ '\n')
    
    for n in range(0,len(p['spw_dict'])):
        info.append(p['spw_dict'][n]['transition'] + '      ' + p['spw_dict'][n]['nchan']+ '	'+ p['spw_dict'][n]['restfreq'] + '\n') 

    info.append('\n')
    info.append('Here are some plotms commands to help you find the appropriate start velocity and number of channels: '+ '\n')
    for n in range(0,len(p['plotcmd'])):
        info.append(p['plotcmd'][n]+ '\n')

    info.append('\n')
    info.append('Try to meet the requested line rms of ' + p['rms'] + ' '+ p['rms_unit'])
    return info

def writeText(param, info):
    param.writelines(info)
    param.close()

#######################
'''
def testmain():
    project_dict = {'alias': '2013.1.00099.S.MOUS.uid___A001_X122_X42.SBNAME.Arp220_a_07_TE', 'asdm': ['uid://A002/Xa216e2/X1218'], 'project_type': 'Imaging', 'project_number': '2013.1.00099.S', 'pipeline_path': '/lustre/naasc/pipeline/pipeline_env_r31667_casa422_30986.sh', 'mous_code': 'uid___A001_X122_X42', 'project_path': '/lustre/naasc/elastufk/testscript', 'SB_name': 'Arp220_a_07_TE', 'project_base': '/lustre/naasc/elastufk/testscript/2013.1.00099.S.MOUS.uid___A001_X122_X42.SBNAME.Arp220_a_07_TE-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/', 'number_asdms': 1}

    AOT='/lustre/naasc/elastufk/Imaging/2013.1.00099.S_v2.aot'
    OT_dict = OT_info.getOTinfo(project_dict['SB_name'], AOT=AOT)
    readme_info = fill_README.getInfo(project_dict, OT_dict)
    XMLroots=OT_dict[1]
    science_root = XMLroots['science_root']
    namespaces = XMLroots['namespaces']
    nms = getnum_ms(project_dict['project_path'], project_dict['alias'])
    #print nms
    listobs = getListobs()
    line = listobs[0]
    index = listobs[1]
    #print line, index
    nspws = getNspw(line, index)
    #print nspws
    cell = getCell(line, index)
    #print cell
    scifld = getScienceFields(line, index)
    #print scifld
    specinfo = getLines(index, int(nspws[0]))
    spwinfo = getSpwInfo(science_root, namespaces, nspws[1])
    #print spwinfo
    rfreqHz = getRestFreq(science_root, namespaces)
    #print rfreqHz
    vwidth = getVelWidth(science_root, namespaces, rfreqHz=rfreqHz)
    #print vwidth
    rframe = getRefFrame(science_root, namespaces)
    #print rframe
    #print linefreq
    plotcmd = genPlotMS(spwinfo, rframe)
    #print plotcmd
    sg = OT_dict[0]
    mosaic = ismosaic(XMLroots['proj_root'], namespaces, sg['science_goal'], scifld[0], scifld[1])
    #print mosaic
    # get stuff from readme
    readme_dict = fill_README.getInfo(project_dict, OT_dict)
    # fill dictionary
    parameters = {'project_number': project_dict['project_number'],'SB_name': project_dict['SB_name'],'PI_name': readme_dict['PI_name'],'title': readme_dict['title'],'nms':nms, 'specinfo':specinfo,'mosaic': mosaic[0], 'pointings': mosaic[1], 'scifield0': scifld[0], 'scifield1': scifld[1], 'cellsize': cell[0], 'imsize':cell[1], 'rframe':rframe,  'vwidth':vwidth[0], 'rwidth': vwidth[1], 'rwidthunit': vwidth[2], 'spw_dict': spwinfo, 'plotcmd': plotcmd, 'rms': readme_dict['rms'], 'rms_unit': readme_dict['rms_unit'], 'rfreq':str(float(rfreqHz)*1e-9)}
    print parameters
    param = openFile()
    info = fillInfo(parameters)
    writeText(param, info)

    # remove temp files

    fill_README.cleanup(OT_dict[0]['tempdir'])

testmain()
'''
def main(project_dict=False, OT_dict=False):
    if project_dict == False:
        project_dict = project_info.main()
    if OT_dict == False:
        OT_dict = OT_info.getOTinfo(project_dict['SB_name'])

    readme_info = fill_README.getInfo(project_dict, OT_dict)
    XMLroots=OT_dict[1]
    science_root = XMLroots['science_root']
    namespaces = XMLroots['namespaces']

    nms = getnum_ms(project_dict['project_path'], project_dict['alias'])
    listobs = getListobs()
    line = listobs[0]
    index = listobs[1]
    nspws = getNspw(line, index)
    cell = getCell(line, index)
    scifld = getScienceFields(line, index)
    specinfo = getLines(index, int(nspws[0]))
    spwdict = getSpwInfo(science_root, namespaces, nspws[1])
    rfreqHz = getRestFreq(science_root, namespaces)
    vwidth = getVelWidth(science_root, namespaces, rfreqHz=rfreqHz)
    rframe = getRefFrame(science_root, namespaces)
    plotcmd = genPlotMS(spwinfo, rframe)
    sg = OT_dict[0]
    mosaic = ismosaic(XMLroots['proj_root'], namespaces, sg['science_goal'], scifld[0], scifld[1])

    # get stuff from readme
    readme_dict = fill_README.getInfo(project_dict, OT_dict)

    # fill dictionary
    parameters = {'project_number': project_dict['project_number'],'SB_name': project_dict['SB_name'],'PI_name': readme_dict['PI_name'],'title': readme_dict['title'],'nms':nms, 'specinfo':specinfo,'mosaic': mosaic[0], 'pointings': mosaic[1], 'scifield0': scifld[0], 'scifield1': scifld[1], 'cellsize': cell[0], 'imsize':cell[1], 'rframe':rframe,  'vwidth':vwidth[0], 'rwidth': vwidth[1], 'rwidthunit': vwidth[2], 'spw_dict': spwinfo, 'plotcmd': plotcmd, 'rms': readme_dict['rms'], 'rms_unit': readme_dict['rms_unit'], 'rfreq':str(float(rfreqHz)*1e-9)}
    param = openFile()
    info = fillInfo(parameters) #! re-work this one too
    writeText(param, info)

    # remove temp files
    fill_README.cleanup(OT_dict[0]['tempdir'])   

if __name__ == "__main__":
    main()

