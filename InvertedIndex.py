import json  #for turning the json file into an inverted list
from collections import defaultdict #for easier creation and use of the dict data structure
import pickle #for saving to disk
import csv

def build_list(json_file):
	#Builds an inverted index of terms existing in the json file

	inverted_index = defaultdict(dict)

	with open(json_file, "r") as jf:
		the_mess = json.loads(jf.read())

	for entry in the_mess.values():
		for list_item in entry:

			#print "sub entry: ", list_item
			scene_id = list_item['sceneId']
			scene_num = list_item['sceneNum']
			play_id = list_item['playId']
			text = list_item['text']

			#we're going to send scene_id in as the doc_id
			#because it automatically includes the play_id
			doc_id = scene_id

			word_list = text.split()
			word_index = 0
			for word in word_list:
				word_index +=1
				#If we haven't yet encountered the word
				if word not in inverted_index.keys() or doc_id not in inverted_index[word].keys():
					inverted_index[word][doc_id] = [word_index]

				else:
					#If we haven't encountered the scene the word is in
					if doc_id not in inverted_index[word].keys():
						inverted_index[word][doc_id] = [word_index]

					#if we've encountered both the word and the scene before
					else:
						inverted_index[word][doc_id].append(word_index)

						#FOR DELTA ENCODING
						#pull out the previous index for the word in the scene
						# prev_index = inverted_index[word][doc_id][-1]
						# inverted_index[word][doc_id].append(word_index-prev_index)

		return inverted_index

def build_document_stats(json_file):
	#builds an index by play_id, scene, and lengthe of the scene
	doc_stats = defaultdict(dict)
	with open(json_file, "r") as jf:
		the_mess = json.loads(jf.read())

	for entry in the_mess.values():
		for list_item in entry:
			text_list = list_item["text"].split()
			scene_id = list_item['sceneId']
			play_id = list_item['playId']

			scene = scene_id.split(":")[-1]

			doc_stats[play_id][scene] = len(text_list)

	return doc_stats



def pickle_the_dict(output_file_name, index):
	with open( output_file_name, 'wb') as handle:
		pickle.dump(index, handle)

####
#Everything under this is for evaluating the text!
###

def find_scenes(term, index):
	#return a list of the scenes a term occurs in
	scenes = []
	if term in index.keys():

		for scene in index[term].keys():
			scenes.append(scene)
		return scenes

	else:
		return None

def find_scenes_with_two_words(word_1, word_2, index):
	#Given two words, find the list of scenes that contain both words

	scene_list_1 = find_scenes(word_1, index)
	scene_list_2 = find_scenes(word_2, index)
	intersection_list = []

	shorter_list = min(scene_list_1, scene_list_2)

	longer_list = max(scene_list_1, scene_list_2)

	for element in shorter_list:
		if element in longer_list:
			intersection_list.append(element)

	if intersection_list:
		return intersection_list

	else:
		return None

def union_of_words(list_of_words, index):
	#finds all scenes that contain at least one
	#of the words in list_of_words
	union_list = []
	for word in list_of_words:
		scenes = find_scenes(word, index)
		for scene in scenes:
			if scene not in union_list:
				union_list.append(scene)

	return union_list

def words_in_order(word1_indices, word2_indices):
	#given two words and a list of scenes where they co-occur,
	#return True if word_2 ever follows word_1

	for w1_index in word1_indices:
		if (w1_index+1) in word2_indices:
			return True

	return False


def find_scenes_with_phrase(the_phrase, index):
	#given the string the_phrase and the inverted_list,
	#it returns a list of scenes in which the entire phrase
	#appears
	list_of_scenes = []
	pruned_list = [] #for taking out scenes as we build

	#for scene in list_of_scenes:
	the_phrase = the_phrase.split()
	prev_word = the_phrase.pop(0)
	first_pass = True
	while the_phrase:
		
		next_word = the_phrase.pop(0)

		#easy way to cut down on number of scenes checked
		list_of_scenes = find_scenes_with_two_words(prev_word, next_word, index)
		if not first_pass:
			list_of_scenes = [scene for scene in list_of_scenes if scene in pruned_list]

		if not list_of_scenes:
			return None
		else:
			count_list = list_of_scenes
			for scene in list_of_scenes:
				prev_list = index[prev_word][scene]
				next_list = index[next_word][scene]

				if not words_in_order(prev_list, next_list):
					count_list.remove(scene)


			prev_word = next_word
			pruned_list = count_list
			first_pass = False

	return list_of_scenes



	return pruned_list


def list_of_higher_freq_scenes(term_list_1, term_list_2, index):
	#returns a list of scenes in which the words in term list 1 occur
	#more frequently than the words in list 2
	union_1 = union_of_words(term_list_1, index)
	union_2 = union_of_words(term_list_2, index)

	#to ensure that we only count the intersecting items once
	union_2 = [scene for scene in union_2 if scene not in union_1]

	list_of_scenes_where_one_has_more = []
	
	for scene in union_1:
		list_1_count = 0
		list_2_count = 0
		for term in term_list_1:
			if scene in index[term]:
				list_1_count += len(index[term][scene])
		for term in term_list_2:
			if scene in index[term]:
				list_2_count += len(index[term][scene])

		if list_1_count > list_2_count:
			list_of_scenes_where_one_has_more.append(scene)

	return list_of_scenes_where_one_has_more

def convert_list_of_scenes_to_plays(scene_list):
	play_list = []

	for scene in scene_list:
		play = scene.split(":")[0]
		if play not in play_list:
			play_list.append(play)


	return play_list

def find_count_per_scene(term_list, index):
	count_per = {}
	for term in term_list:
		for scene in index[term]:
			count_per[scene] = len(index[term][scene])

	return count_per


#BUILD AND SAVE INDEX FOR LATER
#real_index = build_list("shakespeare-scenes.json")
#saved_index = pickle_the_dict("shakespeare_index.pickle", real_index)
# doc_stats = build_document_stats("shakespeare-scenes.json")
# saved_stats = pickle_the_dict("doc_stats.pickle", doc_stats)



#UNCOMMENT THIS FOR REVTRIEVING THE INDEX AFTER IT HAS BEEN BUILT
get_index = open("shakespeare_index.pickle", "rb")
unpickled_index = pickle.load(get_index)
get_stats = open("doc_stats.pickle", "rb")
unpickled_doc_stats = pickle.load(get_stats)

print unpickled_index

#print unpickled_doc_stats

# with open("phrase2.txt", "w") as the_file:
# 	#phrase-finding example
# 	list_of_scenes = find_scenes_with_phrase("cry havoc", unpickled_index)

# 	#find a scene with a term
# 	#list_of_scenes = find_scenes("soldier", unpickled_index)

# 	#for converting a list of scenes into a list of plays
# 	#
# 	#list_of_plays = convert_list_of_scenes_to_plays(list_of_scenes)

# 	#for finding the scenes where any of the words in the list occur
# 	#
# 	#list_of_scenes = union_of_words(["verona", "rome", "italy"], unpickled_index)

# 	#for comparing two lists of words and finding which scenes have a higher frequency of
# 	#the first list than the second
# 	#
# 	#list_of_scenes = list_of_higher_freq_scenes(["thee", "thou"], ["you"], unpickled_index)

# 	list_of_scenes = sorted(list_of_scenes)
# 	#list_of_plays = sorted(list_of_plays)
# 	for scene in list_of_scenes:
# 		the_file.write(str(scene)+" \n")


#FOR DOCUMENT METADATA





def determine_avg_len(unpickled_doc_stats):
	longest_scene_len = 0
	longest_scene = ""
	avg_len = 0
	scene_count = 0
	shortest_scene_len = 5000000000000
	shortest_scene = ""

	for key1 in unpickled_doc_stats.keys():
		for key2 in unpickled_doc_stats[key1].keys():

			#UNCOMMENT FOR FINDING LONGEST AND SHORTEST DOCS
			# if unpickled_doc_stats[key1][key2] < shortest_scene_len:
			# 	shortest_scene = key1+":"+key2
			# 	shortest_scene_len = unpickled_doc_stats[key1][key2]
			# elif unpickled_doc_stats[key1][key2] > longest_scene_len:
			# 	longest_scene = key1+":"+key2
			# 	longest_scene_len = unpickled_doc_stats[key1][key2]

			scene_count += 1
			avg_len += unpickled_doc_stats[key1][key2]

	avg_len = long(avg_len)/scene_count

	return avg_len

def determine_doc_len(name_of_scene):
	return

# thee_thou_counts = find_count_per_scene(["thee", "thou"], unpickled_index)
# you_counts = find_count_per_scene(["you"], unpickled_index)

# list_of_thees = sorted(thee_thou_counts.keys())
# list_of_yous = sorted(you_counts.keys())

# with open("counts1.csv", "wb") as the_file:
# 	spamwriter = csv.writer(the_file, dialect='excel')
# 	spamwriter.writerow("Thee and thou counts")
# 	for item in list_of_thees:
# 		spamwriter.writerow([item, thee_thou_counts[item]])
# 	the_file.write("You counts")
# 	for item in list_of_yous:
# 		spamwriter.writerow([item, you_counts[item]])




def bm25(the_index, doc_stats, the_phrase):
	k1 = 1.2
	k2 = 100
	avg_doc_len = determine_avg_len(doc_stats) #avg_len
	b = .75

	word_list = the_phrase.split()
	
	list_of_scenes = union_of_words(word_list)
	#list_of_plays = convert_list_of_scenes_to_plays(list_of_scenes)

	for scene in list_of_scenes:
		bm_score = 0
		for word in word_list:
			
			fi = len(the_index[word][scene])	#frequency of i in the document
			qfi = find_term_freq(the_index)	#frequency of i in the index
			ri = 0	#number of relevent documents that contain a term
			R = 0	#number of relevent documents
			doc_len = determine_doc_len(the_index, word)
			K = determine_K (k1, b, doc_len, avg_doc_len)	#A parameter based on k1, b, doc_len, and N

			curr_score = ((ri+.5)/(R-ri+.5))/((docs_with_term - ri+.5)/(tot_docs-docs_with_term-R+ri+.5))

			curr_score = curr_score*(k1+1)*fi/(K+fi)

			curr_score = curr_score*(k2+2)*qfi/(k2+qfi)

			bm_score += math.log(curr_score, 2)

	return bm_score



def find_term_freq(the_index, term):
	working_freq = 0
	for scene in the_index[term].keys():
		working_freq += len(the_index[term][scene])

	return working_freq


def determine_K(k1, b, dl, avdl):
	return k1*((1-b)+b*(dl/avdl))

#####
#Unit Testing
#####

#test_index = build_list("tester.json")
# list_1 = [1,5,27, 31]
# list_2 = [3, 6, 28, 42]

# the_index ={"the":{"hello":[0], "daysend":[15]}, "sun":{"hello":[1], "daysend":[22]}, "will":{"hello":[2], "daysend":[56], "howdy":[89, 120]}, "come": {"daysend":[57]}}

# test_scene_list = find_scenes_with_phrase("the sun will", the_index)

# print "union_list: ", union_of_words(["the", "will"], the_index)

# another_test = find_scenes_with_phrase("will sun", the_index)

# print "comparing the and sun: ", list_of_higher_freq_scenes(["the", "will"], ["sun"], the_index)

#print "next scene test: ", another_test

#print "a scene?", test_scene_list

# s = shelve.open("inner_shelf.db", writeback=True)

# for element in test_index.keys():
# 	for scene in test_index[element]:

