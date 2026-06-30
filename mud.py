"""
Simple Multi-User Dungeon (MUD) Game
A text-based adventure with rooms, items, NPCs, and combat.
"""

import random


# ──────────────────────────────
#  DATA LAYER
# ──────────────────────────────

class Room:
    """A node in the dungeon graph."""

    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.exits = {}       # direction -> Room
        self.items = []       # list of Item objects
        self.npcs = []        # list of NPC objects


class Item:
    def __init__(self, name, description=""):
        self.name = name.lower()
        self.description = description

    def take(self):
        print(f">>> You picked up the {self.name}.")


class NPC:
    """A non-player character with basic AI."""

    def __init__(self, name, dialogue="", hostile=False):
        self.name = name.title()
        self.dialogue = dialogue
        self.hostile = hostile
        self.alive = not hostile          # NPCs start alive unless hostile


class Player:
    """The player's state."""

    def __init__(self):
        self.hp = 100
        self.max_hp = 100
        self.gold = 0
        self.inventory = []
        self.pos = None                # current Room reference


# ──────────────────────────────
#  WORLD BUILDING
# ──────────────────────────────

def build_world():
    """Construct the dungeon map and return all rooms."""

    r1 = Room("Dark Forest", "A dense forest. Trees block most of the light.")
    r2 = Room("Riverside Campfire", "You see a campfire crackling by a river.")
    r3 = Room("Dungeon Entrance", "The mouth of an ancient dungeon ahead.")
    r4 = Room("Dark Tunnel", "A long, dark tunnel stretches forward.")
    r5 = Room("Treasure Chamber", "Gold and jewels glitter everywhere!")

    # Connect rooms
    r1.exits["east"] = r2
    r1.exits["west"] = None           # edge of world
    r2.exits["north"] = r3
    r2.exits["south"] = None          # riverbank edge
    r3.exits["north"] = r4
    r4.exits["east"] = r5
    r5.exits["west"] = r4

    # Items & NPCs
    sword = Item("rusty sword", "A short, rusty blade.")
    shield = Item("wooden shield", "Carved from an old oak tree.")
    potion = Item("health potion", "A glowing red liquid in a glass vial.")
    key = Item("iron key", "Cold to the touch. Looks like it fits many locks.")

    r1.items.append(sword)
    r2.items.append(shield)
    r3.items.append(potion)
    r4.items.append(key)

    # NPC
    old_man = NPC("Old Man Treekeeper",
                   "He speaks in riddles about the treasure hidden deep within.",
                   hostile=False)
    goblin = NPC("Goblin Guard",
                 "I won't let you pass without a fight!",
                 hostile=True)

    r1.npcs.append(old_man)
    r3.npcs.append(goblin)

    return [r1, r2, r3, r4, r5]


# ──────────────────────────────
#  GAME ENGINE
# ──────────────────────────────

class Game:
    def __init__(self):
        self.rooms = build_world()
        self.player = Player()
        self.player.pos = self.rooms[0]
        self.running = True

    # ---------- output helpers ----------

    def print(self, text=""):
        if text:
            print(text)

    def clear(self):
        print("\n" + "=" * 50)

    # ---------- core commands ----------

    def look(self):
        room = self.player.pos
        self.clear()
        print(f">>> {room.name}")
        print(room.description)
        if room.items:
            for it in room.items:
                print(f"  - {it.name}: {it.description}")
        if room.npcs:
            for npc in room.npcs:
                alive_tag = " (alive)" if npc.alive else ""
                print(f"  - {npc.name}{alive_tag}")

    def go(self, direction):
        room = self.player.pos
        next_room = room.exits.get(direction)
        if not next_room:
            self.print(">>> You can't go that way.")
            return
        self.player.pos = next_room
        # hostile NPC aggression check — fight all alive hostile NPCs in the new room
        for npc in list(self.player.pos.npcs):
            if npc.hostile and npc.alive:
                self.combat(npc)

    def take(self, item_name):
        room = self.player.pos
        found = False
        for it in list(room.items):
            if it.name == item_name.lower():
                self.player.inventory.append(it)
                room.items.remove(it)
                it.take()
                found = True
        if not found:
            self.print(">>> You don't see that here.")

    def drop(self, item_name):
        for it in list(self.player.inventory):
            if it.name == item_name.lower():
                room = self.player.pos
                room.items.append(it)
                self.player.inventory.remove(it)
                self.print(f">>> You dropped the {item_name}.")
                return
        self.print(">>> That's not in your inventory.")

    def talk(self, npc_name):
        for npc in list(self.player.pos.npcs):
            if npc.name.lower() == npc_name.lower():
                if not npc.alive:
                    self.print(f">>> {npc.name} is gone...")
                    return
                self.print(f"'{npc.dialogue}' says {npc.name}.")
                return
        self.print(">>> You don't see anyone to talk to.")

    def attack(self):
        room = self.player.pos
        for npc in list(room.npcs):
            if npc.hostile and npc.alive:
                damage = 10
                self.player.hp -= damage
                self.print(f">>> {npc.name} attacks you! ({damage} dmg)")
                self.combat(npc)
                return

    def use(self, item_name):
        for it in list(self.player.inventory):
            if it.name == item_name.lower():
                if "potion" in item_name.lower() and self.player.hp < 100:
                    heal = 30
                    self.player.hp = min(100, self.player.hp + heal)
                    self.print(f">>> You drink the potion. Recovered {heal} HP!")
                else:
                    self.print(">>> That's not a useful item right now.")
                return
        self.print(">>> You don't have that.")

    def inventory(self):
        if not self.player.inventory:
            self.print(">>> Your pockets are empty.")
            return
        for it in self.player.inventory:
            print(f"  - {it.name}: {it.description}")

    def stats(self):
        self.clear()
        print("╔═══════ STATUS ═══════╗")
        print(f"╠───────────────────────╣")
        print(f"║  HP: {self.player.hp}/{self.player.max_hp}   ║")
        print(f"║  Gold: {self.player.gold}                  ║")
        print(f"║  Location: {self.player.pos.name}          ║")
        print(f"╚═══════════════════════╝")

    # ---------- combat (FIXED) ----------

    def check_remaining_enemies(self):
        """After a fight, re-trigger combat for any hostile NPCs still alive."""
        for npc in list(self.player.pos.npcs):
            if npc.hostile and npc.alive:
                self.combat(npc)

    def combat(self, npc):
        self.print(">>> A wild encounter! Prepare for battle!")
        while npc.alive and self.player.hp > 0:
            turn = input(">>> (a)ttack / (r)un? ").strip().lower()
            if turn == "a":
                dmg = 8 + random.randint(0, 2)
                self.player.hp -= dmg
                self.print(f">>> You hit {npc.name} for {dmg} damage!")
                npc.alive = False
            elif turn == "r":
                break
        if not npc.alive:
            if self.player.hp <= 0:
                self.game_over()
            else:
                self.check_remaining_enemies()
        else:
            # Player ran away — check if dead first, then check remaining enemies
            if self.player.hp <= 0:
                self.game_over()
            else:
                self.check_remaining_enemies()

    def game_over(self):
        self.clear()
        print("╔═══════ GAME OVER ═══════╗")
        print("╠───────────────────────╣")
        print(f"║  Final HP: {self.player.hp}                ║")
        print(f"║  Gold earned: {self.player.gold}          ║")
        print(f"╚═══════════════════════╝")
        self.running = False

    # ---------- win ----------

    def win(self):
        self.clear()
        print("╔═══════ YOU WIN! ═══════╗")
        print("╠───────────────────────╣")
        print(f"║  Gold: {self.player.gold}                  ║")
        print(f"║  Items collected: {len(self.player.inventory)}   ║")
        print(f"╚═══════════════════════╝")
        self.running = False

    # ---------- main loop ----------

    def cmd(self, raw):
        """Parse a single command string."""
        parts = raw.strip().split(None, 1)
        verb = (parts[0] or "").lower()
        rest = parts[1] if len(parts) > 1 else ""

        verbs = {
            "look":       self.look,
            "go":         self.go,
            "take":       self.take,
            "drop":       self.drop,
            "talk":       self.talk,
            "attack":     self.attack,
            "use":        self.use,
            "inventory":  self.inventory,
            "stats":      self.stats,
            "help":       self.help,
        }

        fn = verbs.get(verb)
        if fn:
            args = rest.strip() if verb in ("go", "take", "talk", "drop") else None
            if args is not None:
                fn(args)
            else:
                fn()
        else:
            # unknown verb — try directions and inventory items
            self.print(">>> Unknown command. Type 'help' for a list.")

    def help(self):
        cmds = (
            "look       - Describe what's around you",
            "go <dir>  - Move north/south/east/west",
            "take <item>- Pick up an item",
            "drop <item>- Put an item back on the ground",
            "talk <name>- Speak to an NPC",
            "attack    - Fight a hostile creature",
            "use <item> - Use an item (potion, key...)",
            "inventory - List your items",
            "stats      - Show HP and gold",
            "help       - This message",
        )
        self.clear()
        print("╔═══════ COMMANDS ═══════╗")
        for c in cmds:
            print(f"║  {c}               ║")
        print("╚═══════════════════════╝")

    def check_all_hostile_defeated(self):
        """After combat ends, verify every hostile NPC is dead. Win if so."""
        all_dead = True
        for npc in self.player.pos.npcs:
            if npc.hostile and npc.alive:
                all_dead = False
                break
        if all_dead:
            self.win()

    def rnd(self, n):
        return random.randint(0, n - 1)


# ──────────────────────────────
#  MAIN — welcome banner & loop
# ──────────────────────────────

def main():
    game = Game()
    game.clear()
    print("╔═══════ WELCOME ═══════╗")
    print("║   TEXT MUD ADVENTURE  ║")
    print("║                       ║")
    print("║  Type 'help' to start.║")
    print("╚═══════════════════════╝")

    while game.running:
        try:
            raw = input(">>> ").strip()
            if not raw:
                continue
            game.cmd(raw)
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing! Goodbye.")


if __name__ == "__main__":
    main()
