class RPGCharacter:
    def __init__(self, name, age, race, sex, height, weight, strength, constitution, dexterity,
                 intelligence, wisdom, charisma, character_class, background, bonuses, equipment):
        self.name = name
        self.age = age
        self.race = race
        self.sex = sex
        self.height = height
        self.weight = weight
        self.strength = strength
        self.constitution = constitution
        self.dexterity = dexterity
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.character_class = character_class
        self.background = background
        self.bonuses = bonuses
        self.equipment = equipment
    
    def get_total_strength(self):
        return self.strength + self.bonuses.get("strength", 0)
    
    def get_total_constitution(self):
        return self.constitution + self.bonuses.get("constitution", 0)
    
    def get_total_dexterity(self):
        return self.dexterity + self.bonuses.get("dexterity", 0)
    
    # Add more getter methods for other attributes as needed
    
    def display_info(self):
        print("Character Information:")
        print(f"Name: {self.name}")
        print(f"Age: {self.age}")
        print(f"Race: {self.race}")
        print(f"Sex: {self.sex}")
        print(f"Height: {self.height}")
        print(f"Weight: {self.weight}")
        print(f"Strength: {self.get_total_strength()}")
        print(f"Constitution: {self.get_total_constitution()}")
        print(f"Dexterity: {self.get_total_dexterity()}")
        print(f"Intelligence: {self.intelligence}")
        print(f"Wisdom: {self.wisdom}")
        print(f"Charisma: {self.charisma}")
        print(f"Character Class: {self.character_class}")
        print(f"Background: {self.background}")
        print(f"Bonuses: {self.bonuses}")
        print(f"Equipment: {self.equipment}")
    
    def equip_item(self, item):
        self.equipment.append(item)
        print(f"{self.name} has equipped {item}!")
    
    def level_up(self, skill):
        if skill == "strength":
            self.strength += 1
        elif skill == "constitution":
            self.constitution += 1
        elif skill == "dexterity":
            self.dexterity += 1
        elif skill == "intelligence":
            self.intelligence += 1
        elif skill == "wisdom":
            self.wisdom += 1
        elif skill == "charisma":
            self.charisma += 1
        else:
            print(f"Cannot determine attribute increase for skill '{skill}'.")
            return
    
# Example usage:
bonuses = {"strength": 2, "dexterity": 1}
equipment = ["Sword", "Shield", "Armor"]
character = RPGCharacter("Gandalf", 78, "Human", "Male", "6'2", 180, 12, 14, 10,
                         18, 16, 20, "Wizard", "Wanderer", bonuses, equipment)
character.display_info()
character.equip_item("Staff")
character.level_up("intelligence")
character.display_info()
