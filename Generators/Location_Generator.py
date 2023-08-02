

current_dir = os.path.dirname(os.path.abspath(__file__))
locations_path = os.path.join(current_dir, 'World', 'Locations')
sys.path.append(locations_path)
from LocationsClass import Location
class_help_string = Location.__doc__

def get_response_from_query(query):
    """
    gpt-3.5-turbo can handle up to 4097 tokens. Setting the chunksize to 1000 and k to 4 maximizes
    the number of tokens to analyze.
    """
    # chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

    # Template to use for the system message prompt
    MODEL = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content":  query}
        ],
        temperature=0,
    )
    return (response['choices'][0]['message']['content'])
    

print("start queries")

def generate_response(start=0, location_list=[], used_regions=[], attempt_num =0):
    for i in range(start, 11):
        query = """Generate an instantiation of a class called Location with the following attributes:"""+class_help_string+" store the class in the variable location"+str(i)+". Note 0: Be sure to include all attributes in the correct syntax. Note 1: don't include any explaination just the instantiation in the response so it can be implemented directly from the response. Note 2:The following regions are already used, and should not be repeated (ignore if empty):" + str(",".join(used_regions) + " Note3: Give the responses a High Fantasy theme.")
        response = get_response_from_query(query)
        try:
            exec(response)
            print(response)
        except:
            print("Exeucting the response failed on: ", response)
            if attempt_num < 5:
                attempt_num+=1
                print("Attempt ", attempt_num, " commencing.")
                generate_response(i, location_list, used_regions, attempt_num)
            else:
                return location_list
        used_regions.append(locals()[f"location{i}"].region_name)
        location_list.append(locals()[f"location{i}"])
    return location_list

location_list = generate_response()
location_list[0].display_info()
print("done with loop")