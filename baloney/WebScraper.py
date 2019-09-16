# Figure out errors: course code not found in catalog. Either not a valid course or not taught this semester
# also deal with variations of user input (spaces between course prefix and number cause issue.
# also issue with labs for classes like physics with json format

import requests


# have to have a loop through the list of professors for a particular class section. Look at mac2312 for an example
# mongodb does not accept set data struct. Use a list and interate through to check for uniqueness
# check out what the deal is with the enc classes. why did the same course get split into multiple? something to do
# with some employee benefits bullshit.
# what to do if a professor hasn't been assigned to a course yet?
def scraper(userinput):
    UFurl = 'https://one.ufl.edu/apix/soc/schedule/?category=CWSP&term=2198&course-code='
    profs = {}
    courses = userinput.split(', ')

    for course in courses:
        response = requests.get(UFurl + course)
        response = response.json()
        for sections in response[0]['COURSES']:
            for section in sections['sections']:
                if len(section['instructors']) != 0:
                    if section['instructors'][0]['name'] not in profs:
                        profs[section['instructors'][0]['name']] = set()
                    if course not in profs[section['instructors'][0]['name']]:
                        profs[section['instructors'][0]['name']].add(course)

    return sortProfs(profs)


def geneds(coursecat):
    UFurl = 'https://one.ufl.edu/apix/soc/schedule/?category=CWSP&term=2198&ge-' + coursecat + '=true'
    response = requests.get(UFurl)
    response = response.json()
    profs = {}

    for sections in response[0]['COURSES']:
        course = sections['code'] + ' - ' + sections['name']
        for section in sections['sections']:
            if len(section['instructors']) != 0:
                if section['instructors'][0]['name'] not in profs:
                    profs[section['instructors'][0]['name']] = set()
                if course not in profs[section['instructors'][0]['name']]:
                    profs[section['instructors'][0]['name']].add(course)

    return sortProfs(profs)


def sortProfs(profs):
    RMPurl1 = 'https://solr-aws-elb-production.ratemyprofessors.com//solr/rmp/select/?solrformat=true&rows=20&wt=json&callback=noCB&q='
    RMPurl2 = '+AND+schoolid_s:1100&defType=edismax&qf=teacherfirstname_t^2000+teacherlastname_t^2000+teacherfullname_t^2000+autosuggest&bf=pow(total_number_of_ratings_i,2.1)&sort=total_number_of_ratings_i+desc&siteName=rmp&rows=20&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+total_number_of_ratings_i+averageratingscore_rf+schoolid_s&fq='
    ordProfs = []
    output = {}

    for prof in profs:
        response = requests.get(RMPurl1 + prof.replace(' ', '+') + RMPurl2)
        response = response.json()
        if len(response['response']['docs']) != 0 and response['response']['docs'][0]['total_number_of_ratings_i'] != 0:
            if len(ordProfs) == 0:
                ordProfs.append((response['response']['docs'][0]['averageratingscore_rf'],
                                 response['response']['docs'][0]['total_number_of_ratings_i'], prof))
            else:
                for x in range(0, len(ordProfs)):
                    if response['response']['docs'][0]['averageratingscore_rf'] > ordProfs[x][0]:
                        ordProfs.insert(x, (response['response']['docs'][0]['averageratingscore_rf'],
                                            response['response']['docs'][0]['total_number_of_ratings_i'], prof))
                        break
                else:
                    ordProfs.append((response['response']['docs'][0]['averageratingscore_rf'],
                                     response['response']['docs'][0]['total_number_of_ratings_i'], prof))
        else:
            ordProfs.append((0, 0, prof))

    for x in range(0, len(ordProfs)):
        if ordProfs[x][0] != 0:
            output[ordProfs[x][2]] = ['Average Rating: ' + str(ordProfs[x][0]), 'Number of Rates: ' +
                                      str(ordProfs[x][1]), 'Course(s): ' + ', '.join(profs[ordProfs[x][2]])]
        else:
            norateprof1 = 'The following professors have no reviews on Rate My Professor:'
            norateprof = ''
            for y in range(x, len(ordProfs)):
                if len(ordProfs) - x == 2:
                    norateprof = norateprof + ', '.join(ordProfs[y][2]) + ' and ' + ', '.join(ordProfs[y + 1][2])
                    break
                else:
                    if len(ordProfs) - x > 1 and len(ordProfs) - y == 1:
                        norateprof = norateprof + ', and ' + ordProfs[y][2]
                    else:
                        norateprof = norateprof + (ordProfs[y][2] if y == x else ', ' + ordProfs[y][2])
            output[norateprof1] = norateprof
            break
    return output
