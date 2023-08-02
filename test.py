import os
import sys
import inspect

current_dir = os.path.dirname(os.path.abspath(__file__))
locations_path = os.path.join(current_dir, 'World', 'Locations')
sys.path.append(locations_path)


from LocationsClass import Location

# init_parameters = inspect.signature(Location.__init__).parameters
# print(list(init_parameters.keys()))
# print(vars(Location))
class_help_string = Location.__doc__
# # print(class_help_string)
for i in range(0, 11):
    query = """Generate an instantiation of a class called Location with the following attributes:"""+class_help_string+" store the class in the variable location"+str(i)+". Note 0: Be sure to include all attributes in the correct syntax. Note 1: don't include any explaination just the instantiation in the response so it can be implemented directly from the response. Note 2:The following regions are already used, and should not be repeated (ignore if empty):" + str("candyland")
    print(query)
# query = """Generate an instantiation of a class called Location with the following attributes:"""+class_help_string+" store the class in the variable Location"+str(1)+" the following regions are already used, and should not be repeated (ignore if empty):"+str(['candyland', 'Mystic Forest'])
# print(query)

# def count_words(input_string):
#     words_list = input_string.split()
#     return len(words_list)

# # Example usage:
# # text = "This is a sample string with multiple words."
# word_count = count_words(query)
# print(f"Number of words: {word_count}")