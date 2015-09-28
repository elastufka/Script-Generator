# data_grap.py
# Author: Brian Kirk 

#This is a coded version of the directions in https://safe.nrao.edu/wiki/bin/view/ALMA/NAASC/Cycle2ImagingWorkflow
# The purpose of this is to get rid of the menial pre-imaging tasks outlined in the Cycle2 Imaging workflow

import os
import urllib2
import subprocess
import glob
import re #to do regular expression searches on the pipeline scripts
import fileinput #to edit the pipeline scripts in place 

#Under construction: accessing information from SCOPS ticket page from python
'''
username = raw_input('> Please enter your ALMA Jira username: ')
password = raw_input('> Please enter your ALMA Jira password: ')
top_level_url = 'http://jira.alma.cl/browse/SCOPS-1190'

#creating a password manager
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

#Add the site, username, and password to the manager (which'll create the authentication handler)
password_mgr.add_password(None, top_level_url, username, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)

#create "opener" (OpenerDirector instance)
opener = urllib2.build_opener(handler)

#Install the opener; now all calls to urllib2.urlopen use our opener - which has username/pass info
urllib2.install_opener(opener)

#Accessing the page with our custom opener which has authentication information built in
page_handle = urllib2.urlopen(top_level_url)

#assigning the html content to a variable 
html = page_handle.read()
'''


#Let's try it by accessing the live google docs spread sheet with all the info
'''
'''

#We can also try it by downloading the spreadsheet to my desktop so I can bypass all url-calling
'''
'''


raw_input('>This must be run from a bash shell on a cvpost node (courtesy of ASDM export). Press enter to continue')

#This is entering each information piece by hand and is proven to work:

#In the meantime I can input these values:
project_path = raw_input('> Enter the path to the directory where you want to work on this:').strip()
'''
project_number = raw_input('> Please enter your project number:').strip()
mous_code = raw_input('> Please enter your MOUS code:').strip()
SB_name = raw_input('> Please enter your SB-name:').strip()
'''
#Open up pages that let us see what pipeline version we need
#os.system('firefox -new-tab https://safe.nrao.edu/wiki/bin/view/ALMA/NAASC/Cycle2ImagingWorkflow https://wikis.alma.cl/bin/view/DSO/PipelineVersionTracker')

paragraph = []
end='Assigned'

print 'Please copy and paste the complete paragraph describing your assignment from the scops ticket'

while True:
    input_str = raw_input(">")
    if end in input_str:
        break
    else:
        paragraph.append(input_str)

def extract_id(line):
    colon = line.find(': ')
    comma= line.find(',')
    amperstand= line.find('and')
    #print colon, comma,amperstand
    #if colon, comma, and amperstand == -1:
    #    return None
    if colon != -1:
        return line[colon+2:len(line)]
    elif comma != -1: 
        return (line[0:comma], line[comma+1:len(line)])
    elif amperstand != -1:
        return (line[0:amperstand-1],line[amperstand+4:len(line)])

project_number = extract_id(paragraph[0])
mous_code = extract_id(paragraph[2]) 
SB_name = extract_id(paragraph[3]) 
SB_name = SB_name.lstrip() #get rid of extra whitespace

asdm=[]
asdmloop=[]
asdmid=extract_id(paragraph[5])

asdmloop=extract_id(asdmid)
while asdmloop != None:
    if len(asdmloop) == 2:
        asdm.append(asdmloop[0])
    else:
        asdm.append(asdmloop)
    asdmid=asdmloop[1]
    asdmloop=extract_id(asdmid)

asdm.append(asdmid)
for n in range(0,len(asdm)):
    asdm[n]=asdm[n].lstrip()
#asdm is now the complete list of asdms

#print project_id,mous_code,SB_name,asdm

#We only have to do this until Remy reports the path in a standard way
pipeline_path = raw_input('> Please enter the path to the pipeline version you want to run (include filename):').strip()
#example: /lustre/naasc/pipeline/pipeline_env_r31667_casa422_30986.sh

'''
#opening a dictionary for ASDMs
asdm = {}
asdm_num = int(raw_input('How many ASDMs do you have? '))
i = 0
while i < asdm_num:
	#dynamically create the keys
	key = i
	#assigning a value and then that value to a key based on iteration number i
	value = raw_input('Enter uid number for ASMD:').strip()
	asdm[key] = value
	i += 1 
'''

#Changing the codes into the form pipetemp requires and moving it from pipetemp to my directory
mous_code = mous_code.replace('/','_').replace(':','_')
alias = '%s.MOUS.%s.SBNAME.%s' % (project_number, mous_code, SB_name)
alias_tgz = '%s.MOUS.%s.SBNAME.%s.tgz' % (project_number, mous_code, SB_name)
os.system('cp /lustre/naasc/pipetemp/%s %s' % (alias_tgz, project_path))

#moving to my directory, unpacking the tar-ball, renaming the extracted files, and removing the tarball
os.chdir('%s' % project_path)
os.system('tar -xvzf %s' % alias_tgz)
os.system('mv %s %s-analysis' % (alias, alias))
os.system('rm %s' % alias_tgz)


#moving down to the script directory and making the pipeline script changes (fixing pipeline issues between JAO and NA ARC)
os.chdir('%s-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/script' % alias)

#checking if planets were used as calibration sources by checking in the script; if so - updating the script
#if there are multiple ASDMs there will be multiple "fix..." commands - I need to record them all and put them in the other script - the file is opened to record all changes and dump them into the other script
mods = open('casa_restore_modification.txt', 'w')
mods.truncate()
n=0

if 'fixplanets' or 'fixsyscaltimes' and '# SACM/JAO - Fixes' in open('casa_pipescript.py').read():             
	pipescript = open('casa_pipescript.py', 'r')
	for line in pipescript:
		if re.match('(.*)hifa_import(.*)', line) and n==0: #this n=0 is a dirty work-around for the hifa_importdata command showing up twice
			hifa_import = line
			#the fix taking place is adding the additional path info			
			hifa_import = hifa_import.replace('uid', '../rawdata/uid')
			mods.write(hifa_import)
			n=n+1
		#getting the other "fix" lines we'll need to add to the piperestorescript
		if re.match('    fixsyscaltimes(.*)', line):
			fixsyscaltimes = line
			mods.write(fixsyscaltimes)
		if re.match('    fixplanets(.*)', line):
			fixplanets = line
			mods.write(fixplanets)



mods.write('    h_save() # SACM/JAO - Finish weblog after fixes\n    h_init() # SACM/JAO - Restart weblog after fixes')
mods.close()

#writing the modifications to casa_piperestorescript.py

for line in fileinput.input('casa_piperestorescript.py', inplace=1):
	print line,
	#finding the place I want to input the new commands
	if line.startswith('__rethrow_casa_exceptions = True'):
		print 'from recipes.almahelpers import fixsyscaltimes # SACM/JAO - Fixes'
	if line.startswith('try:'):
		for line in open('casa_restore_modification.txt'):
			#printing the new commands into the script
			print line

#moving to the lowest directory, make the raw directory, cd into it to download the raw files
os.chdir('../')
os.system('mkdir raw')
os.chdir('raw/')




#Downloading the ASDMs and renaming them
for current_asdm in asdm: #range(0,asdm_num):
	#current_asdm = asdm[i]
	subprocess.call(['source /lustre/naasc/pipeline/pipeline_env.asdmExportLight.sh && asdmExportLight %s' % current_asdm], shell=True)
	#changing the names of the usdm to match when it was changed by asdmExport
	new_asdm = current_asdm.replace('/','_').replace(':','_')
	os.system('mv %r %r.asdm.sdm' % (new_asdm, new_asdm))


#Copying the *_flagtemplate.txt files from calibration directory to /lustre/naasc/PipelineTestData/flagfiles 
os.chdir('../calibration')
os.system('cp *_flagtemplate.txt /lustre/naasc/PipelineTestData/flagfiles')

#Add template filename, project code, MOUS, and SB name to /lustre/naasc/PipelineTestData/flagfiles/listflagfiles.txt
flag_templates = glob.glob('*_flagtemplate.txt')
flag_file = open('/lustre/naasc/PipelineTestData/flagfiles/listflagfiles.txt', 'a')
for i in flag_templates:
	string = '%s\t%s\t%s\t%s\n' % (i, project_number, mous_code, SB_name)
	flag_file.write(string)
flag_file.close()



#Moving to the script directory and running the pipeline
os.chdir('../script/')
subprocess.call(['source %s && casapy -c scriptForPI.py' % pipeline_path], shell=True, executable='/bin/bash')
#This may fail if it's a manual reduction - the CASA versions might be different



#Moving up from /script, making a backup of the pipeline data, and adding the README template 
os.chdir('..')
#os.system('cp -r calibrated calibrated_backup') #CASA exits and re-enters when scriptForPI.py is run (we suspect this because two log files are created) and kicks off the remaining commands in this script before the pipeline is finished; it doesn't bother anything else except the backup
os.system('cp /users/thunter/AIV/science/qa2/README.header.cycle2.txt README.header.txt')


#Untar the weblog reports from the /qa directory
os.chdir('qa/')
os.system('tar -xvzf %s.weblog.tar.gz' % mous_code)


#Moving into /calibrated and downloading the latest version of the imaging script template
os.chdir('../calibrated/')
response = urllib2.urlopen('https://raw.githubusercontent.com/aakepley/ALMAImagingScript/master/scriptForImaging_template.py')
html = response.read()
template = open('scriptForImaging.py', 'w').write(html)
#template.close() #this throws an error for some reason?



 
