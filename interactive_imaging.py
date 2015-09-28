# to do: run plotms before flagging stuff
# write the whole script as well as the segments

import script_generator as sg
import project_info as pi
import subprocess
import mypre_imaging_working as mp
import os
import glob
import IPython
#import comments as com
import sys

def run_segment(script, project_dict, filename=False, segment_title = False): # how to run correct CASA version?
    project_path = project_dict['project_path']
    os.chdir(project_path)
    if project_dict['project_type'] == 'Imaging':
        os.chdir('sg_ouss_id/group_ouss_id/member_ouss_id/calibrated/')
    else:
        os.chdir('Imaging/')

    if not filename:
        filename = 'scriptForImaging.py'
    sg.write_script(script,project_dict, filename = filename)
    casa_version = project_dict['casa_version'] #hopefully this is defined by now...
    approve = raw_input('Run segment %s of %s?' % (segment_title, filename))
    if approve == 'Y': 
        segment = subprocess.Popen([ "casa","-r","%s" % (casa_version),"-c","%s" % (filename)], shell=False,         stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
        segment.wait()
    # else sys.exit?

def fitspw(parameters, flagchannels): # what if multiple ranges flagged in the same spw?
    fitspw = ""
    for n in range(0,2):
        line_spw = flagchannels.find(':')
        tilde = flagchannels.find('~')
        comma = flagchannels.find(',')
        if tilde == flagchannels.rfind('~'):  # you're at the end
            end = flagchannels[tilde +1:].strip()
        else: 
            end = flagchannels[tilde +1: comma].strip()
        spw_index = flagchannels[line_spw -1] 
        width = parameters['spw_dict'][int(spw_index)]['nchan']
        start = flagchannels[line_spw + 1:tilde]
        if start == '0' or int(start) -1 == 0:
            fitspw = fitspw + spw_index + ':' + str(int(end) + 1) + '~' + str(int(width) -1) + ','
        else:
            fitspw = fitspw + spw_index + ':0~' + str(int(start) - 1) + ';' + str(int(end) + 1) + '~' + str(int(width) -1) + ','
        flagchannels = flagchannels[comma + 1:] 
    fitspw = fitspw[0:len(fitspw)-1]
    return fitspw

def continuum_flagging(parameters):
    
    #Selecting the Continuum Data
    contspws = []
    #width = []
    #spwall = []
    #widthall = []

    for n in range(0,len(parameters['spw_dict'])): #nspws:
        #print parameters['spw_dict'][n]['transition']
        #spwall.append(parameters['spw_dict'][n]['index'])
        if parameters['spw_dict'][n]['transition'] == 'continuum': 
            contspws.append(parameters['spw_dict'][n]['index'])
            #width.append(parameters['spw_dict'][n]['nchan'])  #get nchan too
        #widthall.append(parameters['spw_dict'][n]['nchan'])
    
    all = raw_input("You have " + str(len(contspws)) + ' continuum-dedicated spws. Do you want to include all ' + str(len(parameters['spw_dict'])) + ' spws and flag out the lines to try to acheive a better rms (Y/N)?') 
    flagchannels = ''
    
    if all == 'Y':
    # generate ploms files
        for i in range(0,len(parameters['spw_dict'])):
	    line_channels = raw_input('For SPW %i, what channel range do you want to flag (ie, 200~300)? If nothing to flag enter 0): ' %i)
	    if line_channels == '0':
	        flagchannels = flagchannels
            else:
                flagchannels= flagchannels + '%i:%s,' % (i, line_channels)
        flagchannels = flagchannels[0:len(flagchannels)-1]
    IPython.embed()
    return flagchannels

def mosaic_cont_dirty():
    clean = "clean(vis=contvis,\n      imagename='calibrated_final_cont_dirty',\n      field=field,\n      phasecenter=phasecenter,\n      mode='mfs',\n      psfmode='clark',\n      imsize = imsize,\n      cell= cell,\n      weighting = weighting,\n      robust = robust,\n      niter = 0,\n      threshold = threshold,\n      interactive = False,\n      imagermode = imagermode)\n"
    return clean

def single_cont_dirty():
    clean = "clean(vis=contvis,\n      imagename='calibrated_final_cont_dirty',\n      field=field,\n      mode='mfs',\n      psfmode='clark',\n      imsize = imsize,\n      cell= cell,\n      weighting = weighting,\n      robust = robust,\n      niter = 0,\n      threshold = threshold,\n      interactive = False,\n      imagermode = imagermode)\n"
    return clean

def iaopenclose():
    iaopen = "ia.open('calibrated_final_cont_dirty.image')\n"
    iaclose = "ia.done()\n"
    return iaopen, iaclose

def calcmask(threshold): # take threshold as 3 sigma above rms for now?
    calcmask = "ia.calcmask('calibrated_final_cont_dirty.image >" + threshold + "',name='cont_dirty')\n"
    return calcmask

def makemask():
    makemask= "makemask(mode = 'copy', inpimage = 'calibrated_final_cont_dirty.image',\n        inpmask='calibrated_final_cont_dirty.image:cont_dirty',output='contDirtyMask',overwrite=True)\n\n"

def find_threshold(project_dict,script, parameters):
    project_path = project_dict['project_path']
    os.chdir(project_path)
    if project_dict['project_type'] == 'Imaging':
        os.chdir('sg_ouss_id/group_ouss_id/member_ouss_id/calibrated/')
    else:
        os.chdir('Imaging/')

    #imsetup = sg.image_setup(script, parameters)
    imstat = "output = imstat(imagename='calibrated_final_cont_image')\nprint output['rms']\nprint output['max']"
    # take 8-10 sigma above rms? or open up viewer and get user-defined threshold? but that's basically interactive cleaning....

    if parameters['mosaic'] == 'true':
        script = script + sg.contvis() + sg.rmtables()+ mosaic_cont_dirty() + imstat 
    else:
        script = script + sg.contvis() + sg.rmtables() + single_cont_dirty() + imstat

    return script

def generate(SB_name, project_path):
    
    parameters = {'PI_name': 'Christopher Faesi',
 'SB_name': 'NGC6357__a_03_7M',
 'cellsize': '3.900000arcsec',
 'imsize': '48',
 'mosaic': 'true',
 'nms': 3,
 'phasecenter': 'J2000 261.50333333333333deg -34.513888888888886deg',
 'plotcmd': ["plotms(vis=finalvis, xaxis='velocity', yaxis='amp', spw = '0', transform=T, freqframe='LSRK',\n        restfreq='88631.601MHz', avgtime='1e8', avgantenna=T)",
  "plotms(vis=finalvis, xaxis='velocity', yaxis='amp', spw = '1', transform=T, freqframe='LSRK',\n        restfreq='89188.526MHz', avgtime='1e8', avgantenna=T)",
  "plotms(vis=finalvis, xaxis='velocity', yaxis='amp', spw = '2', transform=T, freqframe='LSRK',\n        restfreq='86754.288MHz', avgtime='1e8', avgantenna=T)",
  "plotms(vis=finalvis, xaxis='velocity', yaxis='amp', spw = '3', transform=T, freqframe='LSRK',\n        restfreq='86339.918MHz', avgtime='1e8', avgantenna=T)"],
 'project_number': '2013.1.01391.S',
 'rframe': 'LSRK',
 'rfreq': '88.6324879296',
 'rms': '50.0',
 'rms_unit': 'mJy',
 'rwidth': 35278.3203125,
 'rwidthunit': 'MHz',
 'scifield0': '5',
 'scifield1': '50',
 'sourceName': 'NGC6357_SE',
 'specinfo': [['Spectral Windows:  (5 unique spectral windows and 1 unique polarization setups)\n',
   '  SpwID  Name                           #Chans   Frame   Ch0(MHz)  ChanWid(kHz)  TotBW(kHz) CtrFreq(MHz) BBC Num  Corrs  \n',
   '  0      ALMA_RB_03#BB_1#SW-01#FULL_RES   2048   TOPO   88673.694       -30.518     62500.0  88642.4593        1  XX  YY\n',
   '  1      ALMA_RB_03#BB_2#SW-01#FULL_RES   2048   TOPO   89230.730       -30.518     62500.0  89199.4953        2  XX  YY\n',
   '  2      ALMA_RB_03#BB_3#SW-01#FULL_RES   1024   TOPO   86796.139       -61.035     62500.0  86764.9198        3  XX  YY\n',
   '  3      ALMA_RB_03#BB_3#SW-02#FULL_RES   1024   TOPO   86381.833       -61.035     62500.0  86350.6132        3  XX  YY\n',
   '  4      ALMA_RB_03#BB_4#SW-01#FULL_RES    124   TOPO   88971.718    -15625.000   1937500.0  88010.7809        4  XX  YY\n'],
  '\n',
  ['Spectral Windows:  (5 unique spectral windows and 1 unique polarization setups)\n',
   '  SpwID  Name                           #Chans   Frame   Ch0(MHz)  ChanWid(kHz)  TotBW(kHz) CtrFreq(MHz) BBC Num  Corrs  \n',
   '  0      ALMA_RB_03#BB_1#SW-01#FULL_RES   2048   TOPO   88673.921       -30.518     62500.0  88642.6862        1  XX  YY\n',
   '  1      ALMA_RB_03#BB_2#SW-01#FULL_RES   2048   TOPO   89230.958       -30.518     62500.0  89199.7228        2  XX  YY\n',
   '  2      ALMA_RB_03#BB_3#SW-01#FULL_RES   1024   TOPO   86796.362       -61.035     62500.0  86765.1423        3  XX  YY\n',
   '  3      ALMA_RB_03#BB_3#SW-02#FULL_RES   1024   TOPO   86382.055       -61.035     62500.0  86350.8356        3  XX  YY\n',
   '  4      ALMA_RB_03#BB_4#SW-01#FULL_RES    124   TOPO   88971.944    -15625.000   1937500.0  88011.0062        4  XX  YY\n'],
  '\n',
  ['Spectral Windows:  (5 unique spectral windows and 1 unique polarization setups)\n',
   '  SpwID  Name                           #Chans   Frame   Ch0(MHz)  ChanWid(kHz)  TotBW(kHz) CtrFreq(MHz) BBC Num  Corrs  \n',
   '  0      ALMA_RB_03#BB_1#SW-01#FULL_RES   2048   TOPO   88673.880       -30.518     62500.0  88642.6454        1  XX  YY\n',
   '  1      ALMA_RB_03#BB_2#SW-01#FULL_RES   2048   TOPO   89230.917       -30.518     62500.0  89199.6819        2  XX  YY\n',
   '  2      ALMA_RB_03#BB_3#SW-01#FULL_RES   1024   TOPO   86796.322       -61.035     62500.0  86765.1022        3  XX  YY\n',
   '  3      ALMA_RB_03#BB_3#SW-02#FULL_RES   1024   TOPO   86382.015       -61.035     62500.0  86350.7956        3  XX  YY\n',
   '  4      ALMA_RB_03#BB_4#SW-01#FULL_RES    124   TOPO   88971.903    -15625.000   1937500.0  88010.9657        4  XX  YY\n'],
  '\n'],
 'spw_dict': [{'index': 0,
   'nchan': '2048',
   'restfreq': '88.631601',
   'transition': 'HCN_v_0_J_1_0',
   'type': 'HCN_v_0_J_1_0'},
  {'index': 1,
   'nchan': '2048',
   'restfreq': '89.188526',
   'transition': 'HCO__v_0_1_0',
   'type': 'HCO__v_0_1_0'},
  {'index': 2,
   'nchan': '1024',
   'restfreq': '86.754288',
   'transition': 'H13CO__1_0',
   'type': 'H13CO__1_0'},
  {'index': 3,
   'nchan': '1024',
   'restfreq': '86.33991800000001',
   'transition': 'H13CN_v_0_J_1_0',
   'type': 'H13CN_v_0_J_1_0'},
  {'index': 4,
   'nchan': '124',
   'restfreq': '88.0',
   'transition': 'continuum',
   'type': 'continuum'}],
 'title': 'NGC 6357: A Laboratory for Testing Modes of Star Formation',
 'vwidth': 119.32615915054762}

    project_dict = {'SB_name': 'NGC6357__a_03_7M',
 'asdm': ['N/A'],
 'casa_version': '4.2.2',
 'mous_code': 'N/A',
 'number_asdms': 1,
 'project_number': '2013.1.01391.S',
 'project_path': '/lustre/naasc/elastufk/Imaging/testscript',
 'project_type': 'Imaging',
 'tarball': 'N/A'}


    #dictionaries = pi.most_info(SB_name, project_path)    
    #project_dict = dictionaries[0]
    #OT_dict = dictionaries[1]
    os.chdir(project_path)
    #parameters = sg.get_parameters(project_dict = project_dict, OT_dict = OT_dict) 
    script = sg.script_data_prep(parameters, project_dict)
    #scriptNormal = sg.make_continuum(scriptNormal,parameters, project_dict)
    #run_segment(script, project_dict, segment_title = "Data preparation")
    #flagchannels = continuum_flagging(parameters)
    #script = sg.make_continuum('', parameters, project_dict, flagchannels = flagchannels)
    #IPython.embed()
    #run_segment(script, project_dict, segment_title = "Make continuum ms") 
    script = sg.image_setup('',parameters)
    #scriptDA = sg.image_setup(scriptDA,parameters)
    threshold_script = find_threshold(project_dict,script,parameters)
    #run_segment(threshold_script, project_dict, filename = 'threshold_script.py', segment_title = "Find threshold for continuum clean mask")
    #IPython.embed()
    # calculate the clean mask ...
    
    #scriptNormal = sg.cont_image(scriptNormal,parameters)
    script = sg.cont_image(script,parameters, mask = True)
    
    run_segment(script, project_dict, segment_title = "Make continuum image")
    '''
    #scriptNormal = sg.contsub(scriptNormal,parameters)
    fspw = fitspw()
    script = sg.contsub(script,parameters, fspw)
    #run_segment(script, project_dict, segment_title = "Continuum subtraction")
    #scriptNormal = sg.line_image(scriptNormal,parameters)
    # find threshold for lines and make line masks
    script = sg.line_image(script,parameters)
    #run_segment(script, project_dict, segment_title = "Make line images")
    #scriptNormal = sg.pbcor_fits(scriptNormal)
    script = sg.pbcor_fits(script)
    #run_segment(script, project_dict, segment_title = "PB cor and export fits")
    sg.write_script(script,project_dict)
    
    sg.write_script(scriptDA, project_dict, filename = 'scriptForImagingDA.py')
    '''

if __name__ == "__main__":
    generate('NGC6357__a_03_7M','/lustre/naasc/elastufk/Imaging/testscript')

