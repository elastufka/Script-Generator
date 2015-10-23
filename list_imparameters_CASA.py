#######################################
# list_imparameters_CASA.py
# Erica Lastufka 09/04/2015 

#Description: Gets useful parameters for imaging from the OT XML files and writes them to imaging_parameters.txt. Places this file in the /calibrated/ directory of the current project. CASA version.
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

#	sourceName(science_root, namespaces)
#	    returns name of the science target

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

import glob
import xml.etree.ElementTree as ET
import os
import scipy.constants
import OT_info 
import project_info_working as project_info 
import fill_README
import IPython

#######################
# get the relevant parameters
#######################

# find if there are multiple ms's 
def getnum_ms(project_type, project_path):
    if project_type == "Imaging":
        os.chdir('%s/sg_ouss_id/group_ouss_id/member_ouss_id/calibrated' % project_path)
    else:
        os.chdir('%s/Imaging' % project_path)
    vislist=glob.glob('*.ms.split.cal')
    if not vislist:
        vislist = glob.glob('calibrated.ms')
    nms = len(vislist)
    return nms

def getNumbers():
    vislist=glob.glob('*.ms.split.cal')
    #from analysisUtils import pickCellSize
    #from analysisUtils import createCasaTool
    #from casa import msmdtool
    #import msmdtool()
    if not vislist:
        vislist=['calibrated.ms'] # in case of a manual reduction that was combined in Combination/calibrated
    #mymsmd=createCasaTool(msmdtool)
    for vis in vislist:
        msmd.open(vis)
        nspws= msmd.spwsforintent(intent=("*TARGET*"))
        sfields = msmd.fieldsforintent(intent=("*TARGET*"), asnames=False)
        msmd.close() 
        cell = au.pickCellSize(vis, spw='', npix=5, intent='OBSERVE_TARGET#ON_SOURCE', imsize=True, maxBaselinePercentile=95, cellstring=True, roundcell=2)
    return nspws,sfields,cell

# spw info 
def getSpwInfo(science_root, namespaces, spws): # let's put stuff into an spw dictionary....
    spwprint = 'You have no continuum-dedicated spws. \n' # default
    #get the right 'SpectralSpec' block...don't want the pointing one! <sbl:name>HCN v=0 J=1-0 Science setup_1</sbl:name>
    spectralspec = science_root.findall('.//sbl:SpectralSpec/', namespaces)

    for n in range(0, len(spectralspec)): # don't want to get the pointing setup instead!
        if 'Science setup' in spectralspec[n].text:
            correlator = spectralspec[n+1]
            nchannels=correlator.findall('sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:effectiveNumberOfChannels', namespaces)
            avg = correlator.findall('sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:spectralAveragingFactor', namespaces) # get the averaging factor
            if nchannels == []:
                nchannels=correlator.findall('sbl:ACABaseBandConfig/sbl:ACASpectralWindow/sbl:effectiveNumberOfChannels', namespaces)
                avg = correlator.findall('sbl:ACABaseBandConfig/sbl:ACASpectralWindow/sbl:spectralAveragingFactor', namespaces)
            break
        #else:
        #    print 'blah'# ? sys.exit etc
    spwtype = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:transition', namespaces) # won't work if it's ACA!!!!
    spwrfreq = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:restFrequency', namespaces)

    if (spwtype == [] and spwrfreq == []):
        spwtype = science_root.findall('.//sbl:SpectralSpec/sbl:ACACorrelatorConfiguration/sbl:ACABaseBandConfig/sbl:ACASpectralWindow/sbl:SpectralLine/sbl:transition', namespaces) 
        spwrfreq = science_root.findall('.//sbl:SpectralSpec/sbl:ACACorrelatorConfiguration/sbl:ACABaseBandConfig/sbl:ACASpectralWindow/sbl:SpectralLine/sbl:restFrequency', namespaces)
    #skyfreq = science_root.findall('.//sbl:SpectralSpec/sbl:BLCorrelatorConfiguration/sbl:BLBaseBandConfig/sbl:BLSpectralWindow/sbl:SpectralLine/sbl:restFrequency', namespaces)
    spwdict=[]

    # if calibrated.ms instead of .ms.split.cal ... data may have been combined before. 
    #os.chdir('../') #hope this doesn't mess anything up....
    if os.path.isdir('calibrated.ms'): 
        print 'WARNING: Your data have been combined into a single ms from multiple executions, resulting in %s spws. Please check the resulting script carefully!' % str(len(spws))
        aa = spwtype
        bb = spwrfreq
        cc = nchannels
        dd = avg
        while len(spwtype) != len(spws): # you have more spws because they're from different executions. 
            spwtype = spwtype + aa
            spwrfreq = spwrfreq + bb
            nchannels = nchannels + cc
            avg = avg + dd
        #os.chdir('Imaging')

    for n in spws:
        # get number of channels
        nchan = str(int(nchannels[n].text)/int(avg[n].text))
        kw = ['continuum','Continuum','cont','Cont']
        for i in range(0,len(kw)):
            if kw[i] in spwtype[n].text: 
                transition = 'continuum'
                break
            elif spwtype[n].text == 'Spec__Scan_': #panic
                spwprint = 'This is a spectral scan ... good luck' + '\n'
                transition = 'Spectral Scan'
            else: 
                transition= spwtype[n].text # it's a line with this transition
        spwdict.append({'index': n, 'type': spwtype[n].text, 'nchan': nchan, 'restfreq': spwrfreq[n].text, 'transition': transition})
        #IPython.embed()
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
    if rframe == 'hel': #bary for helio
        rframe = 'BARY'
    else: 
        rframe = rframe.upper()
    return rframe

# generate plotms commands for each line spw to help with picking start and nchan
def genPlotMS(spwinfo, rframe):
    plotcmd = []
    for n in range(0,len(spwinfo)):
        if spwinfo[n]['transition'] != 'continuum':
            plotcmd.append("plotms(vis=finalvis, xaxis='velocity', yaxis='amp', spw = '%s', transform=T, freqframe='%s',\n        restfreq='%sMHz', avgtime='1e8', avgantenna=T)" % (str(n), rframe, str(float(spwinfo[n]['restfreq'])*1e3)))
    return plotcmd
 
# mosaic? 
def mosaicBool(namespaces, projroot,sg):
    mosaicbool = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:isMosaic',namespaces)
    return mosaicbool[int(sg)].text

def ismosaic(projroot, namespaces, sg,lastfield, firstfield):
    mosaic = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:isMosaic',namespaces)
    if mosaic[int(sg)].text == 'true' :
        isMosaic = ''
        pointings = 'with ' + str(int(firstfield) - int(lastfield)) + ' pointings (fields ' + lastfield + '~' + firstfield + ' ). Use imagermode="mosaic".' # number of pointings - same as number of fields if it's a mosaic I guess
        #coords = projroot.findall('.//prj:ScienceGoal/prj:TargetParameters/prj:Rectangle/prj:centre',namespaces) #! what if it's a custom mosaic??
        #! get nearest matching field ID ... from ze listobs?
    else:
        isMosaic = 'not'
        pointings = 'so use imagermode="csclean". \n The science field index is ' + firstfield
    return isMosaic, pointings

def getPhasecenter(science_root, namespaces):
    #from astropy import units as u
    #from astropy.coordinates import SkyCoord
    # get source coordinates for science field
    sourceLong = science_root.findall('.//sbl:FieldSource/sbl:sourceCoordinates/val:longitude',namespaces)
    sourceLat = science_root.findall('.//sbl:FieldSource/sbl:sourceCoordinates/val:latitude',namespaces)
    system = science_root.findall('.//sbl:FieldSource/sbl:sourceCoordinates',namespaces)
    query = science_root.findall('.//sbl:FieldSource/sbl:isQuery',namespaces) # if false that's the science target ... or name = Primary:

    for n in range(0,len(query)):
        if query[n].text == 'false':
            sourceCoords = [sourceLong[n].text, sourceLat[n].text] 
            coordUnits = [sourceLong[n].attrib['unit'], sourceLat[n].attrib['unit']]
            break

    phasecenter = system[n].attrib['system'] + ' ' + sourceCoords[0] + coordUnits[0] + ' ' + sourceCoords[1] + coordUnits[1]

    return phasecenter
 
def sourceName(science_root, namespaces):
    names = science_root.findall('.//sbl:FieldSource/sbl:sourceName',namespaces)
    query = science_root.findall('.//sbl:FieldSource/sbl:isQuery',namespaces) # if false that's the science target ... or name = Primary:
    for n in range(0,len(names)):
        if query[n].text == 'false':
            sourceName = names[n].text
            break
    return sourceName

#######################
# write to image_parameters.txt
#######################
# go to directory
#if project_path[len(project_path)-1] != '/': 
#    project_path = project_path + '/'

#os.chdir(project_path + '%s-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/calibrated' % alias)
def openFile():
    import stat
    if os.path.isfile('imaging_parameters.txt') != True:
        mode = 0666|stat.S_IRUSR
        os.mknod('imaging_parameters.txt', mode)
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
    info.append('The phasecenter coordinates are: ' + p['phasecenter'])
    #info.append('The science field indexes are: ' + sfields + '\n') # print science field(s) somewhere
    info.append('Recommended cell and image sizes are: \n' + p['cellsize'] + '	' + '[' + p['imsize'] + ',' + p['imsize'] + '] \n')

    info.append('\n')
    info.append('Velocity parameters are: '+ '\n')
    info.append('Rest frame: ' +p['rframe'] + '\n')
    info.append('Representative frequency: ' + p['rfreq']+ ' GHz \n')
    info.append('Width for sensitivity: ' + str(p['rwidth']) + ' ' + p['rwidthunit'] + ' or ' + str(p['vwidth']) + ' m/s'+ '\n')  #fix the unit

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

def testmain():
    print 'testing'
    
    project_dict = {'SB_name': 'NGC6357__a_03_7M',
 'alias_tgz': '2013.1.01391.S.MOUS.uid___A001_X147_X27e.SBNAME.NGC6357__a_03_7M.tgz',
 'asdm': ['uid://A002/X9e0695/X7fd8',
  'uid://A002/X9dcf39/X3484',
  'uid://A002/X9dcf39/X3085'],
 'mous_code': 'uid___A001_X147_X27e',
 'number_asdms': 3,
 'pipeline_path': '/lustre/naasc/pipeline/pipeline_env_r31667_casa422_30986.sh',
 'project_number': '2013.1.01391.S',
 'project_path': '/lustre/naasc/elastufk/Imaging/testscript',
 'project_type': 'Imaging'}
    '''
    project_dict = {'SB_name': 'Arp220_a_07_TE',
  'alias_tgz': 'N/A',
  'asdm': ['N/A'],
  'mous_code': 'N/A',
  'number_asdms': 1,
  'pipeline_path': 'N/A',
  'project_number': '2013.1.00099.S',
  'project_path': '/lustre/naasc/elastufk/testscript/',
  'project_type': 'Imaging'}

    
    OT_dict = [{'AOT': '/lustre/naasc/elastufk/Imaging/2013.1.00099.S_v2.aot',
   'AOTdir': '/lustre/naasc/elastufk/Imaging',
   'AOTfile': '2013.1.00099.S_v2.aot',
   'science_goal': '1',
   'tempdir': '/lustre/naasc/elastufk/Imaging/temp'},
  {'namespaces': {'prj': 'Alma/ObsPrep/ObsProject',
    'prp': 'Alma/ObsPrep/ObsProposal',
    'sbl': 'Alma/ObsPrep/SchedBlock',
    'val': 'Alma/ValueTypes'}, 
   'proj_root': <Element '{Alma/ObsPrep/ObsProject}ObsProject' at 0x3537550>,
   'prop_root': <Element '{Alma/ObsPrep/ObsProposal}ObsProposal' at 0x3104e10>,
   'science_root': <Element '{Alma/ObsPrep/SchedBlock}SchedBlock' at 0x3a6cbd0>}]
    '''
    
    AOT='/lustre/naasc/elastufk/ManualReduction/2013.1.01391.S_v3.aot'
    #AOT='/lustre/naasc/elastufk/Imaging/2013.1.00099.S_v2.aot'
    OT_dict = OT_info.getOTinfo(project_dict['SB_name'], AOTpath=AOT)
    #readme_info = fill_README.getInfo(project_dict, OT_dict)
    XMLroots=OT_dict[1]
    science_root = XMLroots['science_root']
    namespaces = XMLroots['namespaces']


    #listobs = getListobs()
    #line = listobs[0]
    #index = listobs[1]
    #print line, index
    #scifld = getScienceFields(line, index)
    sn = sourceName(science_root, namespaces)
    pc = getPhasecenter(science_root, namespaces)
    print pc
    '''
    nms = getnum_ms(project_dict['project_type'], project_dict['project_path'])
    listobs = getListobs()
    line = listobs[0]
    index = listobs[1]
    #print line, index
    nspws = getNspw(line, index)
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
    '''
def main(project_dict=False, OT_dict=False):
    #if project_dict == False:
    #    project_dict = project_info.main()
    #if OT_dict == False:
    #    OT_dict = OT_info.getOTinfo(project_dict['SB_name'])
 
    dictionaries = project_info.most_info(SBname = 'WISE_220_a_09_TE', project_path = '/lustre/naasc/elastufk/testscript/Reduce_X1bb')
    OT_dict = dictionaries[1]
    project_dict = dictionaries[0]
    #readme_info = fill_README.getInfo(dictionaries[0], OT_dict)
    XMLroots=OT_dict[1]
    science_root = XMLroots['science_root']
    namespaces = XMLroots['namespaces']

    nms = getnum_ms(project_dict['project_type'],project_dict['project_path'])
    listobs = getNumbers()
    specinfo = getLines(index, listobs['nspws'])
    spwinfo = getSpwInfo(science_root, namespaces, listobs['spws'])
    rfreqHz = getRestFreq(science_root, namespaces)
    vwidth = getVelWidth(science_root, namespaces, rfreqHz=rfreqHz)
    rframe = getRefFrame(science_root, namespaces)
    plotcmd = genPlotMS(spwinfo, rframe)
    sg = OT_dict[0]
    mosaic = ismosaic(XMLroots['proj_root'], namespaces, sg['science_goal'], scifld[0], scifld[1])
    sName = sourceName(science_root, namespaces)

    # get stuff from readme
    readme_dict = fill_README.getInfo(dictionaries[0], OT_dict)

    # fill dictionary
    parameters = {'project_number': project_dict['project_number'],'SB_name': project_dict['SB_name'],'PI_name': readme_dict['PI_name'],'title': readme_dict['title'],'nms':nms, 'specinfo':specinfo,'mosaic': mosaic[0], 'pointings': mosaic[1], 'scifield0': listobs['sfields0'], 'scifield1': listobs['sfields1'], 'cellsize': listobs['cell'], 'imsize':listobs['imsize'], 'rframe':rframe,  'vwidth':vwidth[0], 'rwidth': vwidth[1], 'rwidthunit': vwidth[2], 'spw_dict': spwinfo, 'plotcmd': plotcmd, 'rms': readme_dict['rms'], 'rms_unit': readme_dict['rms_unit'], 'rfreq':str(float(rfreqHz)*1e-9), 'phasecenter': pc}
    param = openFile()
    info = fillInfo(parameters) #! re-work this one too
    writeText(param, info)

    # remove temp files
    fill_README.cleanup(OT_dict[0]['tempdir'])   

#if __name__ == "__main__":
#    main()

