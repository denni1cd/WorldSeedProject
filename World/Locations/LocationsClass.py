class Location:
    """
    A class representing a location in the setting, each area will be defined by a terrain type and must be thematically appropriate.

    Attributes:
    - region_name (str): An original name of the region in the type of settings, the name should be unique and based off the terrain and society of the region.
    - terrain (str): Description of the region's terrain (e.g., mountainous, forested, coastal).
    - total_population (int): Total population of the region, as is realistic by the terrain for example mountains are  less populated than plains, put a median value at 20,000 individuals and adjust for terrain. 
    - size (float): size of the area in square kilometers, note, introduce irregulatiry as a non standard number. No area is exactly 100 square kilometers for example.
    - shape (str): a general and detailed description of the shape of the area, for example, irregulalry shaped around a central mountain, the region curves out slightly at one end creating a teardrop shape
    - population_percentage_by_race (dict): Percentage ofthe total population for each sentient race (e.g., {"human": 60, "elf": 30, "dwarf": 10}).
    - history (str): A brief history or background of the region.
    - fauna (list): List of animals or creatures found in the region.
    - flora (list): List of plant life found in the region.
    - climate (str): Description of the region's climate.
    - notable_features (list): Prominent landmarks or features in the region.
    - potential_resources (list): List of valuable resources present in the region.
    - settlements (int): Number of settlements or towns in the region.
    - landmarks (int): Number of significant landmarks in the region.
    - government (str): Description of the region's governing system.
    - economy (str): Description of the region's economy.
    - conflicts (list): Any ongoing or historical conflicts in the region.
    - religion (str): Description of the region's prevalent religions or belief systems.
    - culture (str): Overview of the region's cultural aspects.
    - transportation (str): Description of the transportation methods used in the region.
    - natural_disasters (list): Potential natural disasters that can occur in the region.
    - mysteries_legends (list): Any mysterious occurrences or legends associated with the region.
    - popular_fashion_by_race (dict): Fashion preferences of each race (e.g., {"human": "loose garments", "elf": "flowing robes"}), there should be at least one entry per race.
    - social_status_by_race (dict): Social status of each race in the form of a list (e.g., {"human": ["nobles", "commoners", "outcasts"]}) Note that social status values do not need to be unique to a race. There should be at least one entry per race
    """
    
    def __init__(self, region_name, terrain, total_population, size, shape, population_percentage_by_race, history, fauna, flora, climate, notable_features,
                 potential_resources, settlements, landmarks, government, economy, conflicts, religion, culture,
                 transportation, natural_disasters, mysteries_legends, popular_fashion_by_race, social_status_by_race):
        self.region_name = region_name
        self.terrain = terrain
        self.total_population = total_population
        self.size = size
        self.shape = shape
        self.population_percentage_by_race = population_percentage_by_race
        self.history = history
        self.fauna = fauna
        self.flora = flora
        self.climate = climate
        self.notable_features = notable_features
        self.potential_resources = potential_resources
        self.settlements = settlements
        self.landmarks = landmarks
        self.government = government
        self.economy = economy
        self.conflicts = conflicts
        self.religion = religion
        self.culture = culture
        self.transportation = transportation
        self.natural_disasters = natural_disasters
        self.mysteries_legends = mysteries_legends
        self.popular_fashion_by_race = popular_fashion_by_race
        self.social_status_by_race = social_status_by_race

    def display_info(self):
            print("Location Information:")
            print(f"Region Name: {self.region_name}")
            print(f"Terrain: {self.terrain}")
            print(f"Total Population: {self.total_population}")
            print(f"size: {self.size}")
            print(f"Shape: {self.shape}")
            print(f"Population Percentage By Race: {self.population_percentage_by_race}")
            print(f"History: {self.history}")
            print(f"Fauna: {self.fauna}")
            print(f"Flora: {self.flora}")
            print(f"Climate: {self.climate}")
            print(f"Notable Features: {self.notable_features}")
            print(f"Potential Resources: {self.potential_resources}")
            print(f"Settlements: {self.settlements}")
            print(f"Landmarks: {self.landmarks}")
            print(f"Government: {self.government}")
            print(f"Economy: {self.economy}")
            print(f"Conflicts: {self.conflicts}")
            print(f"Religion: {self.religion}")
            print(f"Culture: {self.culture}")
            print(f"Transportation: {self.transportation}")
            print(f"Natural Disasters: {self.natural_disasters}")
            print(f"Mysteries and Legends: {self.mysteries_legends}")
            print(f"Poplar Fashion by Race: {self.popular_fashion_by_race}")      
            print(f"Social Status by Race: {self.social_status_by_race}")        
 