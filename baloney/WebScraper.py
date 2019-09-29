# Figure out errors: course code not found in catalog. Either not a valid course or not taught this semester
# also deal with variations of user input (spaces between course prefix and number cause issue.
# also issue with labs for classes like physics with json format

from pymongo import MongoClient
import requests


# have to have a loop through the list of professors for a particular class section. Look at mac2312 for an example
# mongodb does not accept set data struct. Use a list and interate through to check for uniqueness
# check out what the deal is with the enc classes. why did the same course get split into multiple? something to do
# with some employee benefits bullshit.
# what to do if a professor hasn't been assigned to a course yet?

client = MongoClient("mongodb+srv://davidjaworski:Jaworski1@cluster0-rhhfx.mongodb.net/test?retryWrites=true&w=majority")
db = client.rmp

dept = {'Accounting': 1703, }

# repeat professors is only an issue for when searching multiple classes and also for entire gen ed groups
def scraper(code):
    UFurl = 'https://one.ufl.edu/apix/soc/schedule/?category=CWSP&term=2198&dept=' + code + '0000'
    # UFurl = 'https://one.ufl.edu/apix/soc/schedule/?category=CWSP&term=2198&course=ENC1101'
    response = requests.get(UFurl)
    response = response.json()
    for course in response[0]['COURSES']:
        collection = db[course['code']]
        collection.delete_many({})
        profs = {}
        for section in course['sections']:
            for instructor in section['instructors']:
                #make course name an element in a list is going to require you to update data structure everywhere
                profs[instructor['name']] = [[course['name']], 0, 0]
        collection.insert_one(sortProfs(profs))

def genEdScraper():
    genEds = ['b', 'c', 'd', 'h', 'n', 'm', 'p', 's']
    for genEd in genEds:
        UFurl = 'https://one.ufl.edu/apix/soc/schedule/?category=CWSP&term=2198&ge-' + genEd + '=true'
        response = requests.get(UFurl)
        response = response.json()
        collection = db[genEd]
        collection.delete_many({})
        profs = {}
        for course in response[0]['COURSES']:
            for section in course['sections']:
                for instructor in section['instructors']:
                    # make course name an element in a list is going to require you to update data structure everywhere
                    if instructor['name'] not in profs:
                        profs[instructor['name']] = [{course['name']}, 0, 0]
                    else:
                        profs[instructor['name']][0].add(course['name'])
        for prof in profs:
            profs[prof][0] = list(profs[prof][0])
        collection.insert_one(sortProfs(profs))

def sortProfs(profs):
    RMPurl1 = 'https://solr-aws-elb-production.ratemyprofessors.com//solr/rmp/select/?solrformat=true&rows=20&wt=json&callback=noCB&q='
    RMPurl2 = '+AND+schoolid_s:1100&defType=edismax&qf=teacherfirstname_t^2000+teacherlastname_t^2000+teacherfullname_t^2000+autosuggest&bf=pow(total_number_of_ratings_i,2.1)&sort=total_number_of_ratings_i+desc&siteName=rmp&rows=20&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+total_number_of_ratings_i+averageratingscore_rf+schoolid_s&fq='
    ordered_profs = {}
    for prof in profs:
        response = requests.get(RMPurl1 + prof.replace(' ', '+') + RMPurl2)
        response = response.json()
        if len(response['response']['docs']) != 0 and response['response']['docs'][0]['total_number_of_ratings_i'] != 0:
            profs[prof][1] = response['response']['docs'][0]['averageratingscore_rf']
            profs[prof][2] = response['response']['docs'][0]['total_number_of_ratings_i']
    while (profs):
        high = -1
        name = ''
        for key in profs:
            if profs[key][1] > high:
                high = profs[key][1]
                name = key
        ordered_profs[name] = [profs[name][0], profs[name][1], profs[name][2]]
        del profs[name]
    return ordered_profs

# attempt to remove the course procedding the section in the array in the if
def search(userinput):
    collec = db[userinput]
    guarantee = {}
    promising = {}
    mediocre = {}
    avoid = {}
    new = {}
    sortedProfs =[]
    for course in collec.find():
        for section in course:
            if section != '_id':
                if course[section][1] >= 4.0 and course[section][2] >= 10:
                    guarantee[section] = course[section]
                elif course[section][1] >= 4.0:
                    promising[section] = course[section]
                elif course[section][1] >= 3.0:
                    mediocre[section] = course[section]
                elif course[section][1] == 0:
                    new[section] = course[section]
                else:
                    avoid[section] = course[section]
    for bucket in [{'Guaranteed Winners': guarantee}, {'Promising Newcomer': promising}, {'Middle of the Barrel': mediocre}, {'Please Avoid': avoid}, {'New Guys': new}]:
        for title in bucket:
            if bucket[title]:
                sortedProfs.append({title: bucket[title]})
    return(sortedProfs)
