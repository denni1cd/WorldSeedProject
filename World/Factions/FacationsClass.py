class Faction:
    def __init__(self, name, location, modus_operandi, leader, history, assets, motive, limitations):
        self.name = name
        self.location = location
        self.modus_operandi = modus_operandi
        self.leader = leader
        self.history = history
        self.assets = assets
        self.motive = motive
        self.limitations = limitations
    
    def display_info(self):
        print("Faction Information:")
        print(f"Name: {self.name}")
        print(f"Location: {self.location}")
        print(f"Modus Operandi: {self.modus_operandi}")
        print(f"Leader: {self.leader}")
        print(f"History: {self.history}")
        print(f"Assets: {self.assets}")
        print(f"Motive: {self.motive}")
        print(f"Limitations: {self.limitations}")

# Example usage:
faction = Faction("Shadow Syndicate", "Gloomy City", "Subterfuge and Espionage", "The Mastermind",
                  "Founded in the shadows centuries ago, known for their cunning tactics.",
                  ["Informants", "Assassins", "Blackmail Material"], "Gain absolute control",
                  "Lack of open confrontation")
faction.display_info()
