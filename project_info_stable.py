#######################################
# project_info.py
# Erica Lastufka 08/20/2015 

#Description: Get the information about a project and store it in a dictionary
#######################################

#######################################
# Usage:
#	import project_info
#       project_info = project_info.main()

#   The user will have to enter: 
#       Project type (Imaging/Manual)
#       lustre username or directory to create Reduce_XXXX directory in (ex. elastufk or /lustre/naasc/elastufk/Imaging)
#       Paragraph form the SCOPS ticket describing project 
#	ex:
#	 Project: 2013.1.00099.S
#	 GOUS: uid://A001/X122/X45
#	 MOUS: uid://A001/X122/X46
#	 SBName: NGC253_a_06_TE
#	 SBuid: uid://A001/X122/X33
#	 ASDMs: uid://A002/X98124f/X478d
#
# 	pipeline version to source (ex. /lustre/naasc/pipeline/pipeline_env_r31667_casa422_30986.sh)

######################################

#########################################
# functions: 

#	extract_id(line)
#	    Parses the paragraph to get the relevant parameters

#	asdmLoop(paragraph)
#	    Gets the complete list of ASDMs

#	fixCodes(mous_code, project_number, SB_name, project_path)
#	    re-formats the MOUS and ASDM codes

#	main()
#	    Asks the user for imput to construct the dictionary
#########################################

def extract_id(line):
    colon = line.find(': ')
    comma= line.find(',')
    amperstand= line.find('and')
    if colon != -1:
        return line[colon+2:len(line)]
    elif comma != -1: 
        return (line[0:comma], line[comma+1:len(line)])
    elif amperstand != -1:
        return (line[0:amperstand-1],line[amperstand+4:len(line)])

def asdmLoop(paragraph):
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
    #print asdm
    return asdm #asdm is now the complete list of asdms

def fixCodes(mous_code, project_number, SB_name, project_path):
    mous_code = mous_code.replace('/','_').replace(':','_')
    alias = '%s.MOUS.%s.SBNAME.%s' % (project_number, mous_code, SB_name)
    project_base = '%s/%s-analysis/sg_ouss_id/group_ouss_id/member_ouss_id/' % (project_path, alias)
#    alias_tgz = '%s.MOUS.%s.SBNAME.%s.tgz' % (project_number, mous_code, SB_name)
    return mous_code, alias, project_base

def main():
    proj_type = raw_input('> Is this an imaging assignment or manual reduction? (Imaging/Manual):').strip()
    while (proj_type != 'Imaging' and proj_type != 'Manual'):
        proj_type = raw_input('> Please enter either Imaging or Manual: ').strip()
    lustre = raw_input('> Should I automatically generate directories Reduce_XXXXX in your lustre area? If so, please enter your username. ').strip()
    if not lustre:
        project_path = raw_input('> Enter the path to the directory where you want to work on this:').strip()
    paragraph = []
    print 'Please copy and paste the complete paragraph describing your assignment from the scops or nadr ticket'
    for n in range(0,6):
        input_str = raw_input(">")
        paragraph.append(input_str)
    if proj_type == 'Imaging':
        pipeline_path = raw_input('> Please enter the path to the pipeline version you want to run (include filename):').strip() #We only have to do this until Remy reports the path in a standard way
    else:
        pipeline_path = 'N/A'
  
    # get information about a project and store it in a dictionary
    project_number = extract_id(paragraph[0])
    mous_code = extract_id(paragraph[2]) 
    SB_name = extract_id(paragraph[3]) 
    SB_name = SB_name.lstrip() #get rid of extra whitespace
    asdm = asdmLoop(paragraph)

    if lustre:
        if proj_type == 'Imaging':
            project_path = '/lustre/naasc/' + lustre + '/Reduce_' + project_number[7:12]
        if proj_type == 'Manual':
            project_path = '/lustre/naasc/' + lustre + '/Reduce_' + str(mous_code[mous_code.rfind('/')+1:])  
    
    codes = fixCodes(mous_code, project_number, SB_name, project_path)
    
    project_info_dict={'project_type': proj_type,'project_path': project_path, 'project_number': project_number, 'mous_code': codes[0], 'SB_name': SB_name, 'number_asdms': len(asdm), 'asdm': asdm, 'alias': codes[1], 'project_base': codes[2], 'pipeline_path' : pipeline_path}
    #print project_info_dict
    return project_info_dict

if __name__ == "__main__":
    main()


