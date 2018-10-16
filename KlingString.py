import re

class KlingString:

    # setupValues
    acceptableDistanceBetweenWords = 2
    abbreviationMin = 3

    # input / transformation
    needle = ''
    needleArray = []
    needleWordCount = ''

    haystack = ''
    haystackArray = []
    haystackWordCount = 0
    haystackMatches = []

    # results / output
    results = []
    occurrences = 0
    accuracy = 0
    averageDistanceBetweenWords = 0
    baseScore = 25

    maxScore = 5

    def __init__(self, needle, haystack):
        #setup
        self.needle = needle
        self.needleArray = re.sub(r'\s+', ' ', self.needle.lower()).split(' ')
        self.needleWordCount = len(self.needleArray)

        self.haystack = haystack
        self.haystackArray = re.sub(r'\s+', ' ', self.haystack.lower(), flags=re.MULTILINE).split(' ')
        self.haystackWordCount = len(self.haystackArray)

        # the max number of transformations to remain a valid candidate
        self.accuracy = self.needleWordCount * 2

    def strip_spaces_breaks(self, string):
        return re.sub('\s+', '', string)

    def calculate_leven_max(self, string):
        if len(string) <= 5:
            return 1
        return 2

    def levenschtein(self, string1, string2):
        xSize = len(string1) + 1
        ySize = len(string2) + 1


        grid = [[0 for col in range(ySize)] for row in range(xSize)]

        for x in range(xSize):
            grid[x][0] = x

        for y in range(ySize):
            grid[0][y] = y

        for x in range(1,xSize):
            for y in range(1,ySize):

                if string1[x-1] == string2[y-1]:
                    grid[x][y] = min(
                        grid[x-1][y] +1,
                        grid[x-1][y-1],
                        grid[x][y-1] + 1
                    )

                else:
                    grid[x][y] = min(
                        grid[x - 1][y] + 1,
                        grid[x - 1][y - 1] +1,
                        grid[x][y - 1] + 1
                    )

        return grid[xSize-1][ySize-1]

    #check for exact matche of the full string and set a count of exact matches found
    def basic_match_count(self):
        self.occurrences = self.haystack.count(self.needle)

        if self.occurrences == 0:
            self.occurrences = self.strip_spaces_breaks(self.haystack).count(
                self.strip_spaces_breaks(self.needle))

        if self.occurrences > 0:
            self.averageDistanceBetweenWords = 1

        return self.basic_match_count

    # indexed string match using various transformations
    # iterate over the haystack and index every occurrence
    def transformative_position_search(self):

        for i in range(len(self.haystackArray)):
            for j in range(len(self.needleArray)):

                abbreviated = 0
                transformation_distance = 0
                levenschtein_used = 0
                match = 0

                # exact match
                if self.haystackArray[i] == self.needleArray[j]:
                    match = True

                # shortened or abbreviated match
                elif self.needleArray[j] in self.haystackArray[i] != -1 or self.haystackArray[i] in self.needleArray[j]:
                    if len(self.haystackArray[i]) >= self.abbreviationMin and len(self.needleArray[j]) >= self.abbreviationMin:
                        match = 1
                        abbreviated = 1
                        transformation_distance += abs(len(self.haystackArray[i]) - len(self.needleArray[j]))

                # total transformations to check for mis-spellings and common non abbreviated diminutives
                else:
                    levenschtein_distance = self.levenschtein(self.haystackArray[i], self.needleArray[j])
                    levenschtein_max = self.calculate_leven_max(self.haystackArray[i])
                    if levenschtein_distance <= levenschtein_max and levenschtein_distance < len(self.needleArray[j]):
                        match = True
                        levenschtein_used = 1
                        transformation_distance += levenschtein_distance

                if match != 0:

                    self.haystackMatches.append({
                        'string_found': self.haystackArray[i],
                        'search': self.needleArray[j],
                        'levenschtein': levenschtein_used,
                        'abbreviated': abbreviated,
                        'transformation_distance': transformation_distance,
                        'position': i,
                        'paired': False
                    })

        # iterate over indexed possibilities to
        if len(self.haystackMatches) > 0:
            for i in range(len(self.haystackMatches)):
                result = {
                    'words_found': 0,
                    'max_distance': 0,
                    'avg_distance': 0,
                    'phrase_direction': '',
                    'transformations': 0,
                    'levenschtein': 0,
                    'abbreviated': 0,
                    'output': '',
                    'score': 0
                }

                needle_array_copy = self.needleArray[:]
                individual_string_matches = 0
                phrase_found = []
                position_order = []

                # start by finding the first word in the search phrase
                first_position = needle_array_copy.index(self.haystackMatches[i]['search'])
                if first_position == 0:
                    direction_forward = True
                    needle_array_copy[first_position] = ''
                    phrase_found.append(self.haystackMatches[i]['string_found'])
                    position_order.append(self.haystackMatches[i]['position'])
                    self.haystackMatches[i]['paired'] = True
                    individual_string_matches += 1
                    result['transformations'] += self.haystackMatches[i]['transformation_distance']
                    result['levenschtein'] += self.haystackMatches[i]['levenschtein']
                    result['abbreviated'] += self.haystackMatches[i]['abbreviated']
                    result['paired'] = True

                    # step back and forth on the haystack index looking for the next likely match
                    for x in range(1,self.needleWordCount):
                        set = False
                        index = i + x

                        #check if the next is our word
                        if index < len(self.haystackMatches) \
                                and needle_array_copy[x] == self.haystackMatches[index]['search'] \
                                and abs(self.haystackMatches[i]['position'] - self.haystackMatches[index]['position']) <= self.acceptableDistanceBetweenWords \
                                and not self.haystackMatches[index]['paired']:

                            set = index
                            needle_array_copy[x] = ''

                        else:
                            #look forward
                            if index < len(self.haystackMatches) and self.haystackMatches[index]['search'] in needle_array_copy \
                                    and not self.haystackMatches[index]['paired'] \
                                    and abs(self.haystackMatches[i]['position'] - self.haystackMatches[index]['position']) <= self.acceptableDistanceBetweenWords:

                                exists = needle_array_copy.index(self.haystackMatches[index]['search'])
                                if exists - x < self.acceptableDistanceBetweenWords:
                                    set = index
                                    needle_array_copy[exists] = ''

                            # walk backwards through the matches sicne we may have started earlier
                            else:
                                direction_forward = False

                                for index in range(i-1, 0, -1):
                                    if index < len(self.haystackMatches) and not self.haystackMatches[index]['paired']:
                                        if self.haystackMatches[index]['search'] in needle_array_copy:
                                            exists = needle_array_copy.index(self.haystackMatches[index]['search'])
                                            needle_array_copy[exists] = ''
                                            set = index

                        if set is not False:
                            if direction_forward:
                                if result['phrase_direction'] == '' or result['phrase_direction'] == 'forward':
                                    result['phrase_direction'] = 'forward'
                                else:
                                    result['phrase_direction'] = 'mixed'
                            else:
                                if result['phrase_direction'] == '' or result['phrase_direction'] == 'reverse':
                                    result['phrase_direction'] = 'reverse'
                                else:
                                    result['phrase_direction'] = 'mixed'

                            individual_string_matches += 1
                            self.haystackMatches[set]['paired'] = True
                            result['transformations'] += self.haystackMatches[set]['transformation_distance']
                            result['levenschtein'] += self.haystackMatches[set]['levenschtein']
                            result['abbreviated'] += self.haystackMatches[set]['abbreviated']

                            if(direction_forward):
                                phrase_found.append(self.haystackMatches[set]['string_found'])
                                position_order.append(self.haystackMatches[set]['position'])
                            else:
                                phrase_found.insert(0, self.haystackMatches[set]['string_found'])
                                position_order.insert(0, self.haystackMatches[set]['position'])

                    distances = []

                    if individual_string_matches > 1:
                        for j in range(len(position_order)):
                            if j+1 < len(position_order):
                                distances.append(abs(position_order[j-1] - position_order[j]))
                            elif j == 0:
                                distances.append(0)
                    else:
                        distances.append(0)


                    result['words_found'] = individual_string_matches
                    result['max_distance'] = max(distances)
                    result['avg_distance'] = sum(distances) / len(distances)
                    result['output'] = ' '.join(phrase_found)
                    result['score'] = self.baseScore - abs(result['transformations'] + result['avg_distance'])

                    result['base_probability'] = 0

                    self.results.append(result)

        #normalize the  probability that this is
        if len(self.results) > 0:
            totalScore = 0.

            for i in range(len(self.results)):
                totalScore += self.results[i]['score']

            for i in range(len(self.results)):
                self.results[i]['base_probability'] = self.results[i]['score'] / totalScore

    def getResults(self):
        return self.results

    def getBest(self):
        best = {}
        for i in range(len(self.results)):
            if best == {}:
                best = self.results[i]
            else:
                if self.results[i]['base_probability'] > best['base_probability']:
                    best = self.results[i]
        return best



search = "Daniel Raymond Klingman"
blob = "hi i am Dan Raymond Klingman and I would like to test my name / string matching algorith. " \
       "If i put my name as Klingman Daniel and Daniel R Klingman it should still find all 3 instances."

a = KlingString(search,blob)
a.transformative_position_search()
print a.getBest()

for i in range(len(a.results)):
    print a.results[i]



# a.basic_match_count()
# print a.occurrences
#

