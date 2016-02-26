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

######################################### 
if 1 :
    import os
    import sys
    import glob 
    import xml.etree.ElementTree as ET
    import scipy.constants
    import OT_info 
    import project_info
    import fill_README

    if (os.getenv('CASAPATH') is not None): # this is the magic that makes python in CASA happen! could probably trim down so only imports the tasks you need
        from taskinit import *
      
#######################
# get the relevant parameters
#######################

# find if there are multiple ms's 
def getnum_ms(project_type, project_path):
    """returns the number of ms's in the folder"""
    if project_type == "Imaging":
        os.chdir('%s/sg_ouss_id/group_ouss_id/member_ouss_id/calibrated' % project_path)
    else:
        os.chdir('%s/Imaging' % project_path)
    vislist=glob.glob('*.ms.split.cal')
    if not vislist: #shouldn't happen any more
        vislist = glob.glob('calibrated.ms')
    nms = len(vislist)
    if nms == 0:
        sys.exit('%s was not found in %s!' % (vislist, os.getcwd()))
    return nms

def getNumbers():
    """Get number of spws, number of science fields, and recommended cell and image size """
    vislist=glob.glob('*.ms.split.cal')
    from analysisUtils import pickCellSize
    #if not vislist:
    #    vislist=['calibrated.ms'] # in case of a manual reduction that was combined in Combination/calibrated -> this doesn't happen any more
    for vis in vislist:
        try:
            msmd.open(vis)
            nspws= msmd.spwsforintent(intent=("*TARGET*"))
            sfields = msmd.fieldsforintent(intent=("*TARGET*"), asnames=False)
            msmd.close() 
            cell = pickCellSize(vis, spw='', npix=5, intent='OBSERVE_TARGET#ON_SOURCE', imsize=True, maxBaselinePercentile=95, cellstring=True, roundcell=2)
        except RuntimeError:
            sys.exit('%s was not found in %s!' % (vis, os.getcwd())) 
    return nspws,sfields,cell

# spw info 
def getSpwInfo(science_root, namespaces, spws): 
    """Make a dictionary of all information pertaining to an spw"""
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
    if os.path.isdir('calibrated.ms'): # shouldn't happpen any more
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


def getRestFreq(science_root, namespaces):
    """get rest frequency of representative window"""
    rfreq = science_root.find('.//sbl:SchedulingConstraints/sbl:representativeFrequency',namespaces)
    rfrequnit = rfreq.attrib
    if rfrequnit['unit'] == 'GHz':
        rfreqHz = float(rfreq.text)*1e9
    elif rfrequnit['unit'] == 'MHz':
        rfreqHz = float(rfreq.text)*1e6
    return rfreqHz

# get velocity width - restructure that if statement
def getVelWidth(science_root,namespaces, rfreqHz=False):
    """Get requested width for sensitivity in km/s"""
    rwidth = science_root.find('.//sbl:ScienceParameters/sbl:representativeBandwidth',namespaces)
    rwidthunit = rwidth.attrib
    if rwidthunit['unit'] == 'MHz':
        rwidthHz = float(rwidth.text)*1e6
    elif rwidthunit['unit'] == 'GHz':
        rwidthHz = float(rwidth.text)*1e9
    elif rwidthunit['unit'] == 'KHz':
        rwidthHz = float(rwidth.text)*1e3
    elif rwidthunit['unit'] == 'm/s':
        vwidth = rwidth.text*(1e-3) # let's go to km/s
        rwidthunit['unit'] == 'km/s'
    elif rwidthunit['unit'] == 'km/s':
        vwidth = rwidth.text

    # convert bandwidth to sensitivity to velocity units if that hasn't already been done - does this depend on reference frmae?
    if (rwidthunit['unit'] != 'm/s' or rwidthunit['unit'] != 'km/s'):
        if rfreqHz !=False:
            vwidth = (scipy.constants.c/rfreqHz)*rwidthHz*(1e-3) # go to km/s 
        else: 
            print 'Please specify the rest frequency in Hz'
            vwidth = '1' #not 0 just in case
    return vwidth, rwidthHz, rwidthunit['unit']

def getRefFrame(science_root, namespaces):
    """ get reference frame"""
    query = science_root.findall('.//sbl:FieldSource/sbl:isQuery',namespaces)
    sv = science_root.findall('.//sbl:FieldSource/sbl:sourceVelocity',namespaces)
    for n in range(0,len(query)):
        if query[n].text == 'false':
            rframe = sv[n].attrib['referenceSystem']
            break

    if rframe == 'hel': #bary for helio
        rframe = 'BARY'
    elif rframe == 'bar':
        rframe = 'BARY'
    else: 
        rframe = rframe.upper()
    return rframe

# if the ms is combined, have to modify the spw argument
# maybe generate these in the script generator instead
def genPlotMS(spwinfo, rframe, spw):
    """generate plotms commands for each line spw to help with picking start and nchan """
    for n in range(0,len(spwinfo)):
        if spwinfo['transition'] != 'continuum':
        #if not spw: # do we actually need this? if generating the commands in sg.line_image()
        #    spw = str(n)
            plotcmd = "plotms(vis=linevis, xaxis='velocity', yaxis='amp', spw = '%s', transform=T, freqframe='%s',\n        restfreq='%sMHz', avgtime='1e8', avgantenna=T)" % (spw, rframe, str(float(spwinfo['restfreq'])*1e3))

    return plotcmd

# yet another attempt at getting a reliable mosaic indicator .... seems like the best thing to do is count the pointings, since ismosaic is always true
def mosaicBool(namespaces, science_root, sourceName): 
    """Returns a boolean value that tells you if it is a mosaic or not"""  
    query = science_root.findall('.//sbl:FieldSource/sbl:isQuery',namespaces) # if false that's the science target 
    pattern = science_root.findall('.//sbl:FieldSource/sbl:PointingPattern',namespaces)
    for n in range(0,len(query)):
        if query[n].text == 'false':
            #get the # of pointings 
            pointings=pattern[n].findall('sbl:phaseCenterCoordinates',namespaces)
            npointings=len(pointings)
            break 
        else: 
            npointings=0
    if npointings > 1:
        mosaicbool = 'true'
    elif npointings == 0:
        print "Couldn't find information about the number of pointings so assuming it's just 1"
        #error, default to single pointing
    else:
        mosaicbool = 'false'
    return mosaicbool

def ismosaic(projroot, namespaces, sg,lastfield, firstfield):
    """Old menthod for finding if it is a mosaic ... not used by script generator"""
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
    """Get the phase center of a mosaic"""
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
 
def sourceName(science_root, namespaces, SB_name):
    """Get the name of the source. Defaults to SB name if no source name found."""
    sourcenames = science_root.findall('.//sbl:FieldSource/sbl:sourceName',namespaces)
    name = science_root.findall('.//sbl:FieldSource/sbl:name',namespaces) # if false that's the science target ... or name = Primary:
    for n in range(0,len(sourcenames)):
        if sourcenames[n].text in SB_name:
            sourceName = sourcenames[n].text
            break
        elif name[n].text == 'Primary:':
            sourceName = sourcenames[n].text
            break
    try:
        sourceName
    except NameError:
        print 'source name could not be found! Will use the SB name instead.'
        sourceName = SB_name
    return sourceName

#######################
# write to image_parameters.txt
#######################

def openFile():
    """For writing list_imparameters.txt. Not used any more since the script generator is better."""
    import stat
    if os.path.isfile('imaging_parameters.txt') != True:
        mode = 0666|stat.S_IRUSR
        os.mknod('imaging_parameters.txt', mode)
#    os.system('rm imaging_parameters.txt')
    param = open('imaging_parameters.txt','rw+')
    return param

def fillInfo(p): #pass the whole dictionary
    """For writing list_imparameters.txt. Not used any more since the script generator is better."""
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
    """For writing list_imparameters.txt. Not used any more since the script generator is better."""
    param.writelines(info)
    param.close()

#######################

def main(project_dict=False, OT_dict=False):
    """For writing list_imparameters.txt. Not used any more since the script generator is better."""
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
    stuff=getNumbers()
    nspws = stuff[0]
    scifld=stuff[1]
    cell = stuff[2]
    spwinfo = getSpwInfo(science_root, namespaces, nspws)
    rfreqHz = getRestFreq(science_root, namespaces)
    vwidth = getVelWidth(science_root, namespaces, rfreqHz=rfreqHz)
    rframe = getRefFrame(science_root, namespaces)
    plotcmd = ''
    sg = OT_dict[0]
    sName = sourceName(science_root, namespaces, project_dict['SB_name'])
    mbool = mosaicBool(namespaces, science_root, sName)
    mosaic = ismosaic(mbool, scifld[0], scifld[scifld.rfind(' ')-1:])
    if mbool == 'true':
        pc = getPhasecenter(science_root, namespaces)
    else: 
        pc = 'N/A'

    # get stuff from readme
    readme_dict = fill_README.getInfo(dictionaries[0], OT_dict)

    # fill dictionary
    parameters = {'project_number': project_dict['project_number'],'SB_name': project_dict['SB_name'],'PI_name': readme_dict['PI_name'],'title': readme_dict['title'],'nms':nms, 'specinfo':specinfo,'mosaic': mosaic[0], 'pointings': mosaic[1], 'scifield0': scifld[0], 'scifield1': scifld[len(scifld)-1], 'cellsize': cell[0], 'imsize': cell[1], 'rframe':rframe,  'vwidth':vwidth[0], 'rwidth': vwidth[1], 'rwidthunit': vwidth[2], 'spw_dict': spwinfo, 'plotcmd': plotcmd, 'rms': readme_dict['rms'], 'rms_unit': readme_dict['rms_unit'], 'rfreq':str(float(rfreqHz)*1e-9), 'phasecenter': pc}
    param = openFile()
    info = fillInfo(parameters) #! re-work this one too
    writeText(param, info)
    print 'The file imaging_parameters.txt is now in %s' % os.getcwd()

    # remove temp files
    fill_README.cleanup(OT_dict[0]['tempdir'])   

#if __name__ == "__main__":
#    main()

