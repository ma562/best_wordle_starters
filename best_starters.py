'''
Written by Joseph Ma
6/10/22
'''
import pandas as pd
import math

GRAY = "\033[2;48;5;243m\033[38;5;255m"
YELLOW = "\033[2;48;5;3m\033[38;5;248m"
GREEN = "\033[2;48;5;10m\033[38;5;248m"
RESET = "\033[2;48;5;10m\033[0m"

#game host function takes in an answer and guess, returns 
#output as feedback 
def game_host(answer, guess):
  hints = ""
  letters = list(guess) 

  #create a dictionary to keep track of how many times a letter has been marked green/yellow
  count_green = dict.fromkeys(letters, 0)
  count_yellow = dict.fromkeys(letters, 0)

  #first determine how many greens are there 
  #because number of greens determine number of yellows allowed
  for i in range(len(guess)):
    if(guess[i] == answer[i]):
      count_green[guess[i]] += 1
  
  for i in range(len(guess)):
    if((guess[i] != answer[i]) and (guess[i] in answer) and (answer.count(guess[i]) > (count_green[guess[i]] + count_yellow[guess[i]]))):
      #the letter is not in that spot
      #the letter is elsewher in the word
      #the number of occurences of that letter in the word is more than that of the currently recorded green + yellow
      count_yellow[guess[i]] += 1

  for i in range(len(guess)):
    if(guess[i] not in answer):
      hints += "W"      #GRAY
    elif(guess[i] == answer[i]):
      hints += "G"      #GREEN
    elif((guess[i] != answer[i]) and (guess[i] in answer) and (count_yellow[guess[i]] != 0)):
      #last condition is to ensure we don't overmark yellow letters
      hints += "Y"      #YELLOW
      count_yellow[guess[i]] -= 1
    else:
      hints += "W"
    
  return hints


def all_words(i):
  df = pd.read_csv("allowed_words.txt")
  #extract the words of the desired length
  df_filtered = df[df["Word"].str.len() == i]

  #create a list of list of seperated letters
  data = []
  for x in range(len(df_filtered)):
    word = df_filtered.values[x][0]
    word_list = list(word)
    word_list.insert(0, word)
    
    data.append(word_list)

  #create a data frame with column consisting of letters in each word
  len_word = i   #number of letters
  column_vals = ["Word"]
  for x in range(len_word):
    column_vals.append("letter_" + str(x + 1))

  letters = pd.DataFrame(data, columns=column_vals)
  return letters


answers = pd.read_csv("answers.txt")
possible_words = all_words(5)

#get list takes in the feedback colors, the guess, df of words and returns the conditionals
def get_conditions(feedback, guess, df):
  #CONDITION EVALUATION
  yellow_letter = []
  green_letter = []
  grey_letter = []

  #Green CONDITIONS
  condition_created = False
  for i in range(len(feedback)):
    if(feedback[i] == "G"):
      green_letter.append(guess[i])
      if(condition_created == False):
        conditions_green = df["letter_" + str(i + 1)] == guess[i]             #checks if that letter is in that spot
        condition_created = True
      else:
        conditions_green = conditions_green & (df["letter_" + str(i + 1)] == guess[i])    #IMPORTANT: need brackets because & takes precdence
  if(condition_created == False):
    conditions_green = df["letter_1"] == df["letter_1"]     #create arbritrary True statements since we are ANDing them at the end anyways

  #Yellow CONDITIONS
  condition_created = False
  for i in range(len(feedback)):
    if(feedback[i] == "Y"):
      yellow_letter.append(guess[i])    

      if(condition_created == False):
        conditions_yellow = df["Word"].str.contains(guess[i]) & (df["letter_" + str(i + 1)] != guess[i])      #checks if that letter is included in the word AND is not in that position
        condition_created = True
      else:
        conditions_yellow = conditions_yellow & (df["Word"].str.contains(guess[i]) & (df["letter_" + str(i + 1)] != guess[i]))
  if(condition_created == False):
    conditions_yellow = df["letter_1"] == df["letter_1"]     #create arbritray True statements since we are ANDing them at the end anyways

  #Grey CONDITIONS
  condition_created = False
  for i in range(len(feedback)):
    if(feedback[i] == "W"):
      grey_letter.append(guess[i])
      if(guess[i] not in yellow_letter and guess[i] not in green_letter):
        #ONLY apply the grey condition-(letter does not appear in the word) if that letter has not been marked yellow or green
        if(condition_created == False):
          conditions_grey = ~df["Word"].str.contains(guess[i])
          condition_created = True
        else:
          conditions_grey = conditions_grey & (~df["Word"].str.contains(guess[i]))      #checks if that letter is not included in the word
      else:
        #IF that letter has been marked yellow or green somewhere- we can only deduce that letter is NOT in that spot
        #example: PILLS- if first L is yellow and second L is grey, we can only deduce second L is not in the spot of the fourth letter
        if(condition_created == False):
          conditions_grey = df["letter_" + str(i + 1)] != guess[i]
          condition_created = True
        else:
          conditions_grey = conditions_grey & (df["letter_" + str(i + 1)] != guess[i])

  if(condition_created == False):
    conditions_grey = df["letter_1"] == df["letter_1"]     #create arbritray True statements since we are ANDing them at the end anyways
        
  #CONDITION COUNT GREEN + YELLOW
  condition_created = False
  #check word count according to yellow letter list- for example in PILLS- if the first L is yellow and second is not, we know there must be at least 1 L in the word + number of green L's
  green_yellow_letters = green_letter + yellow_letter

  unique_gy_letters = list(set(green_yellow_letters))
  for letter in unique_gy_letters:
    count = yellow_letter.count(letter) + green_letter.count(letter)    #see how many times that letter was colored yellow and green
    if(letter not in grey_letter):
      #the letter has to appear AT LEAST the number of times it has been green + yellow
      if(condition_created == False):
        conditions_repeat = df["Word"].str.count(letter) >= count
        condition_created = True
      else:
        conditions_repeat = conditions_repeat & (df["Word"].str.count(letter) >= count)
    else:
      #the letter has to appear EXACTLY the number of times it has been green + yellow
      if(condition_created == False):
        conditions_repeat = df["Word"].str.count(letter) == count
        condition_created = True
      else:
        conditions_repeat = conditions_repeat & (df["Word"].str.count(letter) == count)

  if(condition_created == False):
    conditions_repeat = df["letter_1"] == df["letter_1"]     #create arbritray True statements since we are ANDing them at the end anyways

  return (conditions_green & conditions_grey & conditions_yellow & conditions_repeat)

average_data = all_words(5)
for i in range(5):
  del average_data["letter_" + str(i + 1)]

data = [0.0] * len(average_data)
column_vals = ["Avg bits of info"]
averages = pd.DataFrame(data, columns = column_vals)
average_data = pd.concat([average_data, averages], axis = 1)

column_vals = ["Avg"]
averages = pd.DataFrame(data, columns = column_vals)
average_data = pd.concat([average_data, averages], axis=1)


data = [0] * len(average_data)
column_vals = ["Max"]
averages = pd.DataFrame(data, columns = column_vals)
average_data = pd.concat([average_data, averages], axis=1)

column_vals = ["Min"]
averages = pd.DataFrame(data, columns = column_vals)
average_data = pd.concat([average_data, averages], axis=1)

data = [""] * len(average_data)
column_vals = ["Most optimal for"]
averages = pd.DataFrame(data, columns = column_vals)
average_data = pd.concat([average_data, averages], axis=1)
#len(possible_words)
for i in range(len(possible_words)):
  #iterate through the possible answers
  total_num_choices = 0
  total_bits = 0
  min_val = 100000
  max_val = 0
  for j in range(len(answers)):
    #iterate through the answers
    hints = game_host(answers.values[j][0], possible_words.values[i][0])    #retrieve hints from game host for guessing that word
    data_array = possible_words[get_conditions(hints, possible_words.values[i][0], possible_words)]
    num_choices = len(data_array)
    total_bits += math.log(num_choices / len(possible_words))
    total_num_choices += num_choices      #add to total number of possible choices
    if(num_choices < min_val):
        min_val = num_choices
        average_data.at[i, "Min"] = num_choices
        if(num_choices != 0):
          average_data.at[i, "Most optimal for"] = data_array.values[0][0]
    if(num_choices > max_val):
        max_val = num_choices
        average_data.at[i, "Max"] = num_choices
        
  average = total_num_choices / len(answers)    #find the average number of choices that guessing that certain word leads to
  average_data.at[i,"Avg"] = average
  average_bits = total_bits / (len(answers) * math.log(0.5))
  average_data.at[i, "Avg bits of info"] = average_bits

average_data.to_pickle("FINAL_data.pkl")
